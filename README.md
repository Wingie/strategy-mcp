# strategy-mcp

**Professional-grade product strategy frameworks as MCP tools.**

Give any MCP-compatible AI assistant — Claude Code, Cursor, Cline — instant access to 12 structured strategy frameworks. Not templates. Not prompts. Actual tools that accept your inputs, apply the framework, show the reasoning, and return specific next steps.

[![PyPI version](https://img.shields.io/pypi/v/strategy-mcp.svg)](https://pypi.org/project/strategy-mcp/)
[![Built with FastMCP](https://img.shields.io/badge/Built%20with-FastMCP-blue)](https://github.com/jlowin/fastmcp)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Compatible with Claude Code](https://img.shields.io/badge/Works%20with-Claude%20Code-orange)](https://claude.ai/code)
[![Compatible with Cursor](https://img.shields.io/badge/Works%20with-Cursor-purple)](https://cursor.sh)
[![Compatible with Cline](https://img.shields.io/badge/Works%20with-Cline-red)](https://github.com/cline/cline)

---

## Why this exists

AI tools are great at generating content. They're inconsistent at applying structured thinking.

strategy-mcp is the product management layer that's been missing from the AI toolkit. Every framework a PM reaches for — RICE scoring, Jobs-to-be-Done, competitive positioning, OKR generation — encoded as a tool your AI can use natively.

Each tool returns:
- **Structured analysis** with reasoning (not just a score)
- **2-5 actionable next steps** (not generic advice)
- **Confidence indicator** (High / Medium / Low) with rationale
- **Pressure-test questions** to challenge the analysis

Built by [Sohaib Thiab](https://sohaibthiab.me) — former CPO, now building AI products in public.

---

## Install in 60 seconds

strategy-mcp is published on [PyPI](https://pypi.org/project/strategy-mcp/) — install it with a single command.

### Claude Code

```bash
claude mcp add strategy-mcp -- uv run --with strategy-mcp python server.py
```

### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "strategy-mcp": {
      "command": "uv",
      "args": ["run", "--with", "strategy-mcp", "python", "server.py"]
    }
  }
}
```

### Cline

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "strategy-mcp": {
      "command": "uv",
      "args": ["run", "--with", "strategy-mcp", "python", "server.py"]
    }
  }
}
```

### Plain pip

```bash
pip install strategy-mcp
```

### Run locally (development)

```bash
git clone https://github.com/sohaibt/strategy-mcp.git
cd strategy-mcp
uv run python server.py
```

---

## The 12 Tools

### Prioritization

| Tool | What it does |
|------|-------------|
| `rice_score` | Score a feature using Reach, Impact, Confidence, Effort. Returns a calculated score, priority tier, and factor-by-factor analysis. |

### Discovery

| Tool | What it does |
|------|-------------|
| `assumption_map` | Map assumptions into a 2x2 matrix of confidence vs. impact. Identifies your riskiest bets and what to test first. |
| `jobs_to_be_done` | Analyze a feature through the JTBD lens — job statement, functional/emotional/social dimensions, hiring criteria, switching barriers. |

### Positioning

| Tool | What it does |
|------|-------------|
| `competitive_position` | Map your product and competitors on a 2-axis chart. Identifies nearest threats, white space, and differentiation opportunities. |

### Business Model

| Tool | What it does |
|------|-------------|
| `business_model_review` | Assess a business model using the Business Model Canvas. Reviews all 9 components for clarity, gaps, and coherence. |
| `tam_sam_som` | Estimate addressable market tiers with top-down + bottom-up cross-validation. Includes sanity checks and key assumptions. |
| `pricing_strategy` | Analyze pricing against positioning and the competitive landscape. Recommends a model, price range, and flags risks. |

### Execution

| Tool | What it does |
|------|-------------|
| `okr_generator` | Generate well-formed OKRs from a strategic goal. Creates an inspirational objective with 3-5 measurable key results. |
| `initiative_scoper` | Break a strategic goal into scoped initiatives with dependencies, effort estimates, critical path, and execution sequence. |

### Advanced

| Tool | What it does |
|------|-------------|
| `wardley_assessment` | Assess where components sit on the evolution axis (Genesis → Commodity). Recommends build vs. buy for each. |
| `hypothesis_builder` | Transform assumptions into structured, testable hypotheses with success metrics, test methods, and risk assessment. |
| `decision_log_entry` | Structure a product decision for archiving — captures context, alternatives, rationale, and revisit conditions. |

---

## Example: RICE Scoring

**Ask your AI assistant:**

> "Score our new AI onboarding feature using RICE. It reaches about 5,000 users per quarter, high impact, we're 80% confident, and it'll take 2 person-months."

**What you get back:**

```json
{
  "feature_name": "AI Onboarding Feature",
  "rice_score": 2000.0,
  "priority_tier": "Critical",
  "score_breakdown": "RICE = (Reach x Impact x Confidence) / Effort\n     = (5,000 x 1 x 0.8) / 2\n     = 2,000.0",
  "analysis": "**AI Onboarding Feature** scores **2,000.0** — classified as **Critical** priority.\n\n- **Reach is moderate** (5,000 users/quarter)\n- **Impact is medium** (1x) per user affected.\n- **Confidence is high** (80%)\n- **Effort is moderate** (2 person-months)",
  "next_steps": [
    "Prioritize AI Onboarding Feature in the next sprint/cycle — the score supports it.",
    "Define success metrics before building so you can validate the impact estimate post-launch.",
    "Stack-rank this against your top 5 backlog items using the same RICE framework for consistency."
  ],
  "confidence": "High",
  "confidence_rationale": "The input estimates appear data-informed (high confidence %, meaningful reach).",
  "pressure_test_questions": [
    "Is the reach estimate (5,000 users/quarter) based on actual data or a gut feeling?",
    "Would the impact really be medium? What's the evidence from user research?",
    "Are there hidden dependencies that could inflate the 2-month effort estimate?"
  ]
}
```

Every tool follows this same structure: analysis + next steps + confidence + pressure-test questions.

---

## Example: Business Model Canvas Review

> "Review the business model for my AI analytics startup. We target mid-market SaaS companies, our value prop is real-time anomaly detection..."

The tool assesses all 9 BMC components, rates each as Strong/Adequate/Weak/Missing, identifies critical gaps, evaluates coherence between components, and tells you exactly what to fix first.

---

## Example: Hypothesis Builder

> "I have three assumptions about my product. Turn them into testable hypotheses."

Each assumption becomes a structured hypothesis with: independent/dependent variables, success metric, success threshold, suggested test method, estimated duration, and risk assessment. Hypotheses are prioritized by risk level — test the scariest ones first.

---

## How it works

strategy-mcp is a stateless MCP server built with [FastMCP](https://github.com/jlowin/fastmcp). Each tool:

1. **Accepts structured inputs** via MCP tool parameters
2. **Applies the framework logic** in Python (no external API calls)
3. **Returns structured JSON** that your AI assistant formats into a readable response

All analysis is done locally using your inputs + the framework logic. No data leaves your machine. No API keys required.

### Architecture

```
Your AI Assistant (Claude/Cursor/Cline)
        │
        ▼
   MCP Protocol
        │
        ▼
  strategy-mcp server (FastMCP)
        │
        ├── tools/prioritization.py    → RICE scoring
        ├── tools/discovery.py         → Assumption map, JTBD
        ├── tools/positioning.py       → Competitive positioning
        ├── tools/business_model.py    → BMC, TAM/SAM/SOM, Pricing
        ├── tools/execution.py         → OKR generator, Initiative scoper
        ├── tools/advanced.py          → Wardley assessment, Hypothesis builder
        └── tools/governance.py        → Decision log
```

---

## Development

### Run tests

```bash
uv run pytest tests/ -v
```

All 12 tools have happy-path and edge-case tests (24 tests total).

### Project structure

```
strategy-mcp/
├── server.py              # MCP server entry point
├── tools/
│   ├── prioritization.py  # RICE score
│   ├── discovery.py       # Assumption map, JTBD
│   ├── positioning.py     # Competitive positioning
│   ├── business_model.py  # BMC, TAM/SAM/SOM, Pricing
│   ├── execution.py       # OKR generator, Initiative scoper
│   ├── advanced.py        # Wardley assessment, Hypothesis builder
│   └── governance.py      # Decision log
├── schemas/
│   └── models.py          # Pydantic models for all inputs/outputs
├── tests/
│   └── test_tools.py      # 24 tests across all 12 tools
└── pyproject.toml
```

---

## Contributing

Contributions welcome! Some ways to help:

- **Add a new framework tool** — open an issue with the framework name and what it should do
- **Improve an existing tool** — better analysis logic, smarter recommendations
- **Add test cases** — especially edge cases and realistic product scenarios
- **Fix bugs** — if a tool gives bad advice, that's a bug

Please open an issue before submitting large PRs so we can discuss the approach.

---

## License

MIT — use it however you want.

---

## Built by

[Sohaib Thiab](https://sohaibthiab.me) — Former CPO, now building AI products in public.

- [Mastering Product HQ](https://masteringproducthq.com) — Weekly writing on product leadership

**Want connected strategy execution?** [GetVelocity.ai](https://getvelocity.ai) takes these frameworks further — connecting your OKRs to Jira, Linear, and ClickUp with AI-powered monitoring and real-time velocity tracking.

---

If strategy-mcp saves you a bad decision, it's done its job.
