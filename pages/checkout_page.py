import re

from playwright.sync_api import Page, expect

from constants import (
    CHECKOUT_COMPLETE_PATH,
    CHECKOUT_STEP_ONE_PATH,
    CHECKOUT_STEP_TWO_PATH,
    MSG_ORDER_COMPLETE_BODY,
    MSG_ORDER_COMPLETE_HEADER,
    TITLE_CHECKOUT_COMPLETE,
    TITLE_CHECKOUT_INFO,
    TITLE_CHECKOUT_OVERVIEW,
    CheckoutSummary,
    Product,
    ShippingInfo,
)
from pages.assertions import expect_product_names, expect_url


class CheckoutPage:

    def __init__(self, page: Page) -> None:

        self.page = page

        self.title = page.get_by_test_id("title")



    def fill_shipping(self, shipping: ShippingInfo) -> None:
        expect_url(self.page, rf"{re.escape(CHECKOUT_STEP_ONE_PATH)}$")
        expect(self.title).to_have_text(TITLE_CHECKOUT_INFO)
        self.page.get_by_test_id("firstName").fill(shipping.first_name)
        self.page.get_by_test_id("lastName").fill(shipping.last_name)
        self.page.get_by_test_id("postalCode").fill(shipping.postal_code)

        self.page.get_by_test_id("continue").click()



    def expect_overview(self, products: list[Product], summary: CheckoutSummary) -> None:

        expect_url(self.page, rf"{re.escape(CHECKOUT_STEP_TWO_PATH)}$")

        expect(self.title).to_have_text(TITLE_CHECKOUT_OVERVIEW)

        expect(self.page.get_by_test_id("payment-info-label")).to_be_visible()

        expect_product_names(self.page, products)

        expect(self.page.get_by_test_id("subtotal-label")).to_have_text(summary.subtotal)

        expect(self.page.get_by_test_id("tax-label")).to_have_text(summary.tax)

        expect(self.page.get_by_test_id("total-label")).to_have_text(summary.total)



    def finish_order(self) -> None:

        self.page.get_by_test_id("finish").click()



    def expect_confirmation(self) -> None:

        expect_url(self.page, rf"{re.escape(CHECKOUT_COMPLETE_PATH)}$")

        expect(self.title).to_have_text(TITLE_CHECKOUT_COMPLETE)

        expect(self.page.get_by_test_id("complete-header")).to_have_text(

            MSG_ORDER_COMPLETE_HEADER

        )

        expect(self.page.get_by_test_id("complete-text")).to_have_text(

            re.compile(MSG_ORDER_COMPLETE_BODY)

        )


