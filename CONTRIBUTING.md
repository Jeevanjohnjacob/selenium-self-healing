# Contributing to Selenium Self-Healing

Thanks for your interest in contributing! Here's how you can help.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/selenium-self-healing.git`
3. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest tests/ -v`

## Ways to Contribute

### 🐛 Bug Reports
Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python/Selenium/browser version

### 💡 New Locator Strategies
The most impactful way to contribute! Add a new strategy to `self_healing/locator_strategies.py`:

1. Create a method `_strategy_your_name(...)`
2. Return a list of `LocatorCandidate` objects
3. Register it in `generate_alternatives()`
4. Add tests in `tests/test_strategies.py`

### 🧪 Tests
- Unit tests go in `tests/`
- Use mocks for WebDriver interactions in unit tests
- Integration tests requiring a browser should be marked with `@pytest.mark.integration`

### 📖 Documentation
- Improve README examples
- Add docstrings to functions
- Create tutorials or blog posts

## Code Style

- Follow PEP 8
- Use type hints for function signatures
- Write docstrings for all public methods
- Keep functions focused and small

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/my-improvement`
2. Make your changes
3. Add/update tests
4. Run `pytest tests/ -v` and ensure all pass
5. Submit a PR with a clear description

## Ideas for Future Work

- **ML-based healing**: Use historical healing data to predict the best fallback
- **Visual locators**: Use image recognition to find elements visually
- **Shadow DOM support**: Heal elements inside Shadow DOM
- **iframe handling**: Auto-switch to correct iframe when element not found
- **Parallel healing**: Try multiple strategies concurrently
- **Reporting dashboard**: Web-based dashboard for healing analytics
