const fs = require("fs");
const path = require("path");

const { chromium } = require("playwright");

async function main() {
  const url = process.argv[2];
  const outputPath = process.argv[3];
  const cookiesPath = process.argv[4] || "";
  const storageStatePath = process.argv[5] || "";

  if (!url || !outputPath) {
    throw new Error(
      "Usage: node scripts/fetch_coupang_playwright.js <url> <output-path> [cookies-json] [storage-state-json]"
    );
  }

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
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);

  for (let attempt = 0; attempt < 10; attempt += 1) {
    await page.mouse.wheel(0, 1800);
    await page.waitForTimeout(1200);
  }

  await page.waitForTimeout(2000);
  const html = await page.content();

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf-8");

  console.log(
    JSON.stringify(
      {
        url,
        outputPath,
        title: await page.title(),
        htmlLength: html.length,
        cookiesPath,
        storageStatePath,
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
