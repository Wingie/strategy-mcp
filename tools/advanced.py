"""Advanced strategy tools — Wardley evolution assessment and hypothesis builder.

These tools help product teams think about component maturity, strategic
positioning over time, and structured experimentation.
"""

from typing import Annotated
from pydantic import Field

from app import mcp
from schemas.models import (
    WardleyComponent,
    WardleyAssessmentOutput,
    ProductHypothesis,
    HypothesisBuilderOutput,
)


# ---------------------------------------------------------------------------
# Wardley Evolution Assessment
# ---------------------------------------------------------------------------

_STAGE_CHARACTERISTICS = {
    "Genesis": {
        "description": "Novel, uncertain, requires exploration. No established market or best practices.",
        "signals": ["no clear market", "high uncertainty", "experimental", "novel technology", "research phase"],
        "build_buy": "Build — this doesn't exist as a product yet. You must create it.",
    },
    "Custom-Built": {
        "description": "Understood enough to build, but no off-the-shelf solutions. Competitive advantage possible.",
        "signals": ["few providers", "custom implementation", "competitive differentiator", "emerging market", "early adopters"],
        "build_buy": "Build — custom solutions still give you an edge. Consider open-sourcing non-core components.",
    },
    "Product": {
        "description": "Established market with multiple vendors. Features are converging. Differentiation through execution.",
        "signals": ["multiple vendors", "feature convergence", "established market", "best practices exist", "growing competition"],
        "build_buy": "Buy or integrate — unless this is your core differentiator. Don't reinvent what others sell.",
    },
    "Commodity": {
        "description": "Ubiquitous, standardized, utility. Competing on price/reliability, not features.",
        "signals": ["utility", "standardized", "price competition", "APIs available", "everyone uses it"],
        "build_buy": "Buy/rent — use a commodity provider. Building this yourself is waste unless you're at massive scale.",
    },
}


def _classify_stage(component_name: str, description: str) -> tuple[str, str]:
    """Classify a component's evolution stage based on its name and description."""
    # Combine name and description for broader signal matching
    desc_lower = f"{component_name} {description}".lower()

    # Score each stage based on signal matches
    scores = {}
    for stage, info in _STAGE_CHARACTERISTICS.items():
        score = sum(1 for signal in info["signals"] if signal in desc_lower)
        scores[stage] = score

    # If clear winner, use it
    max_score = max(scores.values())
    if max_score > 0:
        best_stage = max(scores, key=scores.get)
        return best_stage, _STAGE_CHARACTERISTICS[best_stage]["description"]

    # Default heuristic based on common patterns
    commodity_keywords = ["aws", "cloud", "api", "database", "auth", "email", "payment", "cdn", "dns", "storage", "logging"]
    product_keywords = ["saas", "platform", "tool", "software", "service", "vendor", "crm", "analytics"]
    custom_keywords = ["proprietary", "internal", "custom", "our own", "bespoke", "in-house"]
    genesis_keywords = ["ai", "ml", "experimental", "prototype", "research", "novel", "new approach"]

    for kw in commodity_keywords:
        if kw in desc_lower:
            return "Commodity", _STAGE_CHARACTERISTICS["Commodity"]["description"]
    for kw in genesis_keywords:
        if kw in desc_lower:
            return "Genesis", _STAGE_CHARACTERISTICS["Genesis"]["description"]
    for kw in custom_keywords:
        if kw in desc_lower:
            return "Custom-Built", _STAGE_CHARACTERISTICS["Custom-Built"]["description"]
    for kw in product_keywords:
        if kw in desc_lower:
            return "Product", _STAGE_CHARACTERISTICS["Product"]["description"]

    return "Product", "Defaulting to Product stage — provide more detail for a precise classification."


def _assess_movement(stage: str, description: str) -> str:
    """Determine if a component is actively evolving."""
    desc_lower = description.lower()
    evolving_signals = ["growing", "changing", "new", "emerging", "shifting", "improving", "developing"]
    stable_signals = ["mature", "stable", "established", "standardized", "commoditized", "legacy"]

    evolving_count = sum(1 for s in evolving_signals if s in desc_lower)
    stable_count = sum(1 for s in stable_signals if s in desc_lower)

    if evolving_count > stable_count:
        return "Evolving"
    elif stable_count > evolving_count:
        return "Stable"
    # Stage-based default
    elif stage in ("Genesis", "Custom-Built"):
        return "Evolving"
    else:
        return "Stable"


@mcp.tool
def wardley_assessment(
    value_chain_context: Annotated[str, Field(
        description="What value chain or domain are you assessing? (e.g., 'Our AI-powered product management platform')"
    )],
    components: Annotated[list[dict], Field(
        description=(
            "Components to assess. Each should have: "
            "'name' (str, e.g., 'AI Model'), "
            "'description' (str, describe what it is and how mature it is, "
            "e.g., 'Custom ML model for feature prioritization, built in-house, no market equivalent')"
        ),
    )],
) -> str:
    """Assess where components sit on the Wardley evolution axis.

    Wardley Maps use four evolution stages:
    - Genesis: Novel, uncertain, no market exists
    - Custom-Built: Understood but no off-the-shelf solutions
    - Product: Established market, multiple vendors
    - Commodity: Ubiquitous, standardized, utility

    This tool classifies each component and recommends build vs. buy decisions.
    """

    if not components:
        return '{"error": "No components provided. Please provide at least one component to assess."}'

    assessed: list[WardleyComponent] = []
    for comp in components:
        name = comp.get("name", "Unknown")
        description = comp.get("description", "")

        stage, stage_reasoning = _classify_stage(name, description)
        movement = _assess_movement(stage, description)
        build_buy = _STAGE_CHARACTERISTICS[stage]["build_buy"]

        strategic_impl = (
            f"{name} is at the **{stage}** stage. {build_buy} "
            f"{'This is evolving — reassess in 6 months.' if movement == 'Evolving' else 'This is stable — focus effort elsewhere.'}"
        )

        assessed.append(WardleyComponent(
            name=name,
            stage=stage,
            stage_reasoning=f"{description.strip()} → {stage_reasoning}",
            movement=movement,
            strategic_implications=strategic_impl,
        ))

    # Stage distribution
    stage_dist = {"Genesis": 0, "Custom-Built": 0, "Product": 0, "Commodity": 0}
    for c in assessed:
        stage_dist[c.stage] += 1

    # Strategic summary
    total = len(assessed)
    genesis_pct = stage_dist["Genesis"] / total * 100
    commodity_pct = stage_dist["Commodity"] / total * 100

    summary_parts = [
        f"Assessed **{total} components** in the {value_chain_context} value chain.\n",
        f"- **Genesis:** {stage_dist['Genesis']} ({genesis_pct:.0f}%) — novel, high-uncertainty components",
        f"- **Custom-Built:** {stage_dist['Custom-Built']} — competitive differentiators to invest in",
        f"- **Product:** {stage_dist['Product']} — buy or integrate, don't reinvent",
        f"- **Commodity:** {stage_dist['Commodity']} ({commodity_pct:.0f}%) — use utilities, minimize custom work",
    ]

    if genesis_pct > 40:
        summary_parts.append("\nHigh proportion of Genesis components — you're operating with significant uncertainty. Expect pivots.")
    if commodity_pct > 50:
        summary_parts.append("\nMost components are commodities — your differentiation must come from how you combine them, not what they are.")

    strategic_summary = "\n".join(summary_parts)

    # Build vs buy recommendations
    build_recs = []
    for c in assessed:
        if c.stage in ("Genesis", "Custom-Built"):
            build_recs.append(f"**Build** {c.name} — {_STAGE_CHARACTERISTICS[c.stage]['build_buy']}")
        else:
            build_recs.append(f"**Buy/rent** {c.name} — {_STAGE_CHARACTERISTICS[c.stage]['build_buy']}")

    # Analysis
    evolving_components = [c.name for c in assessed if c.movement == "Evolving"]
    analysis = (
        f"**Value chain:** {value_chain_context}\n\n"
        f"{strategic_summary}\n\n"
    )
    if evolving_components:
        analysis += f"**Actively evolving:** {', '.join(evolving_components)} — these will shift stages over time. Reassess quarterly."

    # Next steps
    next_steps = [
        "Map these components visually on a Wardley Map (X axis = evolution, Y axis = value chain position).",
        "Focus engineering investment on Genesis and Custom-Built components — that's where you create competitive advantage.",
    ]
    if stage_dist["Product"] > 0 or stage_dist["Commodity"] > 0:
        next_steps.append("Audit Product/Commodity components for custom implementations you should replace with off-the-shelf solutions.")
    if evolving_components:
        next_steps.append(f"Set a 6-month reminder to reassess evolving components: {', '.join(evolving_components[:3])}.")
    next_steps.append("Share this assessment with your engineering team — their input on component maturity will improve accuracy.")
    next_steps = next_steps[:5]

    # Confidence
    well_described = sum(1 for comp in components if len(comp.get("description", "").split()) >= 8)
    if well_described >= total * 0.7:
        conf = "High"
        conf_rationale = "Most components have detailed descriptions — classifications are well-informed."
    elif well_described >= total * 0.4:
        conf = "Medium"
        conf_rationale = "Some components lack detail — classifications may need refinement."
    else:
        conf = "Low"
        conf_rationale = "Most descriptions are sparse — add more detail for accurate classification."

    # Pressure-test questions
    questions = [
        "Are you sure your 'Genesis' components aren't actually Custom-Built elsewhere? Research competitors before assuming novelty.",
        "Are you building any 'Product' or 'Commodity' components in-house that you should be buying?",
    ]
    if stage_dist["Genesis"] > 0:
        questions.append("For your Genesis components — what's your plan if the market evolves faster than expected?")
    else:
        questions.append("Do you have any truly novel components, or are you competing purely on execution of known patterns?")

    output = WardleyAssessmentOutput(
        context=value_chain_context,
        components=assessed,
        stage_distribution=stage_dist,
        strategic_summary=strategic_summary,
        build_vs_buy_recommendations=build_recs,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# Hypothesis Builder
# ---------------------------------------------------------------------------

@mcp.tool
def hypothesis_builder(
    assumptions: Annotated[list[dict], Field(
        description=(
            "Assumptions to turn into testable hypotheses. Each should have: "
            "'assumption' (str, e.g., 'Product managers will pay for AI-powered RICE scoring'), "
            "'target_user' (str, e.g., 'B2B SaaS product managers'), "
            "'expected_outcome' (str, e.g., 'Faster prioritization decisions'), "
            "and optionally 'risk_level' (str, 'High'/'Medium'/'Low', how bad if this is wrong)"
        ),
    )],
    product_context: Annotated[str, Field(
        description="Brief context about the product (e.g., 'AI-powered product management platform targeting mid-market SaaS teams')"
    )],
) -> str:
    """Build testable product hypotheses from assumptions.

    Transforms vague assumptions into structured, testable hypotheses with
    clear independent/dependent variables, success metrics, and test methods.

    Format: "We believe that [action] will result in [outcome] for [user].
    We'll know this is true when [metric] reaches [threshold]."
    """

    if not assumptions:
        return '{"error": "No assumptions provided. Please provide at least one assumption."}'

    hypotheses: list[ProductHypothesis] = []

    for a in assumptions:
        assumption_text = a.get("assumption", "")
        target_user = a.get("target_user", "target users")
        expected_outcome = a.get("expected_outcome", "improved experience")
        risk_level = a.get("risk_level", "Medium")

        # Build the hypothesis statement
        hypothesis_statement = (
            f"We believe that building/offering a solution for '{assumption_text}' "
            f"will result in {expected_outcome} for {target_user}."
        )

        # Determine independent variable (what we're testing)
        independent_var = f"The presence/design of the feature or approach based on: '{assumption_text}'"

        # Determine dependent variable (what we're measuring)
        outcome_lower = expected_outcome.lower()
        if any(w in outcome_lower for w in ("revenue", "pay", "monetiz", "pricing", "conversion")):
            dependent_var = "Conversion rate or revenue per user"
            success_metric = "Conversion rate from free to paid"
            success_threshold = "At least 5% conversion within 30 days of exposure"
            test_method = "A/B test with pricing page variations or feature gating"
            test_duration = "4-6 weeks (minimum 2 conversion cycles)"
        elif any(w in outcome_lower for w in ("engage", "usage", "adopt", "active", "retention")):
            dependent_var = "User engagement or retention metrics"
            success_metric = "Weekly active usage rate"
            success_threshold = "30%+ of exposed users return weekly"
            test_method = "Feature flag rollout to a cohort, measure engagement vs. control"
            test_duration = "3-4 weeks (enough for habit formation signal)"
        elif any(w in outcome_lower for w in ("fast", "time", "efficien", "quick", "speed", "reduc")):
            dependent_var = "Task completion time or efficiency gain"
            success_metric = "Time to complete target task"
            success_threshold = "At least 30% reduction in task completion time"
            test_method = "Prototype test with 10-15 users, measure time-on-task"
            test_duration = "1-2 weeks (usability test sprint)"
        elif any(w in outcome_lower for w in ("satisf", "nps", "happy", "love", "delight")):
            dependent_var = "User satisfaction score"
            success_metric = "CSAT or NPS score"
            success_threshold = "CSAT > 4.0/5.0 or NPS > 40"
            test_method = "Post-interaction survey with exposed users"
            test_duration = "2-3 weeks (enough for meaningful sample)"
        else:
            dependent_var = f"Measurable change in: {expected_outcome}"
            success_metric = f"Quantified measure of '{expected_outcome}'"
            success_threshold = "Define a specific numeric threshold before testing"
            test_method = "Start with 5-10 user interviews, then design a quantitative test"
            test_duration = "2-4 weeks depending on test method"

        # Risk assessment
        if risk_level.lower() == "high":
            risk_if_wrong = (
                f"High risk: If '{assumption_text}' is false, significant resources may be wasted "
                f"on the wrong approach. Test this before committing to full build."
            )
        elif risk_level.lower() == "low":
            risk_if_wrong = (
                f"Low risk: If wrong, the impact is limited. But still worth testing to avoid "
                f"building features nobody uses."
            )
        else:
            risk_if_wrong = (
                f"Medium risk: If '{assumption_text}' is false, you'll need to pivot your approach "
                f"but the overall strategy can likely adapt."
            )

        hypotheses.append(ProductHypothesis(
            hypothesis_statement=hypothesis_statement,
            assumption_being_tested=assumption_text,
            independent_variable=independent_var,
            dependent_variable=dependent_var,
            target_user=target_user,
            success_metric=success_metric,
            success_threshold=success_threshold,
            suggested_test_method=test_method,
            estimated_test_duration=test_duration,
            risk_if_wrong=risk_if_wrong,
        ))

    # Testing priority — high risk first, then by specificity
    risk_order = {"high": 0, "medium": 1, "low": 2}
    sorted_hypotheses = sorted(
        enumerate(hypotheses),
        key=lambda x: risk_order.get(assumptions[x[0]].get("risk_level", "Medium").lower(), 1),
    )
    testing_priority = []
    for idx, h in sorted_hypotheses:
        risk = assumptions[idx].get("risk_level", "Medium")
        testing_priority.append(
            f"Test '{h.assumption_being_tested}' ({risk} risk) — {h.suggested_test_method}"
        )

    # Experiment design notes
    experiment_notes = (
        f"**{len(hypotheses)} hypotheses** generated from your assumptions about {product_context}.\n\n"
        f"**General experiment guidelines:**\n"
        f"1. Test the highest-risk assumption first — it's the one most likely to invalidate your strategy.\n"
        f"2. Define success criteria BEFORE running the test. Moving the goalposts after seeing data is a trap.\n"
        f"3. Keep tests small and fast. A week with 10 users beats a month with 1000 if you learn the right thing.\n"
        f"4. Document results whether positive or negative — failed hypotheses are as valuable as confirmed ones.\n"
        f"5. One hypothesis per test. Testing multiple assumptions simultaneously makes results uninterpretable."
    )

    # Analysis
    high_risk_count = sum(1 for a in assumptions if a.get("risk_level", "Medium").lower() == "high")
    analysis = (
        f"Built **{len(hypotheses)} testable hypotheses** for {product_context}.\n\n"
        f"{'**' + str(high_risk_count) + ' high-risk assumption(s)** should be tested first — these could invalidate your core strategy.' if high_risk_count > 0 else 'No assumptions flagged as high-risk, but test the most uncertain ones first.'}\n\n"
        f"Each hypothesis follows the format: 'We believe [action] → [outcome] for [user], "
        f"measured by [metric] reaching [threshold].'"
    )

    # Next steps
    next_steps = [
        f"Pick the top hypothesis from the priority list and design a test this week.",
        "Set up a hypothesis tracker (spreadsheet or Notion table) with: hypothesis, test method, status, result, decision.",
    ]
    if high_risk_count > 0:
        next_steps.append(f"The {high_risk_count} high-risk hypothesis/hypotheses should be tested before committing to full development.")
    next_steps.append("After each test, decide: proceed (confirmed), pivot (partially confirmed), or kill (refuted).")
    next_steps.append("Share results with your team — hypotheses are most valuable when they're a shared understanding.")
    next_steps = next_steps[:5]

    # Confidence
    well_specified = sum(
        1 for a in assumptions
        if a.get("assumption") and a.get("target_user") and a.get("expected_outcome")
    )
    if well_specified == len(assumptions):
        conf = "High"
        conf_rationale = "All assumptions have target users and expected outcomes — hypotheses are well-structured."
    elif well_specified >= len(assumptions) * 0.5:
        conf = "Medium"
        conf_rationale = "Some assumptions are missing target users or outcomes — hypotheses may need refinement."
    else:
        conf = "Low"
        conf_rationale = "Most assumptions lack key details — hypotheses are generic. Add target users and expected outcomes."

    # Pressure-test questions
    questions = [
        "Are these the right assumptions to test, or are you avoiding the scary ones? The most uncomfortable hypothesis is usually the most important.",
        "Can you actually measure the success metrics you've defined? Do you have the instrumentation in place?",
    ]
    if len(hypotheses) > 3:
        questions.append(f"You have {len(hypotheses)} hypotheses — can you realistically test all of them? Focus on the top 2-3.")
    else:
        questions.append("Are there assumptions you're taking for granted that should also be hypotheses?")

    output = HypothesisBuilderOutput(
        hypotheses=hypotheses,
        testing_priority=testing_priority,
        experiment_design_notes=experiment_notes,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
