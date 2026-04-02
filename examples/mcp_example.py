"""Example: Using browser-mcp with MCP protocol.

This example shows how to interact with the browser MCP server
using the MCP JSON-RPC protocol.
"""

import json
import subprocess
import sys


def send_request(request: dict) -> dict:
    """Send a JSON-RPC request to the MCP server."""
    print(f"Request: {json.dumps(request)}")
    
    result = subprocess.run(
        [sys.executable, "-m", "browser_mcp"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
    )
    
    response = result.stdout.strip()
    print(f"Response: {response}")
    
    if response:
        return json.loads(response)
    return {}


def main():
    """Run the MCP example."""
    # Initialize
    init_response = send_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "example-client",
                "version": "1.0.0",
            },
        },
    })
    
    print(f"\nInitialized: {init_response.get('result', {}).get('serverInfo', {})}")
    
    # List tools
    list_response = send_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    })
    
    tools = list_response.get("result", {}).get("tools", [])
    print(f"\nAvailable tools: {[t['name'] for t in tools]}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
