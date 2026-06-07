"""Single source of truth for credentials, copy, products, and checkout totals."""

from dataclasses import dataclass

# --- Credentials ---

STANDARD_USER = "standard_user"
PASSWORD = "secret_sauce"
INVALID_PASSWORD = "wrong_password"

# --- URLs (path fragments for assertions) ---

LOGIN_PATH = "/"
INVENTORY_PATH = "inventory.html"
CART_PATH = "cart.html"
CHECKOUT_STEP_ONE_PATH = "checkout-step-one.html"
CHECKOUT_STEP_TWO_PATH = "checkout-step-two.html"
CHECKOUT_COMPLETE_PATH = "checkout-complete.html"

# --- Exact messages (tests fail if product copy changes) ---

MSG_INVALID_LOGIN = (
    "Epic sadface: Username and password do not match any user in this service"
)
MSG_ORDER_COMPLETE_HEADER = "Thank you for your order!"
# App randomizes ending — only these two variants are valid.
MSG_ORDER_COMPLETE_BODY = (
    r"^Your order has been dispatched, and will arrive just as fast as "
    r"(?:an ambulance|the pony can get there)!$"
)

TITLE_INVENTORY = "Products"
TITLE_CART = "Your Cart"
TITLE_CHECKOUT_INFO = "Checkout: Your Information"
TITLE_CHECKOUT_OVERVIEW = "Checkout: Overview"
TITLE_CHECKOUT_COMPLETE = "Checkout: Complete!"

# --- Checkout shipping (test input) ---


@dataclass(frozen=True, slots=True)
class ShippingInfo:
    first_name: str
    last_name: str
    postal_code: str


DEFAULT_SHIPPING = ShippingInfo(
    first_name="Jane",
    last_name="Doe",
    postal_code="12345",
)

# --- Checkout summary lines (Swag Labs tax rules are fixed for this catalog) ---


@dataclass(frozen=True, slots=True)
class CheckoutSummary:
    subtotal: str
    tax: str
    total: str


CHECKOUT_BACKPACK_ONLY = CheckoutSummary(
    subtotal="Item total: $29.99",
    tax="Tax: $2.40",
    total="Total: $32.39",
)

CHECKOUT_TWO_ITEMS = CheckoutSummary(
    subtotal="Item total: $39.98",
    tax="Tax: $3.20",
    total="Total: $43.18",
)

# --- Products (stable data-test ids from Swag Labs) ---


@dataclass(frozen=True, slots=True)
class Product:
    add_to_cart_id: str
    remove_from_cart_id: str
    name: str
    price: str


BACKPACK = Product(
    add_to_cart_id="add-to-cart-sauce-labs-backpack",
    remove_from_cart_id="remove-sauce-labs-backpack",
    name="Sauce Labs Backpack",
    price="$29.99",
)

BIKE_LIGHT = Product(
    add_to_cart_id="add-to-cart-sauce-labs-bike-light",
    remove_from_cart_id="remove-sauce-labs-bike-light",
    name="Sauce Labs Bike Light",
    price="$9.99",
)
