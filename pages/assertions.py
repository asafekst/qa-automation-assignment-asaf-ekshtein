"""Shared Playwright assertions reused across page objects."""

import re

from playwright.sync_api import Page, expect

from constants import Product


def expect_url(page: Page, pattern: str) -> None:
    expect(page).to_have_url(re.compile(pattern))


def expect_product_names(page: Page, products: list[Product]) -> None:
    names = page.get_by_test_id("inventory-item-name")
    for product in products:
        expect(names.get_by_text(product.name, exact=True)).to_have_count(1)


def expect_cart_line_items(page: Page, products: list[Product]) -> None:
    names = page.get_by_test_id("inventory-item-name")
    prices = page.get_by_test_id("inventory-item-price")
    expect(names).to_have_count(len(products))
    expect(prices).to_have_count(len(products))
    for product in products:
        expect(names.get_by_text(product.name, exact=True)).to_have_count(1)
        expect(prices.get_by_text(product.price, exact=True)).to_have_count(1)
