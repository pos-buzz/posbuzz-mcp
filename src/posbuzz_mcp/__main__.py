"""Entry point: run the local MCP server over stdio."""

from __future__ import annotations

from .server import build_server


def main() -> None:
    # FastMCP defaults to stdio transport — no HTTP port is opened.
    build_server().run()


if __name__ == "__main__":
    main()
