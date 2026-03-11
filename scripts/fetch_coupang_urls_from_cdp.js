const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

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

function runNodeScript(scriptPath, args) {
  const result = spawnSync(process.execPath, [scriptPath, ...args], {
    stdio: "pipe",
    encoding: "utf-8",
  });

  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || `Failed to run ${scriptPath}`);
  }

  return result.stdout.trim();
}

async function main() {
  const urlFilePath = process.argv[2];
  const outputDir = process.argv[3];
  const cdpEndpoint = process.argv[4] || "http://127.0.0.1:9222";
  const maxPagesArg = process.argv[5] || "0";
  const maxPages = Number(maxPagesArg) || 0;

  if (!urlFilePath || !outputDir) {
    throw new Error(
      "Usage: node scripts/fetch_coupang_urls_from_cdp.js <url-file> <output-dir> [cdp-endpoint] [max-pages]"
    );
  }

  const urls = loadUrlList(urlFilePath);
  const scriptPath = path.join(__dirname, "fetch_coupang_pages_from_cdp.js");
  const results = [];

  for (const url of urls) {
    const args = [url, outputDir, cdpEndpoint];
    if (maxPages) {
      args.push(String(maxPages));
    }

    try {
      const output = runNodeScript(scriptPath, args);
      const parsed = JSON.parse(output);
      results.push({ ok: true, productId: getProductId(url), ...parsed });
      console.log(`OK ${getProductId(url)} pages=${parsed.totalPagesSaved}`);
    } catch (error) {
      results.push({ ok: false, productId: getProductId(url), url, error: String(error) });
      console.error(`FAIL ${getProductId(url)} ${error}`);
    }
  }

  console.log(JSON.stringify(results, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
