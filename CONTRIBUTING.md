# Contributing to strategy-mcp

Thanks for your interest in contributing! strategy-mcp is an open source project that encodes product strategy frameworks as MCP tools.

## Ways to contribute

### Add a new framework tool

Have a product framework you use regularly? Open an issue with:
- The framework name
- What inputs it needs
- What the output should look like
- A real-world example of when you'd use it

Label: `tool-request`

### Improve an existing tool

If a tool gives shallow analysis or misses important nuances of the framework, that's worth fixing. Better reasoning logic, smarter recommendations, and more actionable next steps are always welcome.

Label: `enhancement`

### Add test cases

We use realistic product scenarios as test inputs. Edge cases and creative uses of the frameworks are especially valuable. Tests should assert on output structure, not exact text content.

Label: `enhancement`

### Fix bugs

If a tool gives bad advice, that's a bug. If inputs that should work cause errors, that's a bug. Report it or fix it.

Label: `bug`

## Development setup

```bash
git clone https://github.com/sohaibt/strategy-mcp.git
cd strategy-mcp
uv sync --dev
```

### Run tests

```bash
uv run pytest tests/ -v
```

### Run the server locally

```bash
uv run python server.py
```

## Adding a new tool

1. **Pick the right module** in `tools/`:
   - `prioritization.py` — Scoring and ranking frameworks
   - `discovery.py` — User research and assumption frameworks
   - `positioning.py` — Market and competitive frameworks
   - `business_model.py` — Business model and market sizing
   - `execution.py` — Planning and goal-setting frameworks
   - `advanced.py` — Evolution and hypothesis frameworks
   - `governance.py` — Decision and documentation frameworks

2. **Define your Pydantic models** in `schemas/models.py` for both input and output.

3. **Implement the tool function** decorated with `@mcp.tool` in the appropriate module.

4. **Every tool must return:**
   - A structured analysis with reasoning (not just a score)
   - 2-5 actionable next steps
   - A confidence indicator (High / Medium / Low) with rationale
   - 2-3 pressure-test questions

5. **Add tests** in `tests/test_tools.py` with realistic product scenarios.

## Pull request guidelines

- Open an issue first for large changes so we can discuss the approach
- Keep PRs focused — one tool or one fix per PR
- Include tests for any new functionality
- Make sure all existing tests still pass

## Code style

- Python 3.11+
- Type hints on function signatures
- Docstrings on tool functions (these become the tool descriptions in MCP)
- No external API calls — all analysis runs locally using framework logic

## Questions?

Open an issue or reach out to [Sohaib Thiab](https://sohaibthiab.me).
