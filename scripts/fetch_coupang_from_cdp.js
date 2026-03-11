const fs = require("fs");
const path = require("path");

const { chromium } = require("playwright");

function getProductId(url) {
  const match = url.match(/\/vp\/products\/(\d+)/);
  return match ? match[1] : "unknown";
}

async function main() {
  const targetUrl = process.argv[2];
  const outputPath = process.argv[3];
  const cdpEndpoint = process.argv[4] || "http://127.0.0.1:9222";

  if (!targetUrl || !outputPath) {
    throw new Error(
      "Usage: node scripts/fetch_coupang_from_cdp.js <target-url> <output-path> [cdp-endpoint]"
    );
  }

  const browser = await chromium.connectOverCDP(cdpEndpoint);
  const contexts = browser.contexts();
  if (!contexts.length) {
    throw new Error("No browser contexts found via CDP.");
  }

  const pages = contexts.flatMap((context) => context.pages());
  const page =
    pages.find((candidate) => candidate.url() === targetUrl) ||
    pages.find((candidate) => candidate.url().startsWith(targetUrl.split("?")[0]));

  if (!page) {
    throw new Error(`No open page matched target URL: ${targetUrl}`);
  }

  await page.bringToFront();
  await page.waitForTimeout(1500);

  for (let attempt = 0; attempt < 12; attempt += 1) {
    await page.mouse.wheel(0, 1800);
    await page.waitForTimeout(700);
  }

  await page.waitForTimeout(1500);
  const html = await page.content();

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf-8");

  console.log(
    JSON.stringify(
      {
        targetUrl,
        pageUrl: page.url(),
        title: await page.title(),
        outputPath,
        htmlLength: html.length,
        productId: getProductId(page.url()),
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
