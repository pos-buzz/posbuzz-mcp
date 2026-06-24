"""posbuzz-mcp: local MCP server for the PosBuzz / cosmetic-analysis SaaS API."""

from .server import build_server

__all__ = ["build_server"]
__version__ = "0.1.0"
