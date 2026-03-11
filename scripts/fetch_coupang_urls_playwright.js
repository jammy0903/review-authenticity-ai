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

function getProductId(url) {
  const match = url.match(/\/vp\/products\/(\d+)/);
  return match ? match[1] : "unknown";
}

async function savePageHtml(page, url, outputPath) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);

  for (let attempt = 0; attempt < 12; attempt += 1) {
    await page.mouse.wheel(0, 1800);
    await page.waitForTimeout(1000);
  }

  await page.waitForTimeout(2000);

  const html = await page.content();
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf-8");

  return {
    url,
    outputPath,
    title: await page.title(),
    htmlLength: html.length,
  };
}

async function main() {
  const urlFilePath = process.argv[2];
  const outputDir = process.argv[3];
  const cookiesPath = process.argv[4] || "";
  const storageStatePath = process.argv[5] || "";

  if (!urlFilePath || !outputDir) {
    throw new Error(
      "Usage: node scripts/fetch_coupang_urls_playwright.js <url-file> <output-dir> [cookies-json] [storage-state-json]"
    );
  }

  const urls = loadUrlList(urlFilePath);
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });

  const contextOptions = {
    locale: "ko-KR",
    userAgent:
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    viewport: { width: 1440, height: 2200 },
  };
  if (storageStatePath) {
    contextOptions.storageState = storageStatePath;
  }

  const context = await browser.newContext(contextOptions);
  if (cookiesPath) {
    const cookies = JSON.parse(fs.readFileSync(cookiesPath, "utf-8"));
    await context.addCookies(cookies);
  }

  const page = await context.newPage();
  const results = [];

  for (const url of urls) {
    const productId = getProductId(url);
    const outputPath = path.join(outputDir, `coupang_${productId}.html`);
    try {
      const result = await savePageHtml(page, url, outputPath);
      results.push({ ...result, cookiesPath, storageStatePath, ok: true });
      console.log(`OK ${productId} ${result.htmlLength}`);
    } catch (error) {
      results.push({
        url,
        outputPath,
        cookiesPath,
        storageStatePath,
        ok: false,
        error: String(error),
      });
      console.error(`FAIL ${productId} ${error}`);
    }
  }

  await browser.close();
  console.log(JSON.stringify(results, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
