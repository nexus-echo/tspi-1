"""TSPI AI Brain — MCP server.

A thin governance + adapter layer that exposes the existing TSPI FastAPI engine to AI chat
clients (Claude Desktop / Claude.ai / ChatGPT) as MCP tools. It contains NO clinical logic:
the engine remains the single deterministic source of truth. This layer only (a) presents the
engine's endpoints as well-described tools, (b) enforces de-identification, and (c) surfaces the
physician-approval / draft governance in every response.
"""

__version__ = "0.1.0"
