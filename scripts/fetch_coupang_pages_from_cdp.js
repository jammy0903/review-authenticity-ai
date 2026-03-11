const fs = require("fs");
const path = require("path");

const { chromium } = require("playwright");

function getProductId(url) {
  const match = url.match(/\/vp\/products\/(\d+)/);
  return match ? match[1] : "unknown";
}

function buildOutputPath(outputDir, productId, pageNumber) {
  const filename = `coupang_${productId}_cdp_page_${String(pageNumber).padStart(3, "0")}.html`;
  return path.join(outputDir, filename);
}

async function scrollReviewSectionIntoView(page) {
  await page.evaluate(() => {
    const reviewSection =
      document.querySelector("#sdpReview") ||
      document.querySelector(".product-review") ||
      document.querySelector('[data-value="review"]');
    if (reviewSection) {
      reviewSection.scrollIntoView({ behavior: "instant", block: "start" });
    }
  });
  await page.waitForTimeout(1200);
}

async function getPaginationState(page) {
  return page.evaluate(() => {
    const reviewRoot =
      document.querySelector("#sdpReview") ||
      document.querySelector(".product-review") ||
      document.body;

    const buttons = [...reviewRoot.querySelectorAll("button")];
    const pageButtons = buttons
      .map((button, index) => {
        const text = (button.innerText || button.textContent || "").trim();
        if (!/^\d+$/.test(text)) {
          return null;
        }

        const className = button.className || "";
        const isActive =
          className.includes("twc-text-[#346aff]") ||
          className.includes("twc-border-solid");

        return {
          index,
          pageNumber: Number(text),
          isActive,
        };
      })
      .filter(Boolean);

    const activeButton = pageButtons.find((button) => button.isActive);
    const currentPage = activeButton ? activeButton.pageNumber : pageButtons[0]?.pageNumber || 1;

    const arrowButtons = buttons
      .map((button, index) => ({
        index,
        text: (button.innerText || button.textContent || "").trim(),
        disabled: Boolean(button.disabled),
        className: button.className || "",
        svgCount: button.querySelectorAll("svg").length,
      }))
      .filter((button) => button.svgCount > 0 && button.text === "");

    const nextArrow = arrowButtons[arrowButtons.length - 1] || null;

    const firstReviewId =
      reviewRoot.querySelector("[data-review-id]")?.getAttribute("data-review-id") || "";

    return {
      currentPage,
      pageNumbers: pageButtons.map((button) => button.pageNumber),
      currentButtonIndex: activeButton ? activeButton.index : null,
      nextArrowIndex: nextArrow ? nextArrow.index : null,
      nextArrowDisabled: nextArrow ? nextArrow.disabled : true,
      firstReviewId,
    };
  });
}

async function clickPageButton(page, pageNumber) {
  const clicked = await page.evaluate((targetPageNumber) => {
    const reviewRoot =
      document.querySelector("#sdpReview") ||
      document.querySelector(".product-review") ||
      document.body;

    const button = [...reviewRoot.querySelectorAll("button")].find((candidate) => {
      const text = (candidate.innerText || candidate.textContent || "").trim();
      return text === String(targetPageNumber);
    });

    if (!button) {
      return false;
    }

    button.click();
    return true;
  }, pageNumber);

  return clicked;
}

async function clickNextArrow(page) {
  return page.evaluate(() => {
    const reviewRoot =
      document.querySelector("#sdpReview") ||
      document.querySelector(".product-review") ||
      document.body;

    const arrowButtons = [...reviewRoot.querySelectorAll("button")].filter((button) => {
      const text = (button.innerText || button.textContent || "").trim();
      return !text && button.querySelectorAll("svg").length > 0;
    });

    const nextArrow = arrowButtons[arrowButtons.length - 1];
    if (!nextArrow || nextArrow.disabled) {
      return false;
    }

    nextArrow.click();
    return true;
  });
}

async function waitForPageChange(page, previousState) {
  await page.waitForFunction(
    ({ previousPage, previousReviewId }) => {
      const reviewRoot =
        document.querySelector("#sdpReview") ||
        document.querySelector(".product-review") ||
        document.body;

      const buttons = [...reviewRoot.querySelectorAll("button")];
      const pageButtons = buttons
        .map((button) => {
          const text = (button.innerText || button.textContent || "").trim();
          if (!/^\d+$/.test(text)) {
            return null;
          }

          const className = button.className || "";
          const isActive =
            className.includes("twc-text-[#346aff]") ||
            className.includes("twc-border-solid");

          return isActive ? Number(text) : null;
        })
        .filter(Boolean);

      const currentPage = pageButtons[0] || 1;
      const currentReviewId =
        reviewRoot.querySelector("[data-review-id]")?.getAttribute("data-review-id") || "";

      return currentPage !== previousPage || currentReviewId !== previousReviewId;
    },
    {
      previousPage: previousState.currentPage,
      previousReviewId: previousState.firstReviewId,
    },
    { timeout: 15000 }
  );

  await page.waitForTimeout(1500);
}

async function saveCurrentPageHtml(page, outputPath) {
  const html = await page.content();
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf-8");
  return html.length;
}

async function main() {
  const targetUrl = process.argv[2];
  const outputDir = process.argv[3];
  const cdpEndpoint = process.argv[4] || "http://127.0.0.1:9222";
  const maxPagesArg = process.argv[5] || "0";
  const maxPages = Number(maxPagesArg) || 0;

  if (!targetUrl || !outputDir) {
    throw new Error(
      "Usage: node scripts/fetch_coupang_pages_from_cdp.js <target-url> <output-dir> [cdp-endpoint] [max-pages]"
    );
  }

  const browser = await chromium.connectOverCDP(cdpEndpoint);
  const contexts = browser.contexts();
  if (!contexts.length) {
    throw new Error("No browser contexts found via CDP.");
  }

  const context = contexts[0];
  const pages = contexts.flatMap((browserContext) => browserContext.pages());
  let page =
    pages.find((candidate) => candidate.url() === targetUrl) ||
    pages.find((candidate) => candidate.url().startsWith(targetUrl.split("?")[0]));

  if (!page) {
    page = await context.newPage();
    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(3000);
  }

  await page.bringToFront();
  await scrollReviewSectionIntoView(page);

  const productId = getProductId(page.url());
  const savedPages = [];
  const visitedPages = new Set();

  while (true) {
    const state = await getPaginationState(page);
    if (visitedPages.has(state.currentPage)) {
      break;
    }

    visitedPages.add(state.currentPage);
    const outputPath = buildOutputPath(outputDir, productId, state.currentPage);
    const htmlLength = await saveCurrentPageHtml(page, outputPath);
    savedPages.push({
      pageNumber: state.currentPage,
      outputPath,
      htmlLength,
      firstReviewId: state.firstReviewId,
    });

    if (maxPages && savedPages.length >= maxPages) {
      break;
    }

    const nextVisiblePage = state.pageNumbers
      .filter((pageNumber) => pageNumber > state.currentPage)
      .sort((left, right) => left - right)[0];

    if (nextVisiblePage) {
      const clicked = await clickPageButton(page, nextVisiblePage);
      if (!clicked) {
        break;
      }
      await waitForPageChange(page, state);
      await scrollReviewSectionIntoView(page);
      continue;
    }

    if (!state.nextArrowDisabled) {
      const clicked = await clickNextArrow(page);
      if (!clicked) {
        break;
      }
      await waitForPageChange(page, state);
      await scrollReviewSectionIntoView(page);
      continue;
    }

    break;
  }

  console.log(
    JSON.stringify(
      {
        targetUrl,
        pageUrl: page.url(),
        title: await page.title(),
        productId,
        savedPages,
        totalPagesSaved: savedPages.length,
      },
      null,
      2
    )
  );

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
