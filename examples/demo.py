"""
Demo: Self-Healing Selenium in Action
======================================

This demo shows how the self-healing framework handles broken locators.
It navigates to a page, finds elements using locators that simulate
real-world breakage scenarios.

Run: python examples/demo.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from self_healing import SelfHealingDriver, HealingConfig


def main():
    """Run the self-healing demo."""
    print("🩺 Selenium Self-Healing Framework — Demo")
    print("=" * 50)
    print()

    # Configure the healer
    config = HealingConfig(
        max_fallback_attempts=5,
        similarity_threshold=0.6,
        store_fingerprints=True,
        report_format="html",
        healing_enabled=True,
    )

    # Create the self-healing driver
    driver = SelfHealingDriver(browser="chrome", config=config, headless=True)

    try:
        # Navigate to a test page
        print("📍 Navigating to https://the-internet.herokuapp.com/login")
        driver.get("https://the-internet.herokuapp.com/login")
        print(f"   Page title: {driver.title}")
        print()

        # --- Scenario 1: Normal find (no healing needed) ---
        print("🔍 Scenario 1: Finding username field by ID (should work normally)")
        username_field = driver.find_element("id", "username")
        username_field.send_keys("tomsmith")
        print("   ✅ Found and filled username field")
        print()

        # --- Scenario 2: Normal find ---
        print("🔍 Scenario 2: Finding password field by ID (should work normally)")
        password_field = driver.find_element("id", "password")
        password_field.send_keys("SuperSecretPassword!")
        print("   ✅ Found and filled password field")
        print()

        # --- Scenario 3: Find login button ---
        print("🔍 Scenario 3: Finding login button by CSS")
        login_btn = driver.find_element("css selector", "button[type='submit']")
        print(f"   ✅ Found button: '{login_btn.text}'")
        print()

        # --- Scenario 4: Simulate a broken locator ---
        print("🔍 Scenario 4: Trying a BROKEN locator (simulating a UI change)")
        print("   Attempting to find: id='login-button' (doesn't exist)")
        try:
            # This ID doesn't exist — the healer will try alternatives
            btn = driver.find_element("id", "login-button")
            print(f"   ✅ Healed! Found element: '{btn.text}'")
        except Exception as e:
            print(f"   ❌ Could not heal: {e}")
        print()

        # --- Scenario 5: Click login and find result ---
        print("🔍 Scenario 5: Clicking login and finding result message")
        login_btn.click()
        flash_message = driver.find_element("css selector", ".flash")
        print(f"   ✅ Login result: '{flash_message.text.strip()[:50]}...'")
        print()

        # --- Print the healing report ---
        print("=" * 50)
        driver.print_healing_report()

        # Save HTML report
        report_path = driver.save_healing_report()
        print(f"📄 Full report saved to: {report_path}")

    finally:
        driver.quit()
        print("\n🏁 Demo complete!")


if __name__ == "__main__":
    main()
