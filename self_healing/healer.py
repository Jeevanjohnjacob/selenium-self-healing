"""
Core healing logic and decision engine.

The Healer orchestrates the self-healing process:
1. Detects when a locator fails
2. Retrieves stored element fingerprints (if available)
3. Generates alternative locators using strategies
4. Scores candidates and picks the best match
5. Logs the healing event for reporting
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

from self_healing.locator_strategies import LocatorStrategyEngine
from self_healing.element_store import ElementStore

logger = logging.getLogger(__name__)


@dataclass
class HealingConfig:
    """Configuration for the self-healing behavior."""

    max_fallback_attempts: int = 5
    similarity_threshold: float = 0.7
    store_fingerprints: bool = True
    report_format: str = "console"  # "console", "html", "json"
    healing_enabled: bool = True


@dataclass
class HealingEvent:
    """Records a single healing event."""

    original_by: str
    original_value: str
    healed_by: Optional[str] = None
    healed_value: Optional[str] = None
    success: bool = False
    confidence: float = 0.0
    candidates_tried: int = 0
    page_url: str = ""


class Healer:
    """
    Core healing engine that attempts to find elements
    using alternative strategies when primary locators fail.
    """

    def __init__(self, driver: WebDriver, config: Optional[HealingConfig] = None):
        self.driver = driver
        self.config = config or HealingConfig()
        self.strategy_engine = LocatorStrategyEngine()
        self.element_store = ElementStore()
        self.healing_events: list[HealingEvent] = []
        self._total_lookups = 0
        self._primary_successes = 0

    @property
    def total_lookups(self) -> int:
        return self._total_lookups

    @property
    def primary_successes(self) -> int:
        return self._primary_successes

    @property
    def healed_count(self) -> int:
        return sum(1 for e in self.healing_events if e.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for e in self.healing_events if not e.success)

    def find_element(self, by: str, value: str) -> WebElement:
        """
        Attempt to find an element. If primary locator fails,
        engage healing strategies.
        """
        self._total_lookups += 1

        # Step 1: Try the primary locator
        try:
            element = self.driver.find_element(by, value)
            self._primary_successes += 1

            # Store fingerprint for future healing
            if self.config.store_fingerprints:
                self._store_element_fingerprint(element, by, value)

            return element
        except NoSuchElementException:
            if not self.config.healing_enabled:
                raise

            logger.info(
                f"Primary locator failed: {by}='{value}'. Attempting self-healing..."
            )

        # Step 2: Attempt healing
        return self._heal(by, value)

    def _heal(self, original_by: str, original_value: str) -> WebElement:
        """
        Core healing logic: generate alternatives, try each one,
        return the first match above the confidence threshold.
        """
        event = HealingEvent(
            original_by=original_by,
            original_value=original_value,
            page_url=self.driver.current_url,
        )

        # Get stored fingerprint if available
        fingerprint = self.element_store.get_fingerprint(original_by, original_value)

        # Generate alternative locator candidates
        candidates = self.strategy_engine.generate_alternatives(
            original_by=original_by,
            original_value=original_value,
            fingerprint=fingerprint,
            max_candidates=self.config.max_fallback_attempts,
        )

        # Try each candidate
        for i, candidate in enumerate(candidates):
            event.candidates_tried = i + 1
            try:
                element = self.driver.find_element(candidate.by, candidate.value)

                # Validate confidence
                confidence = self._calculate_confidence(
                    candidate, fingerprint, element
                )

                if confidence >= self.config.similarity_threshold:
                    event.success = True
                    event.healed_by = candidate.by
                    event.healed_value = candidate.value
                    event.confidence = confidence

                    logger.info(
                        f"✅ Healed! {original_by}='{original_value}' → "
                        f"{candidate.by}='{candidate.value}' "
                        f"(confidence: {confidence:.0%})"
                    )

                    # Update store with new locator info
                    if self.config.store_fingerprints:
                        self._store_element_fingerprint(
                            element, original_by, original_value
                        )

                    self.healing_events.append(event)
                    return element

            except NoSuchElementException:
                continue

        # All candidates failed
        event.success = False
        self.healing_events.append(event)

        raise NoSuchElementException(
            f"Self-healing failed: Could not find element with "
            f"{original_by}='{original_value}'. "
            f"Tried {event.candidates_tried} alternative locators."
        )

    def _calculate_confidence(self, candidate, fingerprint, element) -> float:
        """
        Calculate confidence score for a healed element.
        Higher score = more likely to be the correct element.
        """
        score = 0.5  # Base score for finding any element

        # Boost for matching tag name from fingerprint
        if fingerprint and fingerprint.get("tag_name"):
            if element.tag_name == fingerprint["tag_name"]:
                score += 0.2

        # Boost for matching text content
        if fingerprint and fingerprint.get("text"):
            element_text = element.text.strip()
            stored_text = fingerprint["text"].strip()
            if element_text and stored_text:
                if element_text == stored_text:
                    score += 0.25
                elif stored_text in element_text or element_text in stored_text:
                    score += 0.1

        # Boost based on strategy reliability
        score += candidate.reliability_bonus

        return min(score, 1.0)

    def _store_element_fingerprint(
        self, element: WebElement, by: str, value: str
    ) -> None:
        """Store element attributes for future healing reference."""
        try:
            fingerprint = {
                "tag_name": element.tag_name,
                "text": element.text[:100] if element.text else "",
                "attributes": self._get_element_attributes(element),
            }
            self.element_store.store(by, value, fingerprint)
        except Exception as e:
            logger.debug(f"Failed to store fingerprint: {e}")

    def _get_element_attributes(self, element: WebElement) -> dict:
        """Extract useful attributes from an element via JavaScript."""
        try:
            attrs = self.driver.execute_script(
                """
                var elem = arguments[0];
                var attrs = {};
                for (var i = 0; i < elem.attributes.length; i++) {
                    var attr = elem.attributes[i];
                    attrs[attr.name] = attr.value;
                }
                return attrs;
                """,
                element,
            )
            return attrs or {}
        except Exception:
            return {}
