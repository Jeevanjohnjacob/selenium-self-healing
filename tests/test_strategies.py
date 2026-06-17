"""
Unit tests for LocatorStrategyEngine.

Tests that the strategy engine generates sensible alternative
locators based on different inputs and fingerprints.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from self_healing.locator_strategies import LocatorStrategyEngine, LocatorCandidate


class TestStrategyEngineBasic:
    """Test basic alternative generation."""

    def setup_method(self):
        self.engine = LocatorStrategyEngine()

    def test_generates_alternatives_without_fingerprint(self):
        """Should generate at least some alternatives even without fingerprint."""
        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="submit-btn",
            fingerprint=None,
        )

        assert len(candidates) > 0
        # Should not include the original locator
        for c in candidates:
            assert not (c.by == "id" and c.value == "submit-btn")

    def test_generates_more_with_fingerprint(self):
        """Should generate more alternatives when fingerprint is available."""
        fingerprint = {
            "tag_name": "button",
            "text": "Submit",
            "attributes": {
                "class": "btn btn-primary submit-button",
                "name": "submit",
                "data-testid": "submit-form-btn",
                "type": "submit",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="submit-btn",
            fingerprint=fingerprint,
        )

        assert len(candidates) >= 3

    def test_respects_max_candidates(self):
        """Should not return more candidates than max_candidates."""
        fingerprint = {
            "tag_name": "button",
            "text": "Submit",
            "attributes": {
                "class": "btn btn-primary",
                "name": "submit",
                "data-testid": "submit-btn",
                "type": "submit",
                "aria-label": "Submit form",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="old-id",
            fingerprint=fingerprint,
            max_candidates=3,
        )

        assert len(candidates) <= 3

    def test_no_duplicate_candidates(self):
        """Should not return duplicate locators."""
        fingerprint = {
            "tag_name": "input",
            "text": "",
            "attributes": {
                "class": "form-control",
                "name": "email",
                "type": "email",
                "placeholder": "Enter email",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="email-input",
            fingerprint=fingerprint,
        )

        seen = set()
        for c in candidates:
            key = (c.by, c.value)
            assert key not in seen, f"Duplicate candidate: {c}"
            seen.add(key)


class TestDataAttributeStrategy:
    """Test data-* attribute strategy."""

    def setup_method(self):
        self.engine = LocatorStrategyEngine()

    def test_finds_data_testid(self):
        """Should prioritize data-testid attributes."""
        fingerprint = {
            "tag_name": "button",
            "text": "Save",
            "attributes": {
                "data-testid": "save-button",
                "class": "btn",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="old-save-btn",
            fingerprint=fingerprint,
        )

        data_candidates = [c for c in candidates if "data-testid" in c.value]
        assert len(data_candidates) > 0
        assert data_candidates[0].reliability_bonus >= 0.2

    def test_finds_data_cy(self):
        """Should find data-cy attributes (Cypress convention)."""
        fingerprint = {
            "tag_name": "a",
            "text": "Profile",
            "attributes": {
                "data-cy": "nav-profile-link",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="profile-link",
            fingerprint=fingerprint,
        )

        data_candidates = [c for c in candidates if "data-cy" in c.value]
        assert len(data_candidates) > 0


class TestTextContentStrategy:
    """Test text content matching strategy."""

    def setup_method(self):
        self.engine = LocatorStrategyEngine()

    def test_generates_text_xpath(self):
        """Should generate XPath based on text content."""
        fingerprint = {
            "tag_name": "button",
            "text": "Sign In",
            "attributes": {"class": "login-btn"},
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="signin-btn",
            fingerprint=fingerprint,
        )

        xpath_text_candidates = [
            c for c in candidates if c.strategy_name.startswith("text_")
        ]
        assert len(xpath_text_candidates) > 0

    def test_skips_long_text(self):
        """Should not use text content strategy for very long text."""
        fingerprint = {
            "tag_name": "p",
            "text": "A" * 100,  # Very long text
            "attributes": {},
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="long-paragraph",
            fingerprint=fingerprint,
        )

        xpath_text_candidates = [
            c for c in candidates if c.strategy_name.startswith("text_")
        ]
        assert len(xpath_text_candidates) == 0


class TestCSSClassStrategy:
    """Test CSS class-based strategy."""

    def setup_method(self):
        self.engine = LocatorStrategyEngine()

    def test_uses_specific_classes(self):
        """Should use specific class names, not utility classes."""
        fingerprint = {
            "tag_name": "div",
            "text": "",
            "attributes": {
                "class": "mt-4 mb-2 product-card-container featured",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="card-1",
            fingerprint=fingerprint,
        )

        css_candidates = [c for c in candidates if c.strategy_name.startswith("css_")]
        # Should prefer "product-card-container" over "mt-4"
        if css_candidates:
            assert "product-card-container" in css_candidates[0].value

    def test_ignores_utility_classes(self):
        """Should not build selectors from utility-only classes."""
        fingerprint = {
            "tag_name": "div",
            "text": "",
            "attributes": {
                "class": "mt-4 mb-2 p-3 w-full",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="util-div",
            fingerprint=fingerprint,
        )

        css_candidates = [c for c in candidates if c.strategy_name.startswith("css_")]
        # All classes are utility — should not generate CSS class candidates
        assert len(css_candidates) == 0


class TestXPathStrategy:
    """Test XPath structural strategy."""

    def setup_method(self):
        self.engine = LocatorStrategyEngine()

    def test_aria_label_xpath(self):
        """Should generate XPath from aria-label."""
        fingerprint = {
            "tag_name": "button",
            "text": "",
            "attributes": {
                "aria-label": "Close dialog",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="close-btn",
            fingerprint=fingerprint,
        )

        aria_candidates = [
            c for c in candidates if "aria-label" in c.value
        ]
        assert len(aria_candidates) > 0

    def test_placeholder_xpath(self):
        """Should generate XPath from placeholder attribute."""
        fingerprint = {
            "tag_name": "input",
            "text": "",
            "attributes": {
                "placeholder": "Search products...",
                "type": "text",
            },
        }

        candidates = self.engine.generate_alternatives(
            original_by="id",
            original_value="search-input",
            fingerprint=fingerprint,
        )

        placeholder_candidates = [
            c for c in candidates if "placeholder" in c.value
        ]
        assert len(placeholder_candidates) > 0
