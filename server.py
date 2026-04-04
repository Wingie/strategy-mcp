"""strategy-mcp — Product strategy frameworks as MCP tools.

Built by Sohaib Thiab (sohaibthiab.me)
"""

from app import mcp

# Import and register tools from each module.
# Each module defines functions decorated with @mcp.tool — importing them
# is enough to register them with the server.
import tools.prioritization  # noqa: F401, E402 — RICE score
import tools.discovery  # noqa: F401, E402 — Assumption map, JTBD
import tools.positioning  # noqa: F401, E402 — Competitive positioning
import tools.business_model  # noqa: F401, E402 — BMC review, TAM/SAM/SOM, Pricing strategy
import tools.execution  # noqa: F401, E402 — OKR generator, Initiative scoper
import tools.advanced  # noqa: F401, E402 — Wardley assessment, Hypothesis builder
import tools.governance  # noqa: F401, E402 — Decision log

if __name__ == "__main__":
    mcp.run()
