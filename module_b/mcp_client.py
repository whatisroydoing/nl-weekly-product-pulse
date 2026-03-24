"""
MCP Client — Shared wrapper for Model Context Protocol interactions.
Handles tool discovery, invocation, and error handling.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClientWrapper:
    """
    Wrapper around the MCP Python SDK client.
    Manages connection lifecycle and tool invocation for MCP servers.
    """

    def __init__(self, server_command: str, server_args: list[str] = None):
        """
        Initialize MCP client.

        Args:
            server_command: Command to start the MCP server (e.g., "python").
            server_args: Arguments for the server command.
        """
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args or [],
        )
        self._session = None

    async def _get_session(self) -> ClientSession:
        """Establish connection to the MCP server."""
        if self._session is None:
            transport = await stdio_client(self.server_params).__aenter__()
            read_stream, write_stream = transport
            self._session = ClientSession(read_stream, write_stream)
            await self._session.__aenter__()
            await self._session.initialize()
        return self._session

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""
        session = await self._get_session()
        result = await session.list_tools()
        return [{"name": t.name, "description": t.description} for t in result.tools]

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Invoke a tool on the MCP server.

        Args:
            tool_name: Name of the tool to invoke.
            arguments: Tool arguments as a dictionary.

        Returns:
            Tool result as a dictionary.

        Raises:
            RuntimeError: If the tool call fails.
        """
        session = await self._get_session()
        try:
            result = await session.call_tool(tool_name, arguments)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close the MCP session."""
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
