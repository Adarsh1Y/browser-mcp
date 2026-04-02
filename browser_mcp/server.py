import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

try:
    from .browser import WebKitBrowser
except ImportError:
    WebKitBrowser = None

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("browser-mcp")


def get_browser():
    if WebKitBrowser is None:
        raise ImportError("WebKitGTK not available. Install with: apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1")
    return WebKitBrowser()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="navigate",
            description="Navigate to a URL and return page content",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "wait": {"type": "number", "description": "Seconds to wait after load", "default": 2}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_page_content",
            description="Get the current page HTML content",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_text",
            description="Extract visible text from the page",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="click",
            description="Click an element by CSS selector or XPath",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or XPath"},
                    "xpath": {"type": "boolean", "description": "If true, treat selector as XPath", "default": False}
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="fill",
            description="Fill an input field",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for the input"},
                    "value": {"type": "string", "description": "Value to fill"}
                },
                "required": ["selector", "value"]
            }
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to save screenshot"},
                    "full_page": {"type": "boolean", "description": "Capture full page", "default": False}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="execute_js",
            description="Execute JavaScript and return result",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "JavaScript code to execute"}
                },
                "required": ["script"]
            }
        ),
        Tool(
            name="find_elements",
            description="Find elements matching a selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector"},
                    "xpath": {"type": "boolean", "description": "If true, treat as XPath", "default": False}
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="get_cookies",
            description="Get all browser cookies",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    browser = get_browser()
    
    try:
        if name == "navigate":
            result = await asyncio.get_event_loop().run_in_executor(
                None, browser.navigate, arguments.get("url"), arguments.get("wait", 2)
            )
            return [TextContent(type="text", text=f"Navigated to {arguments['url']}\nTitle: {result['title']}\nURL: {result['url']}")]

        elif name == "get_page_content":
            result = await asyncio.get_event_loop().run_in_executor(None, browser.get_html)
            return [TextContent(type="text", text=result)]

        elif name == "get_text":
            result = await asyncio.get_event_loop().run_in_executor(None, browser.get_text)
            return [TextContent(type="text", text=result)]

        elif name == "click":
            xpath = arguments.get("xpath", False)
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: browser.click(arguments["selector"], is_xpath=xpath)
            )
            return [TextContent(type="text", text=f"Clicked: {arguments['selector']}")]

        elif name == "fill":
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: browser.fill(arguments["selector"], arguments["value"])
            )
            return [TextContent(type="text", text=f"Filled '{arguments['value']}' in {arguments['selector']}")]

        elif name == "screenshot":
            path = Path(arguments["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: browser.screenshot(str(path), arguments.get("full_page", False))
            )
            return [TextContent(type="text", text=f"Screenshot saved to {path}")]

        elif name == "execute_js":
            result = await asyncio.get_event_loop().run_in_executor(
                None, browser.execute_js, arguments["script"]
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "find_elements":
            xpath = arguments.get("xpath", False)
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: browser.find_elements(arguments["selector"], is_xpath=xpath)
            )
            return [TextContent(type="text", text=f"Found {len(result)} elements:\n" + "\n".join(result))]

        elif name == "get_cookies":
            result = await asyncio.get_event_loop().run_in_executor(None, browser.get_cookies)
            return [TextContent(type="text", text=str(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    finally:
        pass


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
