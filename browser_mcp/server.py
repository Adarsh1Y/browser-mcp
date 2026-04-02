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
    """List all available browser tools. 🌍"""
    return [
        Tool(
            name="navigate",
            description="🌐 Navigate to a URL and return page information\n🔗 किसी URL पर जाएं और पेज जानकारी प्राप्त करें",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "🌍 URL to navigate to / जाने के लिए URL"},
                    "wait": {
                        "type": "number",
                        "description": "⏱️ Seconds to wait after page load / पेज लोड होने के बाद इंतजार सेकंड",
                        "default": 2.0,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_page_content",
            description="📄 Get the current page HTML content\n🌍 वर्तमान पेज का HTML कंटेंट प्राप्त करें",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_text",
            description="📝 Extract visible text from the page\n🔤 पेज से दिखाई देने वाला टेक्स्ट निकालें",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="click",
            description="🖱️ Click an element by CSS selector or XPath\n👆 CSS selector या XPath से एलिमेंट पर क्लिक करें",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "🎯 CSS selector or XPath / CSS selector या XPath"},
                    "xpath": {
                        "type": "boolean",
                        "description": "☑️ If true, treat selector as XPath / अगर true है, तो selector को XPath मानें",
                        "default": False,
                    },
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="fill",
            description="✍️ Fill an input field with text\n📝 इनपुट फील्ड में टेक्स्ट भरें",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "🎯 CSS selector for the input / इनपुट के लिए CSS selector"},
                    "value": {"type": "string", "description": "📃 Value to fill / भरने के लिए मान"},
                },
                "required": ["selector", "value"],
            },
        ),
        Tool(
            name="screenshot",
            description="📸 Take a screenshot of the current page\n🖼️ वर्तमान पेज का स्क्रीनशॉट लें",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "💾 Path to save screenshot / स्क्रीनशॉट सेव करने का पाथ"},
                    "full_page": {
                        "type": "boolean",
                        "description": "📜 Capture full page instead of visible area / दृश्य क्षेत्र के बजाय पूरा पेज कैप्चर करें",
                        "default": False,
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="execute_js",
            description="📜 Execute JavaScript and return the result\n⚡ JavaScript चलाएं और परिणाम प्राप्त करें",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "💻 JavaScript code to execute / चलाने के लिए JavaScript कोड"},
                },
                "required": ["script"],
            },
        ),
        Tool(
            name="find_elements",
            description="🔍 Find all elements matching a selector\n🔎 CSS selector या XPath से मिलने वाले सभी एलिमेंट खोजें",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "🎯 CSS selector or XPath / CSS selector या XPath"},
                    "xpath": {
                        "type": "boolean",
                        "description": "☑️ If true, treat selector as XPath / अगर true है, तो selector को XPath मानें",
                        "default": False,
                    },
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="get_cookies",
            description="🍪 Get all browser cookies\n🍪 सभी ब्राउज़र कुकीज़ प्राप्त करें",
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
