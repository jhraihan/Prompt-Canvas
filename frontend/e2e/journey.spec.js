import { expect, test } from "@playwright/test";

function newAccount() {
  const stamp = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  return {
    email: `e2e-${stamp}@example.com`,
    password: "a-long-enough-e2e-passphrase",
  };
}

async function register(page, account) {
  await page.goto("/register");
  await page.getByLabel(/email/i).fill(account.email);
  await page.getByLabel(/password/i).fill(account.password);
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page.getByRole("heading", { name: /imagine it/i })).toBeVisible();
}

async function generate(page, prompt) {
  await page.getByLabel(/describe your image/i).fill(prompt);
  await page.getByRole("button", { name: /generate image/i }).click();

  await expect(page.getByAltText(new RegExp(`generated image: ${prompt}`, "i"))).toBeVisible({
    timeout: 20_000,
  });
}

test.describe("the core journey", () => {
  test("register, generate, review in history, then delete", async ({ page }) => {
    const account = newAccount();
    const prompt = "a harbour at dawn";

    await test.step("register", async () => {
      await register(page, account);
    });

    await test.step("generate an image", async () => {
      await generate(page, prompt);
      const result = page.getByRole("region", { name: /result/i });
      await expect(result.getByRole("button", { name: /^download$/i })).toBeVisible();
    });

    await test.step("it appears in history", async () => {
      await page.getByRole("link", { name: /history/i }).click();
      await expect(page.getByRole("heading", { name: /your gallery/i })).toBeVisible();

      const card = page.getByRole("article").filter({ hasText: prompt });
      await expect(card).toBeVisible();
      await expect(card.getByAltText(new RegExp(prompt, "i"))).toBeVisible();
    });

    await test.step("delete it", async () => {
      await page.getByRole("button", { name: /delete this image/i }).click();
      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();
      await dialog.getByRole("button", { name: /delete image/i }).click();
      await expect(page.getByText(/no images yet/i)).toBeVisible();
    });
  });

  test("a signed-out visitor is sent to sign in", async ({ page }) => {
    await page.goto("/history");
    await expect(page).toHaveURL(/\/login/);
  });

  test("the session survives a reload", async ({ page }) => {

    const account = newAccount();
    await register(page, account);

    await page.reload();

    await expect(page.getByRole("heading", { name: /imagine it/i })).toBeVisible();
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("signing out ends the session", async ({ page }) => {
    const account = newAccount();
    await register(page, account);

    await page.getByRole("button", { name: /sign out/i }).click();

    await expect(page.getByRole("link", { name: /^sign in$/i })).toBeVisible();

    await page.goto("/history");
    await expect(page).toHaveURL(/\/login/);
  });

  test("one account cannot see another's history", async ({ page }) => {
    const first = newAccount();
    await register(page, first);
    await generate(page, "a private lighthouse");

    await page.getByRole("button", { name: /sign out/i }).click();
    await expect(page.getByRole("link", { name: /^sign in$/i })).toBeVisible();

    const second = newAccount();
    await register(page, second);
    await page.getByRole("link", { name: /history/i }).click();

    await expect(page.getByText(/no images yet/i)).toBeVisible();
    await expect(page.getByText("a private lighthouse")).toHaveCount(0);
  });
});

test.describe("validation", () => {
  test("Generate stays disabled until the prompt is long enough", async ({ page }) => {
    await register(page, newAccount());

    const button = page.getByRole("button", { name: /generate image/i });
    await expect(button).toBeDisabled();

    await page.getByLabel(/describe your image/i).fill("a fox");
    await expect(button).toBeEnabled();
  });

  test("the quota is shown and decreases after generating", async ({ page }) => {
    await register(page, newAccount());

    const quota = page.getByText(/of \d+ left/i);
    await expect(quota).toBeVisible();
    const before = await quota.textContent();

    await generate(page, "a copper teapot");

    await expect(quota).not.toHaveText(before);
  });
});

test.describe("saved prompts", () => {
  test("a saved prompt can be restored", async ({ page }) => {
    await register(page, newAccount());
    const prompt = "a snow leopard on a ridge";

    await page.getByLabel(/describe your image/i).fill(prompt);
    await page.getByRole("button", { name: /^save$/i }).click();
    await expect(page.getByRole("button", { name: /^saved$/i })).toBeVisible();

    const entry = page.locator(`button[title="${prompt}"]`);
    await expect(entry).toBeVisible();

    await page.getByLabel(/describe your image/i).fill("something else entirely");
    await entry.click();

    await expect(page.getByLabel(/describe your image/i)).toHaveValue(prompt);
  });
});

test.describe("sharing", () => {
  test("a share link works without an account", async ({ page, context }) => {
    await register(page, newAccount());
    await generate(page, "a shared harbour");

    await page.getByRole("link", { name: /history/i }).click();
    await page.getByRole("button", { name: /share this image/i }).click();
    await page.getByRole("button", { name: /create share link/i }).click();

    const link = page.locator("li").filter({ hasText: "/shared/" }).first();
    await expect(link).toBeVisible();
    const url = (await link.locator("p").first().textContent()).trim();

    const anonymous = await context.browser().newContext();
    const visitor = await anonymous.newPage();
    await visitor.goto(url);

    await expect(visitor.getByText("a shared harbour")).toBeVisible();
    await anonymous.close();
  });
});
