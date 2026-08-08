import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const port = 8765;
const baseUrl = `http://127.0.0.1:${port}`;
const screenshotPath = path.join(root, "docs", "screenshot.png");
const sampleLog = path.join(root, "docs", "fixtures", "sample.log");
const readmePath = path.join(root, "README.md");
const screenshotDataDir = path.join(root, "docs", "fixtures", ".screenshot-data");

const SCREENSHOT_START = "<!-- APP_SCREENSHOT -->";
const SCREENSHOT_END = "<!-- /APP_SCREENSHOT -->";

async function waitForServer(maxAttempts = 40) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`${baseUrl}/api/version`);
      if (res.ok) return;
    } catch {
      // Server not ready yet.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("Screenshot server did not start in time");
}

function updateReadme() {
  const readme = fs.readFileSync(readmePath, "utf8");
  const block = `${SCREENSHOT_START}\n![Logs Home screenshot](docs/screenshot.png)\n${SCREENSHOT_END}`;
  const pattern = new RegExp(`${SCREENSHOT_START}[\\s\\S]*?${SCREENSHOT_END}`);
  const updated = pattern.test(readme)
    ? readme.replace(pattern, block)
    : readme.replace(/^# Logs Home\r?\n/, `# Logs Home\n\n${block}\n`);
  fs.writeFileSync(readmePath, updated);
}

async function seedDemoSource() {
  const res = await fetch(`${baseUrl}/api/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "ollama logs",
      path: sampleLog,
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Failed to seed demo source: ${body}`);
  }
  return res.json();
}

async function captureScreenshot() {
  fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
  fs.rmSync(screenshotDataDir, { recursive: true, force: true });
  fs.mkdirSync(screenshotDataDir, { recursive: true });

  const server = spawn(
    "python",
    ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: root,
      env: {
        ...process.env,
        LOGS_HOME_DATA_DIR: screenshotDataDir,
      },
      stdio: "ignore",
      shell: true,
    },
  );

  let browser;
  try {
    await waitForServer();
    const source = await seedDemoSource();

    browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.goto(baseUrl);
    await page.waitForSelector("#app-version:not([hidden])");

    await page.locator(".source-item-info").first().click();
    await page.waitForSelector("#viewer:not([hidden])");
    await page.locator("#highlight-enabled").check();
    await page.locator("#highlight-pattern").fill("ERR");
    await page.waitForTimeout(300);

    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Screenshot saved to ${path.relative(root, screenshotPath)} (source: ${source.name})`);
    updateReadme();
    console.log("README updated with screenshot");
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
    await new Promise((resolve) => {
      server.on("exit", resolve);
      setTimeout(resolve, 2000);
    });
    fs.rmSync(screenshotDataDir, { recursive: true, force: true });
  }
}

captureScreenshot().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
