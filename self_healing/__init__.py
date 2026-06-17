"""
Selenium Self-Healing Test Framework
=====================================

A smart Selenium wrapper that automatically recovers from broken locators.

Usage:
    from self_healing import SelfHealingDriver, HealingConfig

    driver = SelfHealingDriver(browser="chrome")
    driver.get("https://example.com")
    element = driver.find_element("id", "my-button")
    driver.print_healing_report()
    driver.quit()
"""

from self_healing.driver import SelfHealingDriver
from self_healing.healer import Healer, HealingConfig
from self_healing.reporter import HealingReporter

__version__ = "1.0.0"
__all__ = ["SelfHealingDriver", "Healer", "HealingConfig", "HealingReporter"]
