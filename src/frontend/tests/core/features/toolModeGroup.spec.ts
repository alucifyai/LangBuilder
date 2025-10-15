import { expect, test } from "@playwright/test";
import { awaitBootstrapTest } from "../../utils/await-bootstrap-test";
import { loginLangflow } from "../../utils/login-langflow";

test.describe("group node test", () => {
  /// <reference lib="dom"/>
  // TODO: fix this test
  test.skip(
    "group and ungroup updating values",
    { tag: ["@release", "@workspace", "@components"] },
    async ({ page }) => {
      await loginLangflow(page);
      await awaitBootstrapTest(page, { skipGoto: true });

      await page.getByTestId("side_nav_options_all-templates").click();
      await page
        .getByRole("heading", { name: "Basic Prompting" })
        .first()
        .click();
      await page.getByTestId("fit_view").first().click();

      await page
        .getByTestId("title-OpenAI")
        .click({ modifiers: ["ControlOrMeta"] });
      await page
        .getByTestId("title-Prompt")
        .click({ modifiers: ["ControlOrMeta"] });

      await page.getByRole("button", { name: "Group" }).click();
      await page.getByTestId("title-Group").click();
      await expect(page.getByTestId("tool-mode-button")).toBeHidden();
    },
  );
});
