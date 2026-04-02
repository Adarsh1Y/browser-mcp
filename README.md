# Browser MCP

Lightweight browser MCP server using WebKitGTK.

## Features

- Navigate to URLs
- Extract page content (HTML/text)
- Click elements
- Fill forms
- Take screenshots
- Execute JavaScript
- Find elements

## Install Dependencies

```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1

# Fedora
sudo dnf install webkit2gtk4.1-devel pygobject3 cairo-gobject

# macOS
brew install pygobject3 webkitgtk@4.1
```

## Install Package

```bash
pip install -e .
```

## Usage

```bash
# Run as MCP server
python -m browser_mcp

# Or use with Claude CLI
claude mcp add browser python -m browser_mcp
```

## Available Tools

| Tool | Description |
|------|-------------|
| `navigate` | Navigate to URL |
| `get_page_content` | Get HTML |
| `get_text` | Get visible text |
| `click` | Click element |
| `fill` | Fill input field |
| `screenshot` | Take screenshot |
| `execute_js` | Run JavaScript |
| `find_elements` | Find matching elements |
| `get_cookies` | Get browser cookies |

## Example

```python
# MCP tool calls
{"name": "navigate", "arguments": {"url": "https://example.com"}}
{"name": "get_text", "arguments": {}}
{"name": "click", "arguments": {"selector": "button.submit"}}
```
