import re

from playwright.sync_api import Page, expect

from constants import INVENTORY_PATH, TITLE_INVENTORY, Product
from pages.assertions import expect_url
from pages.cart_page import CartPage


class InventoryPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.title = page.get_by_test_id("title")
        self.inventory_list = page.get_by_test_id("inventory-list")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.cart_link = page.get_by_test_id("shopping-cart-link")

    def expect_loaded(self) -> None:
        expect_url(self.page, rf"{re.escape(INVENTORY_PATH)}$")
        expect(self.title).to_have_text(TITLE_INVENTORY)
        expect(self.inventory_list).to_be_visible()
        expect(self.page.get_by_test_id("inventory-item")).not_to_have_count(0)

    def add_to_cart(self, product: Product) -> None:
        self.page.get_by_test_id(product.add_to_cart_id).click()
        expect(self.page.get_by_test_id(product.remove_from_cart_id)).to_be_visible()

    def expect_cart_badge(self, count: int) -> None:
        if count == 0:
            expect(self.cart_badge).to_be_hidden()
        else:
            expect(self.cart_badge).to_be_visible()
            expect(self.cart_badge).to_have_text(str(count))

    def open_cart(self) -> CartPage:
        self.cart_link.click()
        cart = CartPage(self.page)
        cart.expect_loaded()
        return cart
