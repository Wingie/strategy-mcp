"""Prioritization tools — RICE scoring and related frameworks.

RICE = (Reach × Impact × Confidence) / Effort
A widely-used prioritization framework that turns gut feelings into comparable scores.
"""

from typing import Annotated
from pydantic import Field

from server import mcp
from schemas.models import RiceScoreOutput


@mcp.tool
def rice_score(
    feature_name: Annotated[str, Field(description="Name of the feature or initiative to score")],
    reach: Annotated[int, Field(description="How many users will this affect per quarter?", ge=0)],
    impact: Annotated[float, Field(
        description=(
            "Expected impact per user. Use: 3 = massive, 2 = high, "
            "1 = medium, 0.5 = low, 0.25 = minimal"
        ),
    )],
    confidence_pct: Annotated[int, Field(
        description="How confident are you in these estimates? (0-100%)",
        ge=0, le=100,
    )],
    effort: Annotated[float, Field(
        description="Estimated effort in person-months (e.g., 0.5, 1, 3, 6)",
        gt=0,
    )],
) -> str:
    """Score a feature using the RICE prioritization framework.

    RICE = (Reach × Impact × Confidence) / Effort

    Returns a structured analysis with the score, priority tier,
    reasoning, next steps, and questions to pressure-test your estimates.
    """

    # --- Calculate RICE score ---
    confidence_decimal = confidence_pct / 100
    rice = (reach * impact * confidence_decimal) / effort

    # --- Classify priority tier ---
    if rice >= 500:
        tier = "Critical"
    elif rice >= 200:
        tier = "High"
    elif rice >= 50:
        tier = "Medium"
    else:
        tier = "Low"

    # --- Generate score breakdown ---
    breakdown = (
        f"RICE = (Reach × Impact × Confidence) / Effort\n"
        f"     = ({reach:,} × {impact} × {confidence_decimal}) / {effort}\n"
        f"     = {rice:,.1f}"
    )

    # --- Generate analysis ---
    analysis_parts = [f"**{feature_name}** scores **{rice:,.1f}** — classified as **{tier}** priority.\n"]

    # Analyze each factor
    if reach >= 10000:
        analysis_parts.append(f"- **Reach is strong** ({reach:,} users/quarter) — this affects a large portion of your user base.")
    elif reach >= 1000:
        analysis_parts.append(f"- **Reach is moderate** ({reach:,} users/quarter) — a meaningful segment but not the majority.")
    else:
        analysis_parts.append(f"- **Reach is limited** ({reach:,} users/quarter) — this targets a small subset of users.")

    impact_labels = {3: "massive", 2: "high", 1: "medium", 0.5: "low", 0.25: "minimal"}
    impact_label = impact_labels.get(impact, f"{impact}x")
    analysis_parts.append(f"- **Impact is {impact_label}** ({impact}x) per user affected.")

    if confidence_pct >= 80:
        analysis_parts.append(f"- **Confidence is high** ({confidence_pct}%) — estimates are well-supported by data.")
    elif confidence_pct >= 50:
        analysis_parts.append(f"- **Confidence is moderate** ({confidence_pct}%) — some assumptions need validation.")
    else:
        analysis_parts.append(f"- **Confidence is low** ({confidence_pct}%) — significant uncertainty in these estimates.")

    if effort <= 1:
        analysis_parts.append(f"- **Effort is low** ({effort} person-months) — quick win potential.")
    elif effort <= 3:
        analysis_parts.append(f"- **Effort is moderate** ({effort} person-months) — manageable scope.")
    else:
        analysis_parts.append(f"- **Effort is high** ({effort} person-months) — significant investment required.")

    analysis = "\n".join(analysis_parts)

    # --- Generate next steps ---
    next_steps = []
    if confidence_pct < 60:
        next_steps.append("Run a quick user survey or data pull to increase confidence in your reach/impact estimates.")
    if tier in ("Critical", "High"):
        next_steps.append(f"Prioritize {feature_name} in the next sprint/cycle — the score supports it.")
        next_steps.append("Define success metrics before building so you can validate the impact estimate post-launch.")
    if tier == "Medium":
        next_steps.append("Compare this score against other backlog items to see where it ranks relatively.")
        next_steps.append("Consider if effort can be reduced by scoping down to an MVP version.")
    if tier == "Low":
        next_steps.append("Deprioritize unless there's a strategic reason beyond the numbers (e.g., retention, compliance).")
        next_steps.append("Revisit if reach or impact assumptions change based on new data.")
    if effort > 3:
        next_steps.append("Break this into smaller deliverables — can you ship a valuable slice in under 1 person-month?")

    # Ensure 2-5 next steps
    next_steps = next_steps[:5]
    if len(next_steps) < 2:
        next_steps.append("Stack-rank this against your top 5 backlog items using the same RICE framework for consistency.")

    # --- Confidence assessment ---
    if confidence_pct >= 70 and reach >= 100:
        conf = "High"
        conf_rationale = "The input estimates appear data-informed (high confidence %, meaningful reach)."
    elif confidence_pct >= 40:
        conf = "Medium"
        conf_rationale = "Moderate confidence in estimates — directionally useful but worth validating key assumptions."
    else:
        conf = "Low"
        conf_rationale = "Low confidence in the underlying estimates — treat this score as a rough signal, not a decision."

    # --- Pressure-test questions ---
    questions = [
        f"Is the reach estimate ({reach:,} users/quarter) based on actual data or a gut feeling?",
        f"Would the impact really be {impact_label}? What's the evidence from user research or comparable features?",
    ]
    if effort > 2:
        questions.append(f"Can the effort ({effort} person-months) be reduced by cutting scope? What's the MVP version?")
    else:
        questions.append(f"Are there hidden dependencies or technical risks that could inflate the {effort}-month effort estimate?")

    result = RiceScoreOutput(
        feature_name=feature_name,
        reach=reach,
        impact=impact,
        confidence_pct=confidence_pct,
        effort=effort,
        rice_score=round(rice, 1),
        priority_tier=tier,
        score_breakdown=breakdown,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return result.model_dump_json(indent=2)
