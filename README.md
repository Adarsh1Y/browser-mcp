# 🌐 Browser MCP

> A lightweight, headless browser server for the Model Context Protocol (MCP)

[![PyPI Version](https://img.shields.io/pypi/v/browser-mcp.svg)](https://pypi.org/project/browser-mcp/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Adarsh1Y/browser-mcp?style=social)](https://github.com/Adarsh1Y/browser-mcp)

Browser MCP brings web browsing capabilities to AI assistants. Navigate pages, extract content, take screenshots, and interact with web elements - all through the MCP protocol.

## ✨ Features

- 🌐 **Navigate & Browse** - Load any URL and browse the web
- 📸 **Screenshots** - Capture full pages or visible portions
- 🔍 **Content Extraction** - Get HTML or plain text from pages
- 🖱️ **Element Interaction** - Click, fill forms, and interact
- 📜 **JavaScript Execution** - Run custom JS in the page context
- 🔧 **Find Elements** - Locate elements by CSS selector or XPath
- 🍪 **Cookie Management** - Access browser cookies

## 📦 Installation

### Quick Install

```bash
pip install browser-mcp
```

### System Dependencies

**Ubuntu / Debian:**
```bash
sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1
```

**Fedora:**
```bash
sudo dnf install webkit2gtk4.1-devel pygobject3 cairo-gobject
```

**Arch Linux:**
```bash
sudo pacman -S webkit2gtk4.1 python-gobject python-cairo gobject-introspection
```

**macOS:**
```bash
brew install webkitgtk4.1 gobject-introspection pygobject3 py3cairo
```

## 🚀 Usage

### CLI

```bash
# Run directly
python -m browser_mcp

# Or install and run
pip install browser-mcp
browser-mcp
```

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "browser": {
      "command": "python",
      "args": ["-m", "browser_mcp"]
    }
  }
}
```

### With n8n

```javascript
// In your n8n MCP node configuration
{
  "command": "python",
  "args": ["-m", "browser_mcp"]
}
```

## 🛠️ Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `navigate` | Navigate to a URL | `url`, `wait` (optional) |
| `get_page_content` | Get page HTML | - |
| `get_text` | Extract visible text | - |
| `click` | Click an element | `selector`, `xpath` (optional) |
| `fill` | Fill an input | `selector`, `value` |
| `screenshot` | Take a screenshot | `path`, `full_page` (optional) |
| `execute_js` | Run JavaScript | `script` |
| `find_elements` | Find elements | `selector`, `xpath` (optional) |
| `get_cookies` | Get cookies | - |

## 💡 Examples

### Basic Navigation

```python
# Navigate to a page
{"name": "navigate", "arguments": {"url": "https://example.com"}}

# Get the page text
{"name": "get_text", "arguments": {}}
```

### Form Interaction

```python
# Fill a search box and search
{"name": "fill", "arguments": {"selector": "input[name='q']", "value": "search query"}}
{"name": "click", "arguments": {"selector": "button[type='submit']"}}
```

### Screenshot

```python
# Take a screenshot
{"name": "screenshot", "arguments": {"path": "/tmp/page.png"}}
```

### Custom JavaScript

```python
# Extract specific data with JS
{"name": "execute_js", "arguments": {"script": "document.title"}}
{"name": "execute_js", "arguments": {"script": "[...document.querySelectorAll('a')].map(a => a.href)"}}
```

## 🔧 Development

```bash
# Clone the repo
git clone https://github.com/Adarsh1Y/browser-mcp
cd browser-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with dev dependencies
pip install -e ".[dev,webkit]"

# Run tests
pytest

# Lint
ruff check .

# Type check
mypy browser_mcp
```

## 📁 Project Structure

```
browser-mcp/
├── browser_mcp/
│   ├── __init__.py       # Package init
│   ├── __main__.py       # Entry point
│   ├── browser.py        # WebKit browser wrapper
│   ├── server.py         # MCP server implementation
│   └── cli.py            # CLI interface
├── tests/
│   └── test_browser.py   # Unit tests
├── examples/
│   └── basic_usage.py    # Usage examples
├── pyproject.toml        # Project config
├── README.md
├── LICENSE
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## 🐛 Troubleshooting

### "WebKitGTK not available"

Make sure system dependencies are installed:
```bash
sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1
```

### Headless environment issues

WebKitGTK requires a display. In headless environments, use Xvfb:
```bash
xvfb-run python -m browser_mcp
```

### Permission denied on screenshot

Ensure the target directory is writable:
```bash
chmod 755 /tmp
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## ⭐ Show Your Support

Give a ⭐ if this project helped you!

[![GitHub stars](https://img.shields.io/github/stars/Adarsh1Y/browser-mcp?style=social)](https://github.com/Adarsh1Y/browser-mcp)

---

## 🇮🇳 हिंदी (Hindi)

🌐 **Browser MCP** एक हल्का, हेडलेस ब्राउज़र सर्वर है जो मॉडल कॉन्टेक्स्ट प्रोटोकॉल (MCP) के लिए वेब ब्राउज़िंग क्षमताएं लाता है।

### ✨ विशेषताएं

- 🌐 **नेविगेट और ब्राउज़ करें** - कोई भी URL लोड करें
- 📸 **स्क्रीनशॉट** - पूरे पेज या दृश्य भाग कैप्चर करें
- 🔍 **सामग्री निष्कर्षण** - HTML या प्लेन टेक्स्ट प्राप्त करें
- 🖱️ **एलिमेंट इंटरैक्शन** - क्लिक, फॉर्म भरें
- 📜 **जावास्क्रिप्ट एक्जीक्यूशन** - कस्टम JS चलाएं
- 🔧 **एलिमेंट खोजें** - CSS selector या XPath से एलिमेंट खोजें

### 📦 इंस्टॉलेशन

```bash
pip install browser-mcp
```

### 🚀 उपयोग

```bash
python -m browser_mcp
```

### 🛠️ उपलब्ध टूल्स

| टूल | विवरण |
|-----|--------|
| `navigate` | URL पर जाएं |
| `screenshot` | स्क्रीनशॉट लें |
| `get_text` | टेक्स्ट निकालें |
| `click` | एलिमेंट पर क्लिक करें |
| `fill` | इनपुट भरें |
| `execute_js` | जावास्क्रिप्ट चलाएं |

### 💡 उदाहरण

```python
# Google पर जाएं
{"name": "navigate", "arguments": {"url": "https://google.com"}}

# स्क्रीनशॉट लें
{"name": "screenshot", "arguments": {"path": "/tmp/screenshot.png"}}
```

---

Made with ❤️ for the AI community
