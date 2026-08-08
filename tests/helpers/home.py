"""Lightweight page helpers for the Logs Home SPA."""

from __future__ import annotations

from playwright.sync_api import Page, expect


class HomePage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def goto(self) -> None:
        self.page.goto(self.base_url)
        expect(self.page.locator("#app-version")).to_be_visible()

    def add_source(self, name: str, path: str) -> None:
        self.page.locator("#source-name").fill(name)
        self.page.locator("#source-path").fill(path)
        self.page.locator("#source-form").locator("button[type='submit']").click()
        expect(self.page.locator("#source-list").get_by_text(name, exact=True)).to_be_visible()

    def select_source(self, name: str) -> None:
        self.page.locator(".source-item").filter(has_text=name).locator(
            ".source-item-info"
        ).click()
        expect(self.page.locator("#viewer")).to_be_visible()
        expect(self.page.locator("#viewer-title")).to_have_text(name)

    def delete_source(self, name: str) -> None:
        item = self.page.locator(".source-item").filter(has_text=name)
        self.page.once("dialog", lambda dialog: dialog.accept())
        item.locator(".delete-btn").click()
        expect(self.page.locator("#source-list").get_by_text(name, exact=True)).to_have_count(0)

    def enable_highlight(self, pattern: str = "ERR") -> None:
        self.page.locator("#highlight-enabled").check()
        self.page.locator("#highlight-pattern").fill(pattern)

    def click_preset(self, pattern: str) -> None:
        self.page.locator(f".preset[data-pattern='{pattern}']").click()
        expect(self.page.locator("#highlight-pattern")).to_have_value(pattern)
        expect(self.page.locator("#highlight-enabled")).to_be_checked()

    def set_line_count(self, count: str) -> None:
        self.page.locator("#line-count").select_option(count)
