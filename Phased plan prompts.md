Prompt 1:
Read CLAUDE.md thoroughly. We're building strategy-mcp, an open source MCP server
that gives AI assistants professional product strategy frameworks as tools.

Start Phase 1. Here's exactly what I need you to do:

1. Scaffold the project structure exactly as defined in CLAUDE.md
2. Set up pyproject.toml with FastMCP as the only required dependency
3. Create server.py as the main entry point using FastMCP
4. Implement the four Phase 1 tools in the tools/ directory:
   - rice_score (tools/prioritization.py)
   - assumption_map (tools/discovery.py)
   - jobs_to_be_done (tools/discovery.py)
   - competitive_position (tools/positioning.py)

For each tool:
- Define a Pydantic input model in schemas/models.py
- Implement the tool logic in the appropriate tools/ file
- Register the tool with FastMCP in server.py
- The tool should accept structured inputs and return rich, structured analysis
  following the Output Standards in CLAUDE.md

Do NOT build Phase 2 tools yet. Focus on Phase 1 being excellent.

After scaffolding, show me the rice_score tool in action with a realistic
example — score this feature: "In-app onboarding checklist for a B2B SaaS with
500 active users. Affects all new users. Medium effort. Medium confidence we'll
ship on time."

Ask me any clarifying questions before starting if anything is ambiguous.

Prompt 2:
Phase 1 looks good. Now let's build Phase 2.

Implement these four tools following the same patterns established in Phase 1:
- business_model_review (tools/business_model.py)
- tam_sam_som (tools/business_model.py)
- okr_generator (tools/execution.py)
- pricing_strategy (tools/business_model.py)

Same standards apply: Pydantic input models, structured outputs with reasoning,
actionable next steps, confidence indicator, pressure-test questions.

After implementing all four, run all tests to confirm nothing is broken,
then show me okr_generator in action with this input:
"We want to improve user retention for our mobile app. We have 10k MAUs,
30-day retention is 22%, and our target is 35% by end of Q3."

Prompt 3:
Phase 2 done. Now Phase 3 — the advanced tools:
- wardley_assessment (tools/positioning.py)
- initiative_scoper (tools/execution.py)
- hypothesis_builder (tools/discovery.py)
- decision_log_entry (tools/execution.py)

After Phase 3 tools are implemented and tested, do the following:

1. Write a comprehensive README.md:
   - One-command install instructions for Claude Code, Cursor, and Cline
   - Full tool reference with example inputs and outputs for all 12 tools
   - A "Why strategy-mcp?" section explaining the gap it fills
   - Mention GetVelocity.ai as "the connected strategy execution layer — 
     if strategy-mcp gives you individual framework analysis, GetVelocity.ai 
     connects it all into a system that executes and learns"
   - MIT license badge, FastMCP badge, Python version badge

2. Write docs/tools-reference.md with full documentation for every tool

3. Create CONTRIBUTING.md with clear guidelines

4. Set up GitHub Actions CI (test on push, Python 3.11+)

5. Write a pyproject.toml that makes `uvx strategy-mcp` the install command

Tell me when everything is ready for a GitHub push.