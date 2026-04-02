"""MCP server implementation for browser control."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    from .browser import WebKitBrowser
except ImportError:
    WebKitBrowser = None

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("browser-mcp")


def get_browser() -> "WebKitBrowser":
    """Create and return a browser instance."""
    if WebKitBrowser is None:
        raise ImportError(
            "WebKitGTK not available. Install with:\n"
            "  Ubuntu/Debian: sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1\n"
            "  Fedora: sudo dnf install webkit2gtk4.1-devel pygobject3 cairo-gobject\n"
            "  Arch: sudo pacman -S webkit2gtk4.1 python-gobject python-cairo gobject-introspection"
        )
    return WebKitBrowser()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available browser tools."""
    return [
        Tool(
            name="navigate",
            description="Navigate to a URL and return page information",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "wait": {
                        "type": "number",
                        "description": "Seconds to wait after page load",
                        "default": 2.0,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_page_content",
            description="Get the current page HTML content",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_text",
            description="Extract visible text from the page",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="click",
            description="Click an element by CSS selector or XPath",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or XPath"},
                    "xpath": {
                        "type": "boolean",
                        "description": "If true, treat selector as XPath",
                        "default": False,
                    },
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="fill",
            description="Fill an input field with text",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for the input"},
                    "value": {"type": "string", "description": "Value to fill"},
                },
                "required": ["selector", "value"],
            },
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to save screenshot"},
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full page instead of visible area",
                        "default": False,
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="execute_js",
            description="Execute JavaScript and return the result",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "JavaScript code to execute"},
                },
                "required": ["script"],
            },
        ),
        Tool(
            name="find_elements",
            description="Find all elements matching a selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or XPath"},
                    "xpath": {
                        "type": "boolean",
                        "description": "If true, treat selector as XPath",
                        "default": False,
                    },
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="get_cookies",
            description="Get all browser cookies",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="show_browser",
            description="Show the browser window",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="hide_browser",
            description="Hide the browser window",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="set_browser_size",
            description="Set the browser window size",
            inputSchema={
                "type": "object",
                "properties": {
                    "width": {"type": "integer", "description": "Window width"},
                    "height": {"type": "integer", "description": "Window height"},
                },
                "required": ["width", "height"],
            },
        ),
        Tool(
            name="console_logs",
            description="Get captured console messages (errors, warnings, logs)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="console_clear",
            description="Clear console message buffer",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="repl",
            description="Execute JavaScript and return pretty-printed result",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "JavaScript code to execute"},
                },
                "required": ["script"],
            },
        ),
        Tool(
            name="set_auto_screenshot",
            description="Enable or disable auto-screenshot on navigation",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "description": "Enable auto-screenshot"},
                },
                "required": ["enabled"],
            },
        ),
        Tool(
            name="get_last_screenshot",
            description="Get path to the last auto-screenshot",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def run_in_thread(func: Any, *args: Any) -> Any:
    """Run a blocking function in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls from the MCP client."""
    browser = get_browser()

    try:
        if name == "navigate":
            url = arguments["url"]
            wait = arguments.get("wait", 2.0)
            result = await run_in_thread(browser.navigate, url, wait)
            return [
                TextContent(
                    type="text",
                    text=f"Navigated to {url}\nTitle: {result['title']}\nURL: {result['url']}",
                )
            ]

        elif name == "get_page_content":
            result = await run_in_thread(browser.get_html)
            return [TextContent(type="text", text=result)]

        elif name == "get_text":
            result = await run_in_thread(browser.get_text)
            return [TextContent(type="text", text=result)]

        elif name == "click":
            selector = arguments["selector"]
            xpath = arguments.get("xpath", False)
            result = await run_in_thread(browser.click, selector, xpath)
            return [TextContent(type="text", text=f"Clicked: {selector}\nResult: {result}")]

        elif name == "fill":
            selector = arguments["selector"]
            value = arguments["value"]
            result = await run_in_thread(browser.fill, selector, value)
            return [
                TextContent(type="text", text=f"Filled '{value}' in {selector}\nResult: {result}")
            ]

        elif name == "screenshot":
            path = Path(arguments["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            full_page = arguments.get("full_page", False)
            result = await run_in_thread(browser.screenshot, str(path), full_page)
            return [TextContent(type="text", text=f"Screenshot saved to {result}")]

        elif name == "execute_js":
            script = arguments["script"]
            result = await run_in_thread(browser.run_javascript_sync, script)
            return [TextContent(type="text", text=str(result) if result else "null")]

        elif name == "find_elements":
            selector = arguments["selector"]
            xpath = arguments.get("xpath", False)
            elements = await run_in_thread(browser.find_elements, selector, xpath)
            if not elements:
                return [TextContent(type="text", text="No elements found")]
            return [
                TextContent(
                    type="text", text=f"Found {len(elements)} elements:\n" + "\n".join(elements)
                )
            ]

        elif name == "get_cookies":
            result = await run_in_thread(browser.get_cookies)
            return [TextContent(type="text", text=str(result))]

        elif name == "show_browser":
            browser.show()
            return [TextContent(type="text", text="Browser window shown")]

        elif name == "hide_browser":
            browser.hide()
            return [TextContent(type="text", text="Browser window hidden")]

        elif name == "set_browser_size":
            width = arguments.get("width", 1024)
            height = arguments.get("height", 768)
            browser.set_size(width, height)
            return [TextContent(type="text", text=f"Browser size set to {width}x{height}")]

        elif name == "console_logs":
            logs = await run_in_thread(browser.get_console_messages)
            if not logs:
                return [TextContent(type="text", text="No console messages")]
            formatted = []
            for log in logs:
                formatted.append(f"[{log['source']}:{log['line']}] {log['message']}")
            return [TextContent(type="text", text="\n".join(formatted))]

        elif name == "console_clear":
            await run_in_thread(browser.clear_console)
            return [TextContent(type="text", text="Console cleared")]

        elif name == "repl":
            script = arguments["script"]
            result = await run_in_thread(browser.repl, script)
            return [TextContent(type="text", text=result)]

        elif name == "set_auto_screenshot":
            enabled = arguments.get("enabled", False)
            await run_in_thread(browser.set_auto_screenshot, enabled)
            status = "enabled" if enabled else "disabled"
            return [TextContent(type="text", text=f"Auto-screenshot {status}")]

        elif name == "get_last_screenshot":
            path = await run_in_thread(browser.get_last_screenshot)
            if path:
                return [TextContent(type="text", text=f"Screenshot: {path}")]
            return [TextContent(type="text", text="No screenshot available")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {str(e)}")]


async def main() -> None:
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
