import pytest

from constants import (
    BACKPACK,
    CHECKOUT_BACKPACK_ONLY,
    DEFAULT_SHIPPING,
    PASSWORD,
    STANDARD_USER,
)

pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_checkout_end_to_end(login_page) -> None:
    inventory = login_page.open().login_as(STANDARD_USER, PASSWORD)
    inventory.expect_loaded()
    inventory.add_to_cart(BACKPACK)

    checkout = inventory.open_cart().checkout()
    checkout.fill_shipping(DEFAULT_SHIPPING)
    checkout.expect_overview([BACKPACK], CHECKOUT_BACKPACK_ONLY)
    checkout.finish_order()
    checkout.expect_confirmation()
