from setuptools import setup, find_packages

setup(
    name="selenium-self-healing",
    version="1.0.0",
    description="A self-healing Selenium test framework that auto-recovers from broken locators",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/selenium-self-healing",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "selenium>=4.10.0",
        "webdriver-manager>=4.0.0",
        "jinja2>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
    ],
)
