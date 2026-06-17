"""
SelfHealingDriver — drop-in replacement for Selenium WebDriver.

Wraps any Selenium WebDriver instance with self-healing capabilities.
Use it exactly like you would use a regular WebDriver, but broken
locators get automatically recovered.
"""

import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from self_healing.healer import Healer, HealingConfig
from self_healing.reporter import HealingReporter

logger = logging.getLogger(__name__)


class SelfHealingDriver:
    """
    A wrapper around Selenium WebDriver that adds self-healing capabilities.

    Usage:
        driver = SelfHealingDriver(browser="chrome")
        driver.get("https://example.com")
        element = driver.find_element("id", "my-button")
        driver.print_healing_report()
        driver.quit()
    """

    SUPPORTED_BROWSERS = ("chrome", "firefox", "edge")

    def __init__(
        self,
        browser: str = "chrome",
        config: Optional[HealingConfig] = None,
        driver: Optional[WebDriver] = None,
        headless: bool = False,
    ):
        """
        Initialize the self-healing driver.

        Args:
            browser: Browser to use ("chrome", "firefox", "edge")
            config: Healing configuration options
            driver: Existing WebDriver instance to wrap (optional)
            headless: Run browser in headless mode
        """
        self.config = config or HealingConfig()

        if driver:
            self._driver = driver
        else:
            self._driver = self._create_driver(browser, headless)

        self._healer = Healer(self._driver, self.config)
        self._reporter = HealingReporter(self._healer, self.config)

    def _create_driver(self, browser: str, headless: bool) -> WebDriver:
        """Create a WebDriver instance for the specified browser."""
        browser = browser.lower()

        if browser not in self.SUPPORTED_BROWSERS:
            raise ValueError(
                f"Unsupported browser: '{browser}'. "
                f"Choose from: {self.SUPPORTED_BROWSERS}"
            )

        if browser == "chrome":
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)

        elif browser == "firefox":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=options)

        elif browser == "edge":
            options = webdriver.EdgeOptions()
            if headless:
                options.add_argument("--headless=new")
            service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=options)

    def find_element(self, by: str, value: str) -> WebElement:
        """
        Find an element with self-healing support.

        If the primary locator fails, the healer tries alternative
        strategies to locate the element.
        """
        return self._healer.find_element(by, value)

    def find_elements(self, by: str, value: str) -> list[WebElement]:
        """
        Find multiple elements (no healing — returns empty list on failure).
        """
        return self._driver.find_elements(by, value)

    # --- Delegation to underlying WebDriver ---

    def get(self, url: str) -> None:
        """Navigate to a URL."""
        self._driver.get(url)

    @property
    def current_url(self) -> str:
        """Get the current page URL."""
        return self._driver.current_url

    @property
    def title(self) -> str:
        """Get the current page title."""
        return self._driver.title

    @property
    def page_source(self) -> str:
        """Get the current page source."""
        return self._driver.page_source

    def execute_script(self, script: str, *args):
        """Execute JavaScript in the browser."""
        return self._driver.execute_script(script, *args)

    def back(self) -> None:
        """Navigate back."""
        self._driver.back()

    def forward(self) -> None:
        """Navigate forward."""
        self._driver.forward()

    def refresh(self) -> None:
        """Refresh the page."""
        self._driver.refresh()

    def quit(self) -> None:
        """Quit the browser and close all windows."""
        self._driver.quit()

    def close(self) -> None:
        """Close the current window."""
        self._driver.close()

    def maximize_window(self) -> None:
        """Maximize the browser window."""
        self._driver.maximize_window()

    def implicitly_wait(self, time_to_wait: float) -> None:
        """Set implicit wait time."""
        self._driver.implicitly_wait(time_to_wait)

    @property
    def underlying_driver(self) -> WebDriver:
        """Access the raw Selenium WebDriver if needed."""
        return self._driver

    # --- Healing Report Methods ---

    def print_healing_report(self) -> None:
        """Print the healing report to console."""
        self._reporter.print_console_report()

    def save_healing_report(self, path: Optional[str] = None) -> str:
        """Save the healing report to a file. Returns the file path."""
        return self._reporter.save_report(path)

    def get_healing_summary(self) -> dict:
        """Get healing statistics as a dictionary."""
        return self._reporter.get_summary()

    def __enter__(self):
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-quit on context manager exit."""
        self.quit()
        return False
