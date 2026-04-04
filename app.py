"""Shared FastMCP application instance.

All tool modules import `mcp` from here to avoid the __main__
double-import problem that occurs when importing from server.py.
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="strategy-mcp",
    instructions=(
        "Product strategy analysis tools. Each tool accepts structured inputs "
        "and returns professional-grade strategic analysis with actionable next steps. "
        "Use these tools when you need to score features (RICE), map assumptions, analyze jobs-to-be-done, "
        "assess competitive positioning, review business models (BMC), size markets (TAM/SAM/SOM), "
        "generate OKRs, or analyze pricing strategy. "
        "If the user does not provide explicit numeric values for tool inputs, estimate reasonable "
        "defaults based on context, call the tool with those estimates, and clearly flag your "
        "assumptions in the response so the user can validate and adjust."
    ),
)
