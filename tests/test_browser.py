"""Tests for browser-mcp."""

import pytest

from browser_mcp import __version__


class TestVersion:
    """Test version information."""

    def test_version_exists(self):
        """Version should be defined."""
        assert __version__ is not None

    def test_version_format(self):
        """Version should be in semver format."""
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


class TestBrowserImport:
    """Test browser import and availability."""

    def test_browser_import(self):
        """Browser module should be importable."""
        try:
            from browser_mcp.browser import WebKitBrowser
            assert WebKitBrowser is not None
        except ImportError:
            pytest.skip("WebKitGTK not available")

    def test_browser_creation(self):
        """Browser instance should be creatable."""
        try:
            from browser_mcp.browser import WebKitBrowser
            browser = WebKitBrowser()
            assert browser is not None
            assert browser.view is not None
        except ImportError:
            pytest.skip("WebKitGTK not available")


class TestServerImport:
    """Test server module."""

    def test_server_import(self):
        """Server should be importable."""
        from browser_mcp import server
        assert server is not None

    def test_server_has_tools(self):
        """Server should have list_tools function."""
        from browser_mcp.server import list_tools
        assert callable(list_tools)


class TestCLI:
    """Test CLI interface."""

    def test_cli_import(self):
        """CLI should be importable."""
        from browser_mcp import cli
        assert cli is not None

    def test_main_is_callable(self):
        """Main should be callable."""
        from browser_mcp.cli import main
        assert callable(main)
