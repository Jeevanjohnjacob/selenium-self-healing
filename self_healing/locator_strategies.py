"""
Locator Strategy Engine — generates alternative locators when primary ones fail.

Each strategy produces candidate locators ranked by reliability.
The engine combines multiple strategies and deduplicates results.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LocatorCandidate:
    """A potential alternative locator with metadata."""

    by: str
    value: str
    strategy_name: str
    reliability_bonus: float = 0.0  # Added to confidence score

    def __repr__(self):
        return f"Candidate({self.by}='{self.value}', strategy={self.strategy_name})"


class LocatorStrategyEngine:
    """
    Generates alternative locator candidates based on the original
    locator and any stored element fingerprint data.
    """

    def generate_alternatives(
        self,
        original_by: str,
        original_value: str,
        fingerprint: Optional[dict] = None,
        max_candidates: int = 5,
    ) -> list[LocatorCandidate]:
        """
        Generate a ranked list of alternative locator candidates.

        Strategies are tried in order of reliability:
        1. data-testid / data-* attributes (most stable)
        2. name attribute
        3. CSS class-based selectors
        4. Text content matching
        5. XPath structural
        6. Tag + attribute combinations
        """
        candidates = []

        # Strategy 1: data-* attribute based (highest reliability)
        candidates.extend(
            self._strategy_data_attributes(original_by, original_value, fingerprint)
        )

        # Strategy 2: name attribute
        candidates.extend(
            self._strategy_name_attribute(original_by, original_value, fingerprint)
        )

        # Strategy 3: CSS class-based
        candidates.extend(
            self._strategy_css_class(original_by, original_value, fingerprint)
        )

        # Strategy 4: Text content
        candidates.extend(
            self._strategy_text_content(original_by, original_value, fingerprint)
        )

        # Strategy 5: XPath structural
        candidates.extend(
            self._strategy_xpath_structural(original_by, original_value, fingerprint)
        )

        # Strategy 6: Tag + attribute combinations
        candidates.extend(
            self._strategy_tag_combinations(original_by, original_value, fingerprint)
        )

        # Deduplicate and limit
        seen = set()
        unique_candidates = []
        for c in candidates:
            key = (c.by, c.value)
            if key not in seen and key != (original_by, original_value):
                seen.add(key)
                unique_candidates.append(c)

        return unique_candidates[:max_candidates]

    def _strategy_data_attributes(
        self, original_by: str, original_value: str, fingerprint: Optional[dict]
    ) -> list[LocatorCandidate]:
        """Look for data-testid, data-cy, data-qa attributes."""
        candidates = []

        if not fingerprint or "attributes" not in fingerprint:
            return candidates

        attrs = fingerprint["attributes"]

        # data-testid is the gold standard
        for attr_name in ["data-testid", "data-test-id", "data-cy", "data-qa", "data-id"]:
            if attr_name in attrs and attrs[attr_name]:
                candidates.append(
                    LocatorCandidate(
                        by="css selector",
                        value=f'[{attr_name}="{attrs[attr_name]}"]',
                        strategy_name="data_attribute",
                        reliability_bonus=0.3,
                    )
                )

        return candidates

    def _strategy_name_attribute(
        self, original_by: str, original_value: str, fingerprint: Optional[dict]
    ) -> list[LocatorCandidate]:
        """Try the name attribute if available."""
        candidates = []

        if not fingerprint or "attributes" not in fingerprint:
            # Guess from the original value
            if original_by == "id":
                candidates.append(
                    LocatorCandidate(
                        by="name",
                        value=original_value,
                        strategy_name="name_from_id",
                        reliability_bonus=0.1,
                    )
                )
            return candidates

        attrs = fingerprint["attributes"]
        if "name" in attrs and attrs["name"]:
            candidates.append(
                LocatorCandidate(
                    by="name",
                    value=attrs["name"],
                    strategy_name="name_attribute",
                    reliability_bonus=0.2,
                )
            )

        return candidates

    def _strategy_css_class(
        self, original_by: str, original_value: str, fingerprint: Optional[dict]
    ) -> list[LocatorCandidate]:
        """Generate CSS selectors from class attributes."""
        candidates = []

        if not fingerprint:
            return candidates

        attrs = fingerprint.get("attributes", {})
        tag_name = fingerprint.get("tag_name", "*")

        if "class" in attrs and attrs["class"]:
            classes = attrs["class"].strip().split()

            # Use the most specific-looking class (longer, not utility)
            specific_classes = [
                c for c in classes
                if len(c) > 3 and not c.startswith(("mt-", "mb-", "p-", "m-", "w-", "h-"))
            ]

            if specific_classes:
                # Single most specific class
                best_class = max(specific_classes, key=len)
                candidates.append(
                    LocatorCandidate(
                        by="css selector",
                        value=f"{tag_name}.{best_class}",
                        strategy_name="css_class",
                        reliability_bonus=0.15,
                    )
                )

                # Combination of tag + multiple classes
                if len(specific_classes) >= 2:
                    class_selector = ".".join(sorted(specific_classes[:3]))
                    candidates.append(
                        LocatorCandidate(
                            by="css selector",
                            value=f"{tag_name}.{class_selector}",
                            strategy_name="css_multi_class",
                            reliability_bonus=0.2,
                        )
                    )

        return candidates

    def _strategy_text_content(
        self, original_by: str, original_value: str, fingerprint: Optional[dict]
    ) -> list[LocatorCandidate]:
        """Match elements by their visible text content."""
        candidates = []

        if not fingerprint or not fingerprint.get("text"):
            return candidates

        text = fingerprint["text"].strip()
        tag_name = fingerprint.get("tag_name", "*")

        if text and len(text) <= 50:
            # Exact text match via XPath
            escaped_text = text.replace("'", "\\'")
            candidates.append(
                LocatorCandidate(
                    by="xpath",
                    value=f"//{tag_name}[normalize-space()='{escaped_text}']",
                    strategy_name="text_exact",
                    reliability_bonus=0.15,
                )
            )

            # Contains text (more forgiving)
            if len(text) > 3:
                candidates.append(
                    LocatorCandidate(
                        by="xpath",
                        value=f"//{tag_name}[contains(text(), '{escaped_text}')]",
                        strategy_name="text_contains",
                        reliability_bonus=0.1,
                    )
                )

        return candidates

    def _strategy_xpath_structural(
        self, original_by: str, original_value: str, fingerprint: Optional[dict]
    ) -> list[LocatorCandidate]:
        """Generate XPath variations based on structure."""
        candidates = []

        if not fingerprint:
            # Pure heuristic: try common patterns based on original value
            if original_by == "id":
                # Try partial ID match
                candidates.append(
                    LocatorCandidate(
                        by="xpath",
                        value=f"//*[contains(@id, '{original_value}')]",
                        strategy_name="xpath_partial_id",
                        reliability_bonus=0.1,
                    )
                )

                # Try class containing similar name
                candidates.append(
                    LocatorCandidate(
                        by="xpath",
                        value=f"//*[contains(@class, '{original_value}')]",
                        strategy_name="xpath_class_from_id",
                        reliability_bonus=0.05,
                    )
                )
            return candidates

        tag_name = fingerprint.get("tag_name", "*")
        attrs = fingerprint.get("attributes", {})

        # aria-label based (accessibility-friendly)
        if "aria-label" in attrs and attrs["aria-label"]:
            label = attrs["aria-label"]
            candidates.append(
                LocatorCandidate(
                    by="xpath",
                    value=f"//{tag_name}[@aria-label='{label}']",
                    strategy_name="xpath_aria_label",
                    reliability_bonus=0.2,
                )
            )

        # placeholder for inputs
        if "placeholder" in attrs and attrs["placeholder"]:
            placeholder = attrs["placeholder"]
            candidates.append(
                LocatorCandidate(
                    by="xpath",
                    value=f"//{tag_name}[@placeholder='{placeholder}']",
                    strategy_name="xpath_placeholder",
                    reliability_bonus=0.2,
                )
            )

        # type + tag combo
        if "type" in attrs and attrs["type"]:
            type_val = attrs["type"]
            candidates.append(
                LocatorCandidate(
                    by="css selector",
                    value=f"{tag_name}[type='{type_val}']",
                    strategy_name="tag_type_combo",
                    reliability_bonus=0.05,
                )
            )

        return candidates

    def _strategy_tag_combinations(
        self, original_by: str, original_value: str, fingerprint: Optional[dict]
    ) -> list[LocatorCandidate]:
        """Combine tag names with various attributes for broader matching."""
        candidates = []

        if not fingerprint:
            return candidates

        tag_name = fingerprint.get("tag_name", "*")
        attrs = fingerprint.get("attributes", {})

        # role attribute
        if "role" in attrs and attrs["role"]:
            candidates.append(
                LocatorCandidate(
                    by="css selector",
                    value=f'{tag_name}[role="{attrs["role"]}"]',
                    strategy_name="tag_role",
                    reliability_bonus=0.15,
                )
            )

        # title attribute
        if "title" in attrs and attrs["title"]:
            candidates.append(
                LocatorCandidate(
                    by="css selector",
                    value=f'{tag_name}[title="{attrs["title"]}"]',
                    strategy_name="tag_title",
                    reliability_bonus=0.1,
                )
            )

        # href for links
        if "href" in attrs and attrs["href"] and tag_name == "a":
            href = attrs["href"]
            if not href.startswith("javascript:"):
                candidates.append(
                    LocatorCandidate(
                        by="css selector",
                        value=f'a[href="{href}"]',
                        strategy_name="link_href",
                        reliability_bonus=0.2,
                    )
                )

        return candidates
