const fs = require("fs");
const path = require("path");

const { chromium } = require("playwright");

function loadUrlList(urlFilePath) {
  return fs
    .readFileSync(urlFilePath, "utf-8")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"));
}

function getPlaceId(url) {
  const match = url.match(/place\.map\.kakao\.com\/(\d+)/);
  return match ? match[1] : "unknown";
}

function buildOutputPath(outputDir, url, pageNumber) {
  const suffix = String(pageNumber).padStart(3, "0");
  return path.join(outputDir, `kakaomap_${getPlaceId(url)}_page_${suffix}.html`);
}

function wrapHtml(title, url, html) {
  return [
    "<!doctype html>",
    "<html>",
    "<head>",
    '<meta charset="utf-8">',
    `<meta property="og:title" content="${title.replace(/"/g, "&quot;")}">`,
    `<meta name="source-url" content="${url.replace(/"/g, "&quot;")}">`,
    "</head>",
    "<body>",
    html,
    "</body>",
    "</html>",
  ].join("\n");
}

function reviewFrameScore(frame) {
  const url = frame.url() || "";
  let score = 0;
  if (url.includes("place.map.kakao.com")) score += 3;
  if (url.includes("#review")) score += 2;
  if (url.includes("/review")) score += 2;
  if (url.includes("/comment")) score += 2;
  return score;
}

async function listCandidateFrames(page) {
  const frames = page.frames();
  const scored = [];
  for (const frame of frames) {
    let bonus = 0;
    try {
      if (await frame.locator("text=/리뷰|후기/").first().isVisible({ timeout: 300 })) {
        bonus += 3;
      }
    } catch (_) {}
    try {
      const html = await frame.content();
      if (/list_review|section_review|후기|리뷰|review/i.test(html)) {
        bonus += 2;
      }
    } catch (_) {}
    scored.push({ frame, score: reviewFrameScore(frame) + bonus });
  }
  return scored.sort((a, b) => b.score - a.score).map((item) => item.frame);
}

async function clickFirstVisible(frame, selectors, timeout = 800) {
  for (const selector of selectors) {
    try {
      const locator = frame.locator(selector).first();
      if (await locator.isVisible({ timeout })) {
        await locator.click({ timeout: 3000 });
        await frame.waitForTimeout(1200);
        return true;
      }
    } catch (_) {}
  }
  return false;
}

async function scrollReviewArea(frame) {
  await frame.evaluate(() => {
    const section =
      document.querySelector(".section_review") ||
      document.querySelector(".group_review") ||
      document.querySelector(".list_review") ||
      document.body;
    section.scrollIntoView({ block: "start", behavior: "instant" });
  });
  await frame.waitForTimeout(900);
}

async function forceScrollReviewBottom(frame, rounds = 8) {
  for (let i = 0; i < rounds; i += 1) {
    await frame.evaluate(() => {
      const section =
        document.querySelector(".section_review") ||
        document.querySelector(".group_review") ||
        document.querySelector(".list_review") ||
        document.body;
      section.scrollBy?.(0, 1600);
      window.scrollBy(0, 1600);
    });
    await frame.waitForTimeout(700);
  }
}

async function openReviewSection(frame) {
  await clickFirstVisible(frame, [
    "a.link_tab[href='#review']",
    "a[role='tab'][href='#review']",
    "a:has-text('후기')",
    "button:has-text('후기')",
    "a:has-text('리뷰')",
    "button:has-text('리뷰')",
  ]);
  await scrollReviewArea(frame);
  await clickFirstVisible(frame, [
    "a.link_reviewall",
    "a:has-text('후기 154')",
    "a:has(.tit_total)",
    "a.link_review",
  ]);
  await scrollReviewArea(frame);
}

async function expandCurrentPageReviews(frame, maxMoreClicks) {
  let clicks = 0;
  while (clicks < maxMoreClicks) {
    const clicked = await clickFirstVisible(frame, [
      "span.btn_more",
      "button:has-text('더보기')",
      "a:has-text('더보기')",
    ], 300);
    if (!clicked) {
      break;
    }
    clicks += 1;
  }
  return clicks;
}

async function getReviewState(frame) {
  return frame.evaluate(() => {
    const section =
      document.querySelector(".section_review") ||
      document.querySelector(".group_review") ||
      document.body;

    const cards = [...section.querySelectorAll(".inner_review")];
    const texts = cards
      .map((card) => card.querySelector(".desc_review")?.textContent?.trim() || "")
      .filter(Boolean);

    const controls = [...section.querySelectorAll("a, button")].map((node, index) => ({
      index,
      text: (node.textContent || "").trim(),
      className: node.className || "",
      ariaCurrent: node.getAttribute("aria-current") || "",
      ariaSelected: node.getAttribute("aria-selected") || "",
      disabled: Boolean(node.disabled),
    }));

    const pageControls = controls.filter((item) => /^\d+$/.test(item.text));
    const activeControl =
      pageControls.find((item) => item.ariaCurrent === "page") ||
      pageControls.find((item) => item.ariaSelected === "true") ||
      pageControls.find((item) => /on|active|selected/.test(item.className));

    const currentPage = activeControl ? Number(activeControl.text) : 1;
    const pageNumbers = pageControls.map((item) => Number(item.text));
    const nextControl = controls.find((item) => /다음|next|다음페이지|>\s*$|›|→/i.test(item.text));

    return {
      currentPage,
      pageNumbers,
      hasPagination: pageControls.length > 0 || Boolean(nextControl),
      firstReviewText: texts[0] || "",
      reviewCount: texts.length,
      hasNextTextButton: Boolean(nextControl && !nextControl.disabled),
    };
  });
}

async function clickPageNumber(frame, targetPage) {
  return frame.evaluate((pageNumber) => {
    const section =
      document.querySelector(".section_review") ||
      document.querySelector(".group_review") ||
      document.body;
    const target = [...section.querySelectorAll("a, button")].find((node) => {
      return (node.textContent || "").trim() === String(pageNumber);
    });
    if (!target) {
      return false;
    }
    target.click();
    return true;
  }, targetPage);
}

async function clickNextPage(frame) {
  return frame.evaluate(() => {
    const section =
      document.querySelector(".section_review") ||
      document.querySelector(".group_review") ||
      document.body;
    const target = [...section.querySelectorAll("a, button")].find((node) => {
      const text = (node.textContent || "").trim();
      const className = node.className || "";
      return (
        (/다음|next|다음페이지|>\s*$|›|→/i.test(text) || /next|paging|paginate|arr/i.test(className)) &&
        !node.disabled
      );
    });
    if (!target) {
      return false;
    }
    target.click();
    return true;
  });
}

async function waitForReviewChange(frame, previousState) {
  try {
    await frame.waitForFunction(
      ({ currentPage, firstReviewText }) => {
        const section =
          document.querySelector(".section_review") ||
          document.querySelector(".group_review") ||
          document.body;
        const firstText =
          section.querySelector(".inner_review .desc_review")?.textContent?.trim() || "";
        const controls = [...section.querySelectorAll("a, button")]
          .map((node) => ({
            text: (node.textContent || "").trim(),
            ariaCurrent: node.getAttribute("aria-current") || "",
            ariaSelected: node.getAttribute("aria-selected") || "",
            className: node.className || "",
          }))
          .filter((item) => /^\d+$/.test(item.text));
        const active =
          controls.find((item) => item.ariaCurrent === "page") ||
          controls.find((item) => item.ariaSelected === "true") ||
          controls.find((item) => /on|active|selected/.test(item.className));
        const page = active ? Number(active.text) : 1;
        return page !== currentPage || firstText !== firstReviewText;
      },
      previousState,
      { timeout: 15000 }
    );
  } catch (_) {
    await frame.waitForTimeout(2000);
  }
  await frame.waitForTimeout(1200);
}

async function saveHtml(outputPath, title, url, html) {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, wrapHtml(title, url, html), "utf-8");
}

async function collectPlacePages(page, url, outputDir, maxMoreClicks, maxPages) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);

  const frames = await listCandidateFrames(page);
  const frame = frames[0] || page.mainFrame();
  await openReviewSection(frame);

  const title = await page.title();
  const savedPages = [];
  const visited = new Set();
  let pageIndex = 1;

  while (pageIndex <= maxPages) {
    await scrollReviewArea(frame);
    const moreClicks = await expandCurrentPageReviews(frame, maxMoreClicks);
    await forceScrollReviewBottom(frame, 10);
    const state = await getReviewState(frame);
    const html = await frame.content();
    const effectivePage = state.currentPage || pageIndex;
    const signature = `${effectivePage}|${state.firstReviewText}`;
    if (visited.has(signature)) {
      break;
    }
    visited.add(signature);

    const outputPath = buildOutputPath(outputDir, url, effectivePage);
    await saveHtml(outputPath, title, url, html);
    savedPages.push({
      pageNumber: effectivePage,
      outputPath,
      htmlLength: html.length,
      reviewCount: state.reviewCount,
      moreClicks,
    });

    if (!state.hasPagination) {
      break;
    }

    const nextVisiblePage = state.pageNumbers
      .filter((num) => num > effectivePage)
      .sort((a, b) => a - b)[0];

    let moved = false;
    if (nextVisiblePage) {
      moved = await clickPageNumber(frame, nextVisiblePage);
    }
    if (!moved && state.hasNextTextButton) {
      moved = await clickNextPage(frame);
    }
    if (!moved) {
      break;
    }

    try {
      await waitForReviewChange(frame, {
        currentPage: effectivePage,
        firstReviewText: state.firstReviewText,
      });
    } catch (_) {
      break;
    }
    pageIndex += 1;
  }

  return {
    url,
    placeId: getPlaceId(url),
    title,
    pageUrl: page.url(),
    savedPages,
    totalPagesSaved: savedPages.length,
  };
}

async function main() {
  const urlFilePath = process.argv[2];
  const outputDir = process.argv[3];
  const maxMoreClicks = Number(process.argv[4] || "20");
  const maxPages = Number(process.argv[5] || "20");

  if (!urlFilePath || !outputDir) {
    throw new Error(
      "Usage: node scripts/fetch_kakaomap_reviews_playwright.js <url-file> <output-dir> [max-more-clicks] [max-pages]"
    );
  }

  const urls = loadUrlList(urlFilePath);
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({
    locale: "ko-KR",
    userAgent:
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    viewport: { width: 1440, height: 2200 },
  });
  const page = await context.newPage();
  const results = [];

  for (const url of urls) {
    try {
      const result = await collectPlacePages(page, url, outputDir, maxMoreClicks, maxPages);
      results.push({ ...result, ok: true });
      console.log(`OK ${result.placeId} pages=${result.totalPagesSaved}`);
    } catch (error) {
      results.push({
        url,
        placeId: getPlaceId(url),
        ok: false,
        error: String(error),
      });
      console.error(`FAIL ${getPlaceId(url)} ${error}`);
    }
  }

  await browser.close();
  console.log(JSON.stringify(results, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
