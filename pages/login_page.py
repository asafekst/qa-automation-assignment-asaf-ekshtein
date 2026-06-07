import re

from playwright.sync_api import Page, expect

from constants import LOGIN_PATH, MSG_INVALID_LOGIN
from pages.assertions import expect_url
from pages.inventory_page import InventoryPage


class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error = page.get_by_test_id("error")

    def open(self) -> "LoginPage":
        self.page.goto(LOGIN_PATH)
        self.expect_on_login_page()
        return self

    def login_as(self, username: str, password: str) -> InventoryPage:
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()
        return InventoryPage(self.page)

    def expect_on_login_page(self) -> None:
        expect_url(self.page, rf"{re.escape(LOGIN_PATH)}$")
        expect(self.login_button).to_be_visible()
        expect(self.username).to_be_visible()

    def expect_invalid_credentials_error(self) -> None:
        self.expect_on_login_page()
        expect(self.error).to_be_visible()
        expect(self.error).to_have_text(MSG_INVALID_LOGIN)
