import pytest

from constants import INVALID_PASSWORD, STANDARD_USER

pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_login_failure_strict_error(login_page) -> None:
    login_page.open()
    login_page.login_as(STANDARD_USER, INVALID_PASSWORD)
    login_page.expect_invalid_credentials_error()
