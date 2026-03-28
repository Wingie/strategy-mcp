"""strategy-mcp — Product strategy frameworks as MCP tools.

Built by Sohaib Thiab (sohaibthiab.me) | Strida (strida.studio) | GetVelocity.ai
"""

from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP(
    name="strategy-mcp",
    instructions=(
        "Product strategy analysis tools. Each tool accepts structured inputs "
        "and returns professional-grade strategic analysis with actionable next steps. "
        "Use these tools when you need to score features (RICE), map assumptions, analyze jobs-to-be-done, "
        "assess competitive positioning, review business models (BMC), size markets (TAM/SAM/SOM), "
        "generate OKRs, or analyze pricing strategy."
    ),
)

# Import and register tools from each module.
# Each module defines functions decorated with @mcp.tool — importing them
# is enough to register them with the server.
import tools.prioritization  # noqa: F401, E402 — RICE score
import tools.discovery  # noqa: F401, E402 — Assumption map, JTBD
import tools.positioning  # noqa: F401, E402 — Competitive positioning
import tools.business_model  # noqa: F401, E402 — BMC review, TAM/SAM/SOM, Pricing strategy
import tools.execution  # noqa: F401, E402 — OKR generator

if __name__ == "__main__":
    mcp.run()
