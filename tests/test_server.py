"""Tests for the MCP server tools."""

import pytest
from unittest.mock import MagicMock, patch


class TestListTools:
    """Tests for the list_tools function."""

    @pytest.mark.asyncio
    async def test_returns_list(self):
        """list_tools should return a list."""
        from browser_mcp.server import list_tools
        result = await list_tools()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_has_expected_tools(self):
        """list_tools should include expected browser tools."""
        from browser_mcp.server import list_tools
        result = await list_tools()
        tool_names = [tool.name for tool in result]
        
        expected_tools = [
            "navigate",
            "get_page_content",
            "get_text",
            "click",
            "fill",
            "screenshot",
            "execute_js",
            "find_elements",
            "get_cookies",
        ]
        
        for tool in expected_tools:
            assert tool in tool_names


class TestCallTool:
    """Tests for the call_tool function."""

    @pytest.mark.asyncio
    async def test_navigate(self):
        """Navigate tool should work."""
        from browser_mcp.server import call_tool
        
        with patch("browser_mcp.server.get_browser") as mock_get:
            mock_browser = MagicMock()
            mock_browser.navigate.return_value = {"url": "https://example.com", "title": "Example"}
            mock_get.return_value = mock_browser
            
            result = await call_tool("navigate", {"url": "https://example.com"})
            
            assert len(result) == 1
            assert "example.com" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Unknown tool should return error message."""
        from browser_mcp.server import call_tool
        
        with patch("browser_mcp.server.get_browser"):
            result = await call_tool("unknown_tool", {})
            
            assert len(result) == 1
            assert "Unknown tool" in result[0].text
