"""Build a local MCP server from the SaaS remote OpenAPI spec.

The spec is fetched at startup and every OpenAPI endpoint is exposed as an MCP
tool. Tool calls are forwarded to the SaaS API with the user's bearer token.
The token is never logged and never included in error messages.
"""

from __future__ import annotations

import logging
import os

import httpx
import yaml
from fastmcp import FastMCP

try:  # FastMCP 3.x
    from fastmcp.server.providers.openapi import MCPType, RouteMap
except ImportError:  # FastMCP 2.x
    from fastmcp.server.openapi import MCPType, RouteMap

logger = logging.getLogger("posbuzz_mcp")

DEFAULT_BASE_URL = "https://pos-buzz.com"
OPENAPI_SPEC_PATH = "/api-docs/v1/openapi.yaml"
DEFAULT_MCP_NAME = "posbuzz-mcp"


def _get_token() -> str:
    token = os.environ.get("SAAS_API_KEY")
    if not token:
        raise SystemExit("SAAS_API_KEY is required")
    return token


def _fetch_spec(spec_url: str) -> dict:
    """Fetch and parse the OpenAPI spec. yaml.safe_load handles JSON too."""
    try:
        response = httpx.get(spec_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # Message names the URL but never the token.
        raise SystemExit(f"Failed to fetch OpenAPI spec from {spec_url}: {exc}") from exc

    try:
        spec = yaml.safe_load(response.text)
    except yaml.YAMLError as exc:
        raise SystemExit(f"Failed to parse OpenAPI spec from {spec_url}: {exc}") from exc

    if not isinstance(spec, dict):
        raise SystemExit(f"OpenAPI spec at {spec_url} is not a valid object")
    return spec


def build_server() -> FastMCP:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    token = _get_token()
    base_url = os.environ.get("API_BASE_URL", DEFAULT_BASE_URL)
    spec_url = base_url + OPENAPI_SPEC_PATH
    name = os.environ.get("MCP_NAME", DEFAULT_MCP_NAME)

    logger.info("Fetching OpenAPI spec from %s", spec_url)
    spec = _fetch_spec(spec_url)
    logger.info("Targeting SaaS API at %s", base_url)

    client = httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )

    return FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name=name,
        # Map every endpoint (including GETs) to an MCP tool.
        route_maps=[RouteMap(mcp_type=MCPType.TOOL)],
    )
