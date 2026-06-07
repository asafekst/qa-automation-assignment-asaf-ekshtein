import pytest

from constants import BACKPACK, BIKE_LIGHT, PASSWORD, STANDARD_USER

pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_add_two_items_validates_badge_and_cart(login_page) -> None:
    inventory = login_page.open().login_as(STANDARD_USER, PASSWORD)
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(BIKE_LIGHT)
    inventory.expect_cart_badge(2)

    cart = inventory.open_cart()
    cart.expect_products([BACKPACK, BIKE_LIGHT])
