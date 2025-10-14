import type { Page } from "playwright/test";

export const loginLangflow = async (
  page: Page,
  username: string = "langflow",
  password: string = "langflow",
  options?: {
    skipGoto?: boolean;
    beforeSignIn?: () => Promise<void>;
    afterSignIn?: () => Promise<void>;
  }
) => {
  if (!options?.skipGoto) {
    await page.goto("/");
  }

  // Wait for login page to appear
  await page.waitForSelector("text=sign in to langflow", { timeout: 30000 });

  // Fill credentials
  await page.getByPlaceholder("Username").fill(username);
  await page.getByPlaceholder("Password").fill(password);

  // Execute optional callback before clicking Sign In (e.g., for sessionStorage manipulation)
  if (options?.beforeSignIn) {
    await options.beforeSignIn();
  }

  // Click sign in button
  await page.getByRole("button", { name: "Sign In" }).click();

  // Execute optional callback after clicking Sign In but before waiting for success
  if (options?.afterSignIn) {
    await options.afterSignIn();
  }

  // Wait for successful login - main page should appear
  await page.waitForSelector('[data-testid="mainpage_title"]', {
    timeout: 30000,
  });
};
