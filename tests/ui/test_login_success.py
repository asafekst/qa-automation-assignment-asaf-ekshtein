import pytest

from constants import PASSWORD, STANDARD_USER

pytestmark = [pytest.mark.ui, pytest.mark.smoke]


def test_login_success(login_page) -> None:
    login_page.open().login_as(STANDARD_USER, PASSWORD)
