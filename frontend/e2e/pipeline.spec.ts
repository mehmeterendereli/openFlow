import { expect, test } from "@playwright/test";

test("generates, renders, and prepares a track for publishing", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Local library")).toBeVisible();
  await page.getByLabel("Track direction").fill("Nocturnal analog synthwave with steady drums");
  await page.getByLabel("Duration").selectOption("4");
  await page.getByRole("button", { name: "Generate track" }).click();

  await expect(page.getByRole("status")).toContainText("Audio generated");
  await expect(page.locator("audio")).toHaveAttribute("src", /\/media\/audio\//);
  await expect(page.getByText("AI generator")).toBeVisible();

  await page.getByRole("button", { name: "Render 1080p video" }).click();
  await expect(page.getByRole("status")).toContainText("1080p video rendered");
  await expect(page.locator("video")).toHaveAttribute("src", /\/media\/video\//);

  await page.getByRole("button", { name: "Validate publish package" }).click();
  await expect(page.getByRole("status")).toContainText("Upload manifest saved locally");
  await expect(page.getByText("validated", { exact: true }).first()).toBeVisible();
});
