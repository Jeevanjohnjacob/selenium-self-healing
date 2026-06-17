"""
Example: Using Self-Healing Driver with pytest
================================================

This shows how to use the SelfHealingDriver in a pytest test suite.
The driver is a drop-in replacement for regular Selenium WebDriver.

Run: pytest examples/sample_test.py -v
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from self_healing import SelfHealingDriver, HealingConfig


@pytest.fixture
def driver():
    """Create a self-healing driver for tests."""
    config = HealingConfig(
        max_fallback_attempts=5,
        similarity_threshold=0.6,
        store_fingerprints=True,
        healing_enabled=True,
    )

    driver = SelfHealingDriver(browser="chrome", config=config, headless=True)
    yield driver

    # Print report after each test
    driver.print_healing_report()
    driver.quit()


class TestLoginPage:
    """Test the login page with self-healing locators."""

    LOGIN_URL = "https://the-internet.herokuapp.com/login"

    def test_successful_login(self, driver):
        """Test a successful login flow."""
        driver.get(self.LOGIN_URL)

        # These locators work normally
        driver.find_element("id", "username").send_keys("tomsmith")
        driver.find_element("id", "password").send_keys("SuperSecretPassword!")
        driver.find_element("css selector", "button[type='submit']").click()

        # Verify success
        flash = driver.find_element("css selector", ".flash.success")
        assert "You logged into" in flash.text

    def test_failed_login(self, driver):
        """Test a failed login shows error message."""
        driver.get(self.LOGIN_URL)

        driver.find_element("id", "username").send_keys("wronguser")
        driver.find_element("id", "password").send_keys("wrongpass")
        driver.find_element("css selector", "button[type='submit']").click()

        # Verify error
        flash = driver.find_element("css selector", ".flash.error")
        assert "Your username is invalid" in flash.text

    def test_page_elements_present(self, driver):
        """Test that all expected elements are present on the page."""
        driver.get(self.LOGIN_URL)

        # These should all be found without healing
        heading = driver.find_element("css selector", "h2")
        assert "Login Page" in heading.text

        username_input = driver.find_element("id", "username")
        assert username_input is not None

        password_input = driver.find_element("id", "password")
        assert password_input is not None
