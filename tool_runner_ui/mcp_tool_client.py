import asyncio
import json
from abc import abstractmethod
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from langchain_core.tools import BaseTool, ArgsSchema
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.types import Tool

from llm_chat_agent import ToolConfig, LLMChatAgent
from logger import Logger
from models import Models


class MCPToolClient(Logger):

    def __init__(self, server_url: str):
        self.name = 'MCP client'
        self.color = Logger.BRIGHT_YELLOW
        self.server_url = server_url
        self.session: ClientSession = None
        self.tools: Dict[str, Any] = {}
        self.toolkit: Dict[str, ToolConfig] = {}

    @abstractmethod
    def _mcp_client(self):
        """Return appropriate MCP client - must be implemented by subclasses"""
        pass

    async def connect(self):
        """Connect to MCP server via HTTP SSE"""
        try:
            # Create SSE client connection
            async with self._mcp_client() as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session

                    # Initialize the session
                    await session.initialize()

                    # List available tools
                    tools_result = await session.list_tools()
                    self.tools = {tool.name: self._convert_to_langchain_tool(tool) for tool in tools_result.tools}
                    self.toolkit = self._create_toolkit()

                    self.log("Connected to MCP server. Available tools: {tools}", tools=list(self.tools.keys()))

        except KeyError as e:
            self.log("Failed to connect to MCP server: {message}", message=e)
            raise

    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        if not self.session:
            await self.connect()
        return list(self.tools.keys())
        # Convert MCP tools to ToolConfig format

    async def get_toolkit(self):
        if not self.session:
            await self.connect()
        return self.toolkit

    def _create_toolkit(self):
        return {name: ToolConfig(callable_tool=tool, direct_response=False, auto_exec=False, is_mcp_tool=True)
                for name, tool in self.tools.items()}

    async def call_tool(self, tool_name: str, **arguments: Any) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        # if not self.session:
        #     await self.connect()

        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available. Available tools: {list(self.tools.keys())}")

        """Connect to MCP server via HTTP SSE"""
        # Create MCP client connection
        async with self._mcp_client() as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the session
                await session.initialize()

                result = await self.session.call_tool(tool_name, arguments)
                self.log("=" * 60)
                self.log("MCP tool call result:\n {result}", result=result)
                self.log("=" * 60)

        if result and hasattr(result, 'content'):
            try:
                content = result.content[0].text
            except AttributeError as e:
                content = result.content

            return {
                "success": True,
                "result": content,
                "tool_name": tool_name
            }

        else:
            return {
                "success": False,
                "error": "No content",
                "tool_name": tool_name
            }

    def _convert_to_langchain_tool(self, mcp_tool: Tool) -> BaseTool:
        """Convert an MCP tool to LangChain's tool format.
        Args:
            mcp_tool: The MCP tool to convert.
            connector: The connector that provides this tool.

        Returns:
            A LangChain BaseTool.
        """

        # This is a dynamic class creation, we need to work with the self reference
        adapter_self: MCPToolClient = self

        class McpToLangChainAdapter(BaseTool):
            name: str = mcp_tool.name or "NO NAME"
            description: str = mcp_tool.description or ""
            args_schema: Optional[ArgsSchema] = mcp_tool.inputSchema
            handle_tool_error: bool = True

            def __repr__(self) -> str:
                return f"MCP tool: {self.name}: {self.description}"

            def _run(self, **kwargs: Any) -> Any:
                return asyncio.run(self._arun(**kwargs))

            async def _arun(self, **kwargs: Any) -> Any:
                """Asynchronously execute the tool with given arguments.
                Args:
                    kwargs: The arguments to pass to the tool.
                Returns:
                    The result of the tool execution.
                Raises:
                    ToolException: If tool execution fails.
                """
                print(f"running: mcp_client.call_tool({self.name}({kwargs}))")
                tool_response = await adapter_self.call_tool(self.name, **kwargs)
                return tool_response['result'], tool_response

        return McpToLangChainAdapter()


class MCPToolSSEClient(MCPToolClient):
    """MCP Tool Client for HTTP SSE connections"""

    def __init__(self, server_url: str):
        super().__init__('MCP SSE client')
        self.server_url = server_url
        self.log("Initialized SSE client for {url}", url=server_url)

    def _mcp_client(self):
        """Return SSE client"""
        return sse_client(
            self.server_url,
            headers={
                "MCP-Protocol-Version": "2024-11-05",
                "Accept": "text/event-stream"
            }
        )


class MCPToolSTDIOClient(MCPToolClient):
    """MCP Tool Client for stdio connections"""

    def __init__(self, server_config_json: str):
        super().__init__('MCP stdio client')
        self.server_config_json: str = server_config_json
        self.server_params: StdioServerParameters = self._parse_server_config(server_config_json)
        self.log("Initialized stdio client for {command}", command=self.server_params.command)

    def _parse_server_config(self, config_json: str) -> StdioServerParameters:
        """Parse JSON string to StdioServerParameters"""
        try:
            config_dict = json.loads(config_json)

            # Extract required and optional parameters
            command = config_dict.get('command')
            if not command:
                raise ValueError("'command' is required in server configuration")

            args = config_dict.get('args', [])
            env = config_dict.get('env', None)
            cwd = config_dict.get('cwd', None)
            encoding = config_dict.get('encoding', 'utf-8')
            encoding_error_handler = config_dict.get('encoding_error_handler', 'strict')

            # Validate encoding_error_handler
            if encoding_error_handler not in ['strict', 'ignore', 'replace']:
                raise ValueError(f"Invalid encoding_error_handler: {encoding_error_handler}")

            return StdioServerParameters(
                command=command,
                args=args,
                env=env,
                cwd=cwd,
                encoding=encoding,
                encoding_error_handler=encoding_error_handler
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON configuration: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing server configuration: {e}")

    def _mcp_client(self):
        """Return stdio client"""
        return stdio_client(self.server_params)

    @classmethod
    def from_command(cls, command: str, args: List[str] = None, env: Dict[str, str] = None,
                     cwd: str = None, encoding: str = 'utf-8', encoding_error_handler: str = 'strict'):
        """Create stdio client from individual parameters"""
        config = {
            'command': command,
            'args': args or [],
            'env': env,
            'cwd': cwd,
            'encoding': encoding,
            'encoding_error_handler': encoding_error_handler
        }
        return cls(json.dumps(config))

    @classmethod
    def from_json(cls, json_config: str, server_name: str = None):
        """
        Create stdio client from MCP JSON configuration format

        Args:
            json_config: JSON string containing mcpServers configuration
            server_name: Optional server name to select from mcpServers.
                        If None, uses the first server found.

        Example JSON formats:

        Example 1 (financial-datasets):
        {
          "mcpServers": {
            "financial-datasets": {
              "command": "/path/to/uv",
              "args": [
                "--directory",
                "/absolute/path/to/financial-datasets-mcp",
                "run",
                "server.py"
              ]
            }
          }
        }

        Example 2 (github with environment):
        {
          "mcpServers": {
            "github": {
              "command": "docker",
              "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server"
              ],
              "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
              }
            }
          }
        }
        """
        try:
            config_dict = json.loads(json_config)

            # Validate structure
            if 'mcpServers' not in config_dict:
                raise ValueError("JSON must contain 'mcpServers' key")

            mcp_servers = config_dict['mcpServers']

            if not isinstance(mcp_servers, dict):
                raise ValueError("'mcpServers' must be a dictionary")

            if not mcp_servers:
                raise ValueError("'mcpServers' cannot be empty")

            # Select server
            if server_name:
                if server_name not in mcp_servers:
                    available_servers = list(mcp_servers.keys())
                    raise ValueError(f"Server '{server_name}' not found. Available servers: {available_servers}")
                selected_server_config = mcp_servers[server_name]
                selected_name = server_name
            else:
                # Use first server if no name specified
                selected_name = next(iter(mcp_servers))
                selected_server_config = mcp_servers[selected_name]

            # Validate server configuration
            if not isinstance(selected_server_config, dict):
                raise ValueError(f"Server configuration for '{selected_name}' must be a dictionary")

            if 'command' not in selected_server_config:
                raise ValueError(f"Server '{selected_name}' must have a 'command' field")

            # Extract configuration
            command = selected_server_config['command']
            args = selected_server_config.get('args', [])
            env = selected_server_config.get('env', None)
            cwd = selected_server_config.get('cwd', None)
            encoding = selected_server_config.get('encoding', 'utf-8')
            encoding_error_handler = selected_server_config.get('encoding_error_handler', 'strict')

            # Create simplified configuration
            simple_config = {
                'command': command,
                'args': args,
                'env': env,
                'cwd': cwd,
                'encoding': encoding,
                'encoding_error_handler': encoding_error_handler
            }

            # Create instance
            instance = cls(json.dumps(simple_config))
            instance.name = f'MCP stdio client ({selected_name})'
            instance.log("Created from JSON config for server: {server}", server=selected_name)

            return instance

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing MCP JSON configuration: {e}")


class MCPClientFactory:
    """Factory class for creating MCP clients based on input string format"""

    @staticmethod
    def create_from(input_string: str) -> MCPToolClient:
        """
        Create appropriate MCP client based on input string format

        Args:
            input_string: Either a URL for SSE client or JSON string for stdio client
            server_name: Optional server name for JSON configs with multiple servers

        Returns:
            MCPToolSSEClient for URLs, MCPToolSTDIOClient for JSON strings

        Raises:
            ValueError: If input string format is not recognized

        Examples:
            # Create SSE client
            client = MCPClientFactory.create("http://localhost:8080/sse")

            # Create stdio client from simple JSON
            json_config = '{"command": "python", "args": ["server.py"]}'
            client = MCPClientFactory.create(json_config)

            # Create stdio client from MCP JSON format
            mcp_config = '''
            {
              "mcpServers": {
                "github": {
                  "command": "docker",
                  "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"]
                }
              }
            }
            '''
            client = MCPClientFactory.create(mcp_config, "github")
        """

        if not input_string or not isinstance(input_string, str):
            raise ValueError("Input string must be a non-empty string")

        input_string = input_string.strip()

        # Check if it's a URL
        if MCPClientFactory._is_url(input_string):
            return MCPToolSSEClient(input_string)

        # Check if it's JSON for MCP server config
        if MCPClientFactory._is_mcp_config(input_string):
            return MCPToolSTDIOClient(input_string)

        # If neither URL nor JSON, raise error
        raise ValueError(
            "Input string must be either a URL (for SSE client) or JSON (for stdio client). "
            f"Received: {input_string[:100]}{'...' if len(input_string) > 100 else ''}"
        )

    @staticmethod
    def _is_url(string: str) -> bool:
        """Check if string is a valid URL"""
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False

    @staticmethod
    def _is_mcp_config(json_string: str) -> bool:
        """Check if JSON string is in MCP configuration format"""
        try:
            config = json.loads(json_string)
            return isinstance(config, dict) and 'command' in config
        except json.JSONDecodeError:
            return False

    @classmethod
    def create_sse_client(cls, url: str) -> MCPToolSSEClient:
        """Explicitly create an SSE client"""
        if not cls._is_url(url):
            raise ValueError(f"Invalid URL: {url}")
        return MCPToolSSEClient(url)

    @classmethod
    def create_stdio_client(cls, json_config: str, server_name: str = None) -> MCPToolSTDIOClient:
        """Explicitly create a stdio client"""
        if not cls._is_mcp_config(json_config):
            raise ValueError(f"Invalid JSON configuration: {json_config}")
        return MCPToolSTDIOClient(json_config)


if __name__ == "__main__":

    #mcp_client = MCPToolClient("http://localhost:8080/sse")

    #stdio client with JSON string
    config_json = json.dumps({
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "data/test-hr.db"],
        "env": {"DEBUG": "1"},
        "encoding": "utf-8"
    })
    # config_json = json.dumps({
    #     'command': 'npx',
    #     'args': ['-y', "@modelcontextprotocol/server-brave-search"],
    #     'env': {'BRAVE_API_KEY': '1'}
    # })

    mcp_client = MCPToolSTDIOClient(config_json)

    #mcp_client = MCPToolSSEClient("http://localhost:8080/sse")

    toolkit = asyncio.run(mcp_client.get_toolkit())

    print(toolkit)

    chat_model = Models.create_chat(Models.QWEN3_8B, base_url='http://192.168.68.116:11434')

    agent = LLMChatAgent("User Assistant Agent", Logger.BLUE, chat_model, toolkit=toolkit)

    response = agent.invoke("3 most expensive products")

    print(response)
