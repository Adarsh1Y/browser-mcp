"""Basic usage examples for browser-mcp.

This file demonstrates common use cases for the browser MCP server.
Run these examples to understand how to interact with web pages.
"""

from browser_mcp.browser import WebKitBrowser


def basic_navigation():
    """Navigate to a website and get basic info."""
    browser = WebKitBrowser()
    
    # Navigate to a page
    result = browser.navigate("https://example.com", wait=2)
    
    print(f"URL: {result['url']}")
    print(f"Title: {result['title']}")
    
    return browser


def extract_page_text(browser=None):
    """Extract visible text from a page."""
    if browser is None:
        browser = WebKitBrowser()
        browser.navigate("https://example.com", wait=2)
    
    text = browser.get_text()
    print("Page text:", text[:500])  # First 500 chars
    
    return text


def take_screenshot(browser=None, path="/tmp/screenshot.png"):
    """Take a screenshot of the current page."""
    if browser is None:
        browser = WebKitBrowser()
        browser.navigate("https://example.com", wait=2)
    
    browser.screenshot(path)
    print(f"Screenshot saved to {path}")


def interact_with_form():
    """Fill and submit a form."""
    browser = WebKitBrowser()
    
    # Navigate to a page with a form
    browser.navigate("https://example.com", wait=2)
    
    # Fill an input field
    browser.fill("input[type='text']", "Search query")
    
    # Click a button
    result = browser.click("button[type='submit']")
    print(f"Click result: {result}")
    
    return browser


def run_custom_javascript():
    """Execute custom JavaScript on the page."""
    browser = WebKitBrowser()
    browser.navigate("https://example.com", wait=2)
    
    # Get page title via JS
    title = browser.run_javascript_sync("document.title")
    print(f"Page title: {title}")
    
    # Get all links
    links = browser.run_javascript_sync("""
        JSON.stringify(
            [...document.querySelectorAll('a')].map(a => ({
                text: a.innerText,
                href: a.href
            }))
        )
    """)
    print(f"Links: {links}")
    
    # Count elements
    count = browser.run_javascript_sync("document.querySelectorAll('p').length")
    print(f"Paragraph count: {count}")


def find_elements():
    """Find elements by CSS selector."""
    browser = WebKitBrowser()
    browser.navigate("https://example.com", wait=2)
    
    # Find all paragraphs
    paragraphs = browser.find_elements("p")
    print(f"Found {len(paragraphs)} paragraphs")
    
    # Find by XPath
    headings = browser.find_elements("//h1", is_xpath=True)
    print(f"Found {len(headings)} headings")


if __name__ == "__main__":
    print("=" * 50)
    print("Basic Navigation")
    print("=" * 50)
    browser = basic_navigation()
    
    print("\n" + "=" * 50)
    print("Extract Page Text")
    print("=" * 50)
    extract_page_text(browser)
    
    print("\n" + "=" * 50)
    print("Find Elements")
    print("=" * 50)
    find_elements()
