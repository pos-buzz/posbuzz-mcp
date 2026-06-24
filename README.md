# posbuzz-mcp

A **local MCP server** that exposes the PosBuzz / cosmetic-analysis SaaS API
(Social Analytics API v1) as MCP tools, so you can call it from MCP clients like
**Claude Code**, **Codex**, and Claude Desktop.

It works by fetching the SaaS OpenAPI spec at startup, turning every endpoint into
an MCP tool, and forwarding tool calls to the SaaS API using your bearer token.

> **This is a local, stdio MCP server — not a remote/hosted MCP.**
> It runs as a local process on your machine, talks to the client over standard
> input/output, opens no HTTP port, and exposes no public endpoint. Your API key
> stays on your machine.

## Requirements

- Python **3.11+**
- A SaaS API key
- (Optional) [`uv`](https://docs.astral.sh/uv/) for the simplest setup

## Get a SaaS API key

In the web app, go to **Settings → Developer API** and issue a key. The token
looks like `sa_...`. Keep it secret — treat it like a password.

## Install

### Using uv (recommended)

```bash
git clone <this-repo-url> posbuzz-mcp
cd posbuzz-mcp
uv run posbuzz-mcp   # creates the env and runs the server (stdio)
```

You can also run it without cloning into your working dir using `--directory`, or
build a one-shot command with `uvx --from . posbuzz-mcp`.

### Using pip

```bash
git clone <this-repo-url> posbuzz-mcp
cd posbuzz-mcp
pip install .
posbuzz-mcp           # console script
# or:
python -m posbuzz_mcp
```

## Configuration

Set configuration via environment variables.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SAAS_API_KEY` | yes | — | SaaS API bearer token (`sa_...`) |
| `API_BASE_URL` | no | `http://localhost:3000` | SaaS API base URL |
| `OPENAPI_SPEC_URL` | no | `http://localhost:3000/api-docs/v1/openapi.yaml` | OpenAPI spec URL (YAML or JSON) |
| `MCP_NAME` | no | `posbuzz-mcp` | MCP server name shown to the client |
| `LOG_LEVEL` | no | `INFO` | Logging level (e.g. `DEBUG`) |

Copy `.env.example` to `.env` for local reference (the `.env` file is gitignored
and is **not** read automatically — pass values via your MCP client's `env`).

## Connect from an MCP client

The server is launched by the client as a local command, communicating over stdio.
Provide the launch `command`, `args`, and `env` (with your API key).

### Claude Code

```bash
claude mcp add posbuzz \
  --env SAAS_API_KEY=sa_your_api_key \
  -- uv run --directory /absolute/path/to/posbuzz-mcp posbuzz-mcp
```

Or, if you installed with pip (console script on PATH):

```bash
claude mcp add posbuzz --env SAAS_API_KEY=sa_your_api_key -- posbuzz-mcp
```

### Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.posbuzz]
command = "uv"
args = ["run", "--directory", "/absolute/path/to/posbuzz-mcp", "posbuzz-mcp"]
env = { SAAS_API_KEY = "sa_your_api_key" }
```

### Generic MCP client (JSON)

```json
{
  "mcpServers": {
    "posbuzz": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/posbuzz-mcp", "posbuzz-mcp"],
      "env": {
        "SAAS_API_KEY": "sa_your_api_key"
      }
    }
  }
}
```

With a pip install, use `"command": "posbuzz-mcp"` (or `"python"` with
`"args": ["-m", "posbuzz_mcp"]`) and drop the `uv` args.

After editing the config, **restart your MCP client**.

## How it works

- The OpenAPI spec is fetched **at startup** from `OPENAPI_SPEC_URL`.
- Spec changes take effect only after you **restart the server** (restart the MCP
  client, or restart the process). There is no live watching or regeneration.
- The available tools are derived entirely from the SaaS OpenAPI spec. As the SaaS
  API evolves, the tools change accordingly.

### Available tools

The available tools are generated from the SaaS OpenAPI spec at startup, so they
always match the current API. For the full list of endpoints and their parameters,
see the **API Doc**.

### Destructive / write operations

Some tools map to write operations (e.g. `POST` endpoints), and some of these may
consume quota. Refer to the API Doc to see which endpoints write or have side
effects, and review arguments before approving these calls in your client.

## Security

- Never commit or share your `.env` file or your API key.
- `.env` is listed in `.gitignore`.
- The token is sent only as `Authorization: Bearer <token>` to the SaaS API. It is
  not logged and is not included in error messages.

## Troubleshooting

- **`Failed to fetch OpenAPI spec ...`** — the SaaS app isn't reachable or
  `OPENAPI_SPEC_URL` is wrong. Verify with
  `curl http://localhost:3000/api-docs/v1/openapi.yaml`.
- **`SAAS_API_KEY is required`** — no token in the environment
  passed to the server. Add it to your MCP client's `env`.
- **401 Unauthorized on tool calls** — the key is invalid or revoked. Issue a new
  one in Settings → Developer API.
- **Connection refused on tool calls** — `API_BASE_URL` is wrong or the SaaS app
  isn't running.
- For more detail, set `LOG_LEVEL=DEBUG`.
