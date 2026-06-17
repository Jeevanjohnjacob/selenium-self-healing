# 🩺 Selenium Self-Healing Test Framework

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green.svg)](https://selenium.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A smart Selenium test framework that **automatically recovers from broken locators**. When an element can't be found using the primary locator, the framework intelligently falls back through alternative strategies — and logs healing suggestions so you can update your tests.

## 🤔 The Problem

Selenium tests are **fragile**. A developer changes a button's ID or restructures the DOM, and suddenly your entire test suite is red. Teams spend hours fixing broken locators instead of writing new tests.

## 💡 The Solution

This framework wraps Selenium's element-finding logic with a self-healing layer that:

1. **Tries the primary locator** (your original selector)
2. **Falls back to alternatives** if it fails — using multiple strategies:
   - Attribute-based matching (name, class, data-* attributes)
   - Text content matching
   - XPath axis navigation (parent/sibling/child relationships)
   - CSS selector variations
   - Visual similarity (tag + position heuristics)
3. **Logs a healing report** showing what broke and what worked
4. **Suggests fixes** so you can update your locators permanently

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/selenium-self-healing.git
cd selenium-self-healing
pip install -r requirements.txt
```

### Basic Usage

```python
from self_healing import SelfHealingDriver

# Create a self-healing driver (wraps regular Selenium WebDriver)
driver = SelfHealingDriver(browser="chrome")

# Use it exactly like normal Selenium
driver.get("https://example.com")

# If this ID breaks, the framework auto-heals
button = driver.find_element("id", "submit-btn")
button.click()

# View the healing report
driver.print_healing_report()
driver.quit()
```

### Run Demo

```bash
python examples/demo.py
```

### Run Tests

```bash
pytest tests/ -v
```

## 🏗️ Architecture

```
selenium-self-healing/
├── self_healing/
│   ├── __init__.py
│   ├── driver.py              # SelfHealingDriver - main entry point
│   ├── locator_strategies.py  # Alternative locator generation
│   ├── healer.py             # Core healing logic & decision engine
│   ├── element_store.py      # Stores element fingerprints for learning
│   └── reporter.py           # Healing reports & fix suggestions
├── examples/
│   ├── demo.py               # Quick demo script
│   └── sample_test.py        # Example test using the framework
├── tests/
│   ├── test_healer.py        # Unit tests for healing logic
│   └── test_strategies.py    # Unit tests for locator strategies
├── reports/                   # Generated healing reports (gitignored)
├── requirements.txt
├── setup.py
└── README.md
```

## 🔧 How Self-Healing Works

```
find_element("id", "old-btn-id")
        │
        ▼
┌─── Try Primary Locator ───┐
│   Found? → Return element  │
│   Failed? → Continue ↓     │
└────────────────────────────┘
        │
        ▼
┌─── Check Element Store ───┐
│   Have we seen this        │
│   element before?          │
│   Yes → Use fingerprint    │
│   No → Generate fallbacks  │
└────────────────────────────┘
        │
        ▼
┌─── Try Alternative Locators ─┐
│  1. By attributes (name,     │
│     class, data-testid)      │
│  2. By text content          │
│  3. By XPath variations      │
│  4. By CSS variations        │
│  5. By tag + position        │
│  Found? → Return + Log heal  │
│  All failed? → Raise error   │
└──────────────────────────────┘
        │
        ▼
┌─── Log & Report ──────────┐
│  • What locator broke      │
│  • What alternative worked │
│  • Suggested permanent fix │
└────────────────────────────┘
```

## 📊 Healing Report Example

After a test run, you get a report like:

```
╔══════════════════════════════════════════════════════════╗
║              SELF-HEALING REPORT                        ║
╠══════════════════════════════════════════════════════════╣
║ Total find_element calls:  47                          ║
║ Successful (primary):      42                          ║
║ Healed (fallback):          4                          ║
║ Failed (unrecoverable):     1                          ║
║ Healing rate:             80% of failures recovered    ║
╠══════════════════════════════════════════════════════════╣
║                                                        ║
║ HEALED ELEMENTS:                                       ║
║ ┌────────────────────────────────────────────────────┐ ║
║ │ ❌ id="submit-btn" (NOT FOUND)                     │ ║
║ │ ✅ Healed via: css="button.btn-primary"            │ ║
║ │ 💡 Suggestion: Update locator to                   │ ║
║ │    css_selector: "button.btn-primary"              │ ║
║ └────────────────────────────────────────────────────┘ ║
╚══════════════════════════════════════════════════════════╝
```

## ⚙️ Configuration

```python
from self_healing import SelfHealingDriver, HealingConfig

config = HealingConfig(
    max_fallback_attempts=5,      # Max alternative locators to try
    similarity_threshold=0.7,     # Min confidence to accept a heal
    store_fingerprints=True,      # Learn element patterns over time
    report_format="html",         # "html", "json", or "console"
    healing_enabled=True,         # Toggle healing on/off
)

driver = SelfHealingDriver(browser="chrome", config=config)
```

## 🤝 Contributing

Contributions are welcome! Here are ways you can help:

- Add new locator strategies
- Improve the similarity scoring algorithm
- Add support for more browsers
- Build a dashboard for healing reports
- Add machine learning for smarter fallback selection

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## ⭐ Star This Repo

If you find this useful, give it a star! It helps others discover the project.
