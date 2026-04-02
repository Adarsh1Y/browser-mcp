# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-04-03

### Added
- Browser singleton pattern - browser persists across MCP tool calls
- reset_browser tool - close current and create new browser instance
- close_browser tool - properly cleanup browser resources

### Fixed
- Browser no longer closes between tool calls
- Session state maintained across multiple navigations

## [0.3.0] - 2024-04-03

### Fixed
- Screenshot now captures actual page content (was returning blank)
- WebView now properly initialized with Gtk.Window for rendering

### Changed
- Browser constructor now accepts optional width/height parameters

## [0.2.0] - 2024-04-03

### Added
- Professional project structure with proper metadata
- Type hints throughout the codebase
- Comprehensive README with badges
- MIT License
- Contributing guidelines
- Example usage files
- Test infrastructure
- CI/CD with GitHub Actions

### Improved
- Better error handling
- Cleaner code organization
- WebKit2 API updates

## [0.1.0] - 2024-04-03

### Added
- Initial release
- Basic browser navigation
- Page content extraction
- Element clicking and form filling
- Screenshot capability
- JavaScript execution
- CSS/XPath element finding
- Cookie management
