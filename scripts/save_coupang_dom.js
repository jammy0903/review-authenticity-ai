/*
Run this in the browser DevTools console on an open Coupang product page.
It scrolls the page to trigger lazy content, then downloads the current DOM.
*/

(async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const productIdMatch = window.location.pathname.match(/\/vp\/products\/(\d+)/);
  const productId = productIdMatch ? productIdMatch[1] : "unknown";
  const filename = `coupang_${productId}.html`;

  const scrollStep = Math.max(Math.floor(window.innerHeight * 0.9), 600);
  let previousHeight = -1;

  for (let attempt = 0; attempt < 20; attempt += 1) {
    window.scrollBy({ top: scrollStep, behavior: "instant" });
    await wait(900);

    const currentHeight = document.documentElement.scrollHeight;
    if (currentHeight === previousHeight && window.innerHeight + window.scrollY >= currentHeight - 10) {
      break;
    }

    previousHeight = currentHeight;
  }

  window.scrollTo({ top: 0, behavior: "instant" });
  await wait(300);

  const html = `<!DOCTYPE html>\n${document.documentElement.outerHTML}`;
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const downloadUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(downloadUrl);

  console.log(`Saved ${filename}`);
})();
