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

- [`uv`](https://docs.astral.sh/uv/) installed (it ships the `uvx` launcher and
  manages Python for you — you do **not** need to install Python yourself)
- A SaaS API key

## Get a SaaS API key

In the web app, go to **Settings → Developer API** and issue a key. The token
looks like `sa_...`. Keep it secret — treat it like a password.

## Quick start (no clone — recommended)

You don't need to clone this repo or install anything by hand. `uvx` fetches the
server straight from GitHub, builds it in an isolated environment, and runs it —
all in one command. The first run downloads and caches it; later runs start
instantly. The only configuration you need is your API key.

Add this to your MCP client's config:

```json
{
  "mcpServers": {
    "posbuzz": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/pos-buzz/posbuzz-mcp@main", "posbuzz-mcp"],
      "env": {
        "SAAS_API_KEY": "sa_your_api_key"
      }
    }
  }
}
```

By default the server talks to the production API at `https://pos-buzz.com`, so
`SAAS_API_KEY` is the only thing you have to set.

### Claude Code

One command — no config file editing:

```bash
claude mcp add posbuzz \
  --env SAAS_API_KEY=sa_your_api_key \
  -- uvx --from git+https://github.com/pos-buzz/posbuzz-mcp@main posbuzz-mcp
```

### Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.posbuzz]
command = "uvx"
args = ["--from", "git+https://github.com/pos-buzz/posbuzz-mcp@main", "posbuzz-mcp"]
env = { SAAS_API_KEY = "sa_your_api_key" }
```

After editing the config, **restart your MCP client**.

### Getting updates

`uvx` caches the version it pulled from `@main`, so it won't pick up new commits
automatically. To upgrade to the latest, run it once with `--refresh`:

```bash
uvx --refresh --from git+https://github.com/pos-buzz/posbuzz-mcp@main posbuzz-mcp
```

(then restart your MCP client). You can also pin a release tag instead of
`@main`, e.g. `git+https://github.com/pos-buzz/posbuzz-mcp@v0.1.0`.

## Configuration

Set configuration via environment variables (via your MCP client's `env`).

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SAAS_API_KEY` | yes | — | SaaS API bearer token (`sa_...`) |
| `API_BASE_URL` | no | `https://pos-buzz.com` | SaaS API base URL |
| `OPENAPI_SPEC_URL` | no | `https://pos-buzz.com/api-docs/v1/openapi.yaml` | OpenAPI spec URL (YAML or JSON) |
| `MCP_NAME` | no | `posbuzz-mcp` | MCP server name shown to the client |
| `LOG_LEVEL` | no | `INFO` | Logging level (e.g. `DEBUG`) |

The defaults point at production, so a normal user only sets `SAAS_API_KEY`.
Copy `.env.example` to `.env` for local reference (the `.env` file is gitignored
and is **not** read automatically — pass values via your MCP client's `env`).

## Local development

If you're hacking on the server itself, clone the repo and run from source.

### Using uv

```bash
git clone https://github.com/pos-buzz/posbuzz-mcp.git
cd posbuzz-mcp
uv run posbuzz-mcp        # creates the env and runs the server (stdio)
# or run from anywhere:  uvx --from . posbuzz-mcp
```

### Using pip

```bash
git clone https://github.com/pos-buzz/posbuzz-mcp.git
cd posbuzz-mcp
pip install .
posbuzz-mcp               # console script
# or:  python -m posbuzz_mcp
```

To point a local checkout at a locally running SaaS app instead of production,
override the URLs in your `env`:

```bash
API_BASE_URL=http://localhost:3000 \
OPENAPI_SPEC_URL=http://localhost:3000/api-docs/v1/openapi.yaml \
uv run posbuzz-mcp
```

A matching MCP client config (Claude Code, Codex, or generic JSON) uses
`"command": "uv"` with
`"args": ["run", "--directory", "/abs/path/to/posbuzz-mcp", "posbuzz-mcp"]`, or
for a pip install just `"command": "posbuzz-mcp"`.

> **Note:** the repo must be **public** for the `uvx --from git+https://...`
> quick start to work without auth. If it ever becomes private, authenticate the
> Git fetch with a token (`git+https://<token>@github.com/...`) or SSH
> (`git+ssh://git@github.com/pos-buzz/posbuzz-mcp.git`).

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
