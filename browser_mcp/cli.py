"""CLI interface for browser-mcp."""

import sys
import argparse


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="browser-mcp",
        description="A lightweight browser MCP server powered by WebKitGTK",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.2.0",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    args = parser.parse_args()
    
    if args.debug:
        print("Starting browser-mcp in debug mode...", file=sys.stderr)
    
    try:
        from browser_mcp.server import main as server_main
        import asyncio
        asyncio.run(server_main())
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMake sure WebKitGTK is installed:", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo", file=sys.stderr)
        print("  Fedora: sudo dnf install webkit2gtk4.1-devel pygobject3", file=sys.stderr)
        print("  Arch: sudo pacman -S webkit2gtk4.1 python-gobject", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
