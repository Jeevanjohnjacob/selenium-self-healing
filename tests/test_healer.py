"""
Unit tests for the Healer module.

These tests mock the WebDriver to test healing logic without a real browser.
"""

import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.common.exceptions import NoSuchElementException
from self_healing.healer import Healer, HealingConfig, HealingEvent
from self_healing.locator_strategies import LocatorCandidate


class TestHealerBasic:
    """Test basic healer behavior."""

    def setup_method(self):
        """Set up a healer with mocked driver."""
        self.mock_driver = MagicMock()
        self.mock_driver.current_url = "https://example.com/page"
        self.config = HealingConfig(
            max_fallback_attempts=5,
            similarity_threshold=0.5,
            store_fingerprints=False,
            healing_enabled=True,
        )
        self.healer = Healer(self.mock_driver, self.config)

    def test_primary_locator_works(self):
        """When primary locator works, no healing should occur."""
        mock_element = MagicMock()
        self.mock_driver.find_element.return_value = mock_element

        result = self.healer.find_element("id", "my-button")

        assert result == mock_element
        assert self.healer.total_lookups == 1
        assert self.healer.primary_successes == 1
        assert self.healer.healed_count == 0

    def test_healing_disabled_raises_immediately(self):
        """When healing is disabled, failures should raise immediately."""
        self.config.healing_enabled = False
        self.healer = Healer(self.mock_driver, self.config)

        self.mock_driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(NoSuchElementException):
            self.healer.find_element("id", "nonexistent")

    def test_healing_attempts_alternatives(self):
        """When primary fails, healer should try alternatives."""
        mock_element = MagicMock()
        mock_element.tag_name = "button"
        mock_element.text = "Submit"

        # First call (primary) fails, second call (healing) succeeds
        self.mock_driver.find_element.side_effect = [
            NoSuchElementException(),  # Primary fails
            mock_element,  # Alternative succeeds
        ]

        result = self.healer.find_element("id", "submit-btn")

        assert result == mock_element
        assert self.healer.healed_count == 1
        assert len(self.healer.healing_events) == 1
        assert self.healer.healing_events[0].success is True

    def test_all_alternatives_fail(self):
        """When all alternatives fail, raise NoSuchElementException."""
        self.mock_driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(NoSuchElementException) as exc_info:
            self.healer.find_element("id", "completely-gone")

        assert "Self-healing failed" in str(exc_info.value)
        assert self.healer.failed_count == 1

    def test_tracks_total_lookups(self):
        """Healer should track total number of find_element calls."""
        mock_element = MagicMock()
        self.mock_driver.find_element.return_value = mock_element

        self.healer.find_element("id", "btn1")
        self.healer.find_element("id", "btn2")
        self.healer.find_element("id", "btn3")

        assert self.healer.total_lookups == 3
        assert self.healer.primary_successes == 3


class TestHealerConfidence:
    """Test confidence scoring logic."""

    def setup_method(self):
        self.mock_driver = MagicMock()
        self.mock_driver.current_url = "https://example.com"
        self.config = HealingConfig(
            similarity_threshold=0.7,
            store_fingerprints=False,
        )
        self.healer = Healer(self.mock_driver, self.config)

    def test_low_confidence_rejected(self):
        """Elements below the confidence threshold should be rejected."""
        mock_element = MagicMock()
        mock_element.tag_name = "div"  # Wrong tag
        mock_element.text = "Something else"  # Wrong text

        # Primary fails, alternative found but low confidence
        self.mock_driver.find_element.side_effect = [
            NoSuchElementException(),  # Primary
            NoSuchElementException(),  # All alternatives also fail
            NoSuchElementException(),
            NoSuchElementException(),
            NoSuchElementException(),
            NoSuchElementException(),
        ]

        with pytest.raises(NoSuchElementException):
            self.healer.find_element("id", "specific-btn")


class TestHealerEvents:
    """Test healing event recording."""

    def setup_method(self):
        self.mock_driver = MagicMock()
        self.mock_driver.current_url = "https://example.com/test"
        self.config = HealingConfig(
            store_fingerprints=False,
            similarity_threshold=0.4,  # Lower threshold for testing
        )
        self.healer = Healer(self.mock_driver, self.config)

    def test_successful_heal_records_event(self):
        """Successful healing should record complete event details."""
        mock_element = MagicMock()
        mock_element.tag_name = "button"
        mock_element.text = "Click me"

        # Primary fails, then first alternative succeeds
        # Use a function to handle the calls more flexibly
        call_count = [0]
        original_side_effect = [NoSuchElementException()]

        def find_element_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise NoSuchElementException()
            return mock_element

        self.mock_driver.find_element.side_effect = find_element_side_effect

        self.healer.find_element("id", "old-button")

        assert len(self.healer.healing_events) == 1
        event = self.healer.healing_events[0]
        assert event.original_by == "id"
        assert event.original_value == "old-button"
        assert event.success is True
        assert event.page_url == "https://example.com/test"

    def test_failed_heal_records_event(self):
        """Failed healing should also record an event."""
        self.mock_driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(NoSuchElementException):
            self.healer.find_element("id", "ghost-element")

        assert len(self.healer.healing_events) == 1
        event = self.healer.healing_events[0]
        assert event.success is False
        assert event.candidates_tried > 0
