"""
Element Store — persists element fingerprints between test runs.

When an element is successfully found, its attributes (tag, text, classes,
data attributes, etc.) are stored. If the primary locator breaks in the
future, the fingerprint helps generate more accurate alternative locators.

Storage is a simple JSON file, making it easy to commit to version control.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports",
    "element_store.json",
)


class ElementStore:
    """
    Stores and retrieves element fingerprints for smarter healing.

    Fingerprint structure:
    {
        "tag_name": "button",
        "text": "Submit",
        "attributes": {
            "class": "btn btn-primary",
            "type": "submit",
            "data-testid": "submit-btn"
        }
    }
    """

    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or DEFAULT_STORE_PATH
        self._data: dict[str, dict] = {}
        self._load()

    def _make_key(self, by: str, value: str) -> str:
        """Create a unique key for a locator."""
        return f"{by}::{value}"

    def store(self, by: str, value: str, fingerprint: dict) -> None:
        """Store an element's fingerprint."""
        key = self._make_key(by, value)
        self._data[key] = fingerprint
        self._save()

    def get_fingerprint(self, by: str, value: str) -> Optional[dict]:
        """Retrieve a stored fingerprint, or None if not found."""
        key = self._make_key(by, value)
        return self._data.get(key)

    def has_fingerprint(self, by: str, value: str) -> bool:
        """Check if a fingerprint exists for the given locator."""
        key = self._make_key(by, value)
        return key in self._data

    def clear(self) -> None:
        """Clear all stored fingerprints."""
        self._data = {}
        self._save()

    @property
    def size(self) -> int:
        """Number of stored fingerprints."""
        return len(self._data)

    def _load(self) -> None:
        """Load fingerprints from disk."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r") as f:
                    self._data = json.load(f)
                logger.debug(f"Loaded {len(self._data)} fingerprints from store")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load element store: {e}")
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Persist fingerprints to disk."""
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save element store: {e}")
