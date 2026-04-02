"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Hello World</h1>
        <p class="intro">Welcome to the test page</p>
        <input type="text" id="search" name="q" />
        <button type="submit" class="btn">Search</button>
        <a href="https://example.com">Example Link</a>
    </body>
    </html>
    """


@pytest.fixture
def data_url(sample_html):
    """Data URL from sample HTML."""
    import base64
    encoded = base64.b64encode(sample_html.encode()).decode()
    return f"data:text/html;base64,{encoded}"
