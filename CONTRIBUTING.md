# Contributing to Browser MCP

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Be patient with new contributors
- Focus on constructive feedback

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/browser-mcp`
3. Create a virtual environment
4. Install dev dependencies: `pip install -e ".[dev,webkit]"`
5. Make your changes

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=browser_mcp

# Run specific test file
pytest tests/test_browser.py
```

### Code Quality

```bash
# Lint with ruff
ruff check .

# Format code
ruff format .

# Type check
mypy browser_mcp
```

### Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: restructure code
test: add tests
chore: maintenance tasks
```

## Pull Request Process

1. Create a new branch for your feature/fix
2. Make your changes with tests
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request

## Reporting Issues

When reporting issues, include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages if applicable

## Questions?

Feel free to open an issue for questions or discussions.
