"""Run browser-mcp as a standalone server."""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
