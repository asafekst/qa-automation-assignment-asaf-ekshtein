import re

from playwright.sync_api import Page, expect

from constants import CART_PATH, TITLE_CART, Product
from pages.assertions import expect_cart_line_items, expect_url
from pages.checkout_page import CheckoutPage


class CartPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.title = page.get_by_test_id("title")
        self.cart_list = page.get_by_test_id("cart-list")

    def expect_loaded(self) -> None:
        expect_url(self.page, rf"{re.escape(CART_PATH)}$")
        expect(self.title).to_have_text(TITLE_CART)
        expect(self.cart_list).to_be_visible()

    def expect_products(self, products: list[Product]) -> None:
        expect_cart_line_items(self.page, products)

    def checkout(self) -> CheckoutPage:
        self.page.get_by_test_id("checkout").click()
        return CheckoutPage(self.page)
