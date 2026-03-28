"""Execution tools — OKR generator and initiative scoping.

These tools help product teams translate strategy into executable plans
with measurable outcomes and clear accountability.
"""

from typing import Annotated
from pydantic import Field

from server import mcp
from schemas.models import KeyResult, OkrGeneratorOutput


# ---------------------------------------------------------------------------
# OKR Generator
# ---------------------------------------------------------------------------

def _refine_objective(raw_goal: str) -> str:
    """Refine a raw strategic goal into a well-formed objective.

    Good objectives are:
    - Qualitative (not metric-driven — that's what KRs are for)
    - Inspirational but achievable
    - Clear enough that anyone can understand the direction
    - Action-oriented (starts with a verb)
    """
    goal = raw_goal.strip().rstrip(".")

    # If it already starts with a verb, keep it
    verb_starters = (
        "achieve", "build", "create", "deliver", "drive", "enable",
        "establish", "expand", "grow", "improve", "increase", "launch",
        "make", "reduce", "scale", "strengthen", "transform", "become",
        "accelerate", "deepen", "elevate", "prove", "unlock", "win",
    )
    if goal.lower().split()[0] in verb_starters:
        return goal

    # If it contains a metric, reframe as qualitative
    metric_words = ("%", "from", "to", "by", "increase", "decrease", "reduce")
    if any(w in goal.lower() for w in metric_words):
        return f"Drive measurable progress on: {goal}"

    # Default: make it action-oriented
    return f"Achieve {goal.lower()}" if goal[0].isupper() else f"Achieve {goal}"


def _generate_key_results(
    objective: str,
    goal: str,
    context: str,
    time_horizon: str,
    current_metrics: list[dict],
) -> list[KeyResult]:
    """Generate key results based on the objective and context.

    Good key results are:
    - Measurable with a specific metric
    - Have a baseline (where you are) and target (where you want to be)
    - Outcomes, not outputs (measure results, not activities)
    - Stretch but achievable (70% completion should feel like a win)
    """

    key_results = []

    # Use provided metrics to generate KRs
    for m in current_metrics[:3]:
        metric_name = m.get("metric", "")
        baseline = m.get("current_value", "unknown")
        target = m.get("target_value", "TBD")

        if metric_name and baseline and target:
            kr = KeyResult(
                key_result=f"Move {metric_name} from {baseline} to {target}",
                metric=metric_name,
                baseline=str(baseline),
                target=str(target),
                rationale=f"Directly measures progress toward the objective. Moving from {baseline} to {target} represents meaningful improvement.",
            )
            key_results.append(kr)

    # If fewer than 3 KRs from metrics, generate contextual ones
    if len(key_results) < 3:
        context_lower = context.lower()
        goal_lower = goal.lower()

        # Product/growth focused KRs
        if any(w in goal_lower for w in ("growth", "user", "customer", "acquisition", "signup")):
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Increase weekly active users by defining a specific growth target",
                    metric="Weekly Active Users (WAU)",
                    baseline="Define current WAU",
                    target="Set target based on growth rate goal",
                    rationale="User growth is the leading indicator of product-market fit and sustainable business growth.",
                ))
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Improve activation rate for new signups",
                    metric="Activation rate (% of signups completing core action)",
                    baseline="Measure current activation rate",
                    target="Set target 20-50% above current",
                    rationale="Activation converts signups into engaged users — growth without activation is a leaky bucket.",
                ))

        # Revenue focused KRs
        if any(w in goal_lower for w in ("revenue", "monetize", "pricing", "arr", "mrr")):
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Grow monthly recurring revenue",
                    metric="MRR",
                    baseline="Define current MRR",
                    target="Set target based on growth goals",
                    rationale="MRR is the primary measure of revenue health for subscription businesses.",
                ))

        # Quality/reliability focused KRs
        if any(w in goal_lower for w in ("quality", "reliability", "performance", "bug", "uptime")):
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Reduce critical bugs or incidents to near-zero",
                    metric="P0/P1 incident count per month",
                    baseline="Measure current incident rate",
                    target="Set target (e.g., <2/month)",
                    rationale="Reliability directly impacts user trust and retention.",
                ))

        # Launch/shipping focused KRs
        if any(w in goal_lower for w in ("launch", "ship", "release", "build", "deliver")):
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Ship the core feature set by the target date",
                    metric="Feature completeness (% of scoped features shipped)",
                    baseline="0%",
                    target="100% of Phase 1 scope",
                    rationale="On-time delivery of the core scope is the primary execution measure.",
                ))
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Achieve target user satisfaction post-launch",
                    metric="User satisfaction score (NPS, CSAT, or qualitative feedback)",
                    baseline="No baseline (new launch)",
                    target="Set target (e.g., NPS > 40, CSAT > 4.0)",
                    rationale="Shipping is only valuable if users find the result useful.",
                ))

        # Engagement focused KRs
        if any(w in goal_lower for w in ("engage", "retention", "churn", "stickiness")):
            if len(key_results) < 3:
                key_results.append(KeyResult(
                    key_result="Improve user retention over the time period",
                    metric="Retention rate (Day 7, Day 30, or monthly cohort)",
                    baseline="Measure current retention",
                    target="Set target based on industry benchmarks",
                    rationale="Retention is the clearest signal that users are getting ongoing value.",
                ))

        # Generic fallback KRs
        while len(key_results) < 3:
            fallback_krs = [
                KeyResult(
                    key_result="Define and hit the primary success metric for this objective",
                    metric="Primary success metric (define based on objective)",
                    baseline="Establish baseline this week",
                    target="Set stretch target (aim for 70% as a win)",
                    rationale="Every objective needs at least one quantitative measure of success.",
                ),
                KeyResult(
                    key_result="Complete all critical milestones within the time horizon",
                    metric="Milestone completion rate",
                    baseline="0%",
                    target="100% of critical milestones",
                    rationale="Milestone tracking ensures the team is making progress toward the objective.",
                ),
                KeyResult(
                    key_result="Validate the approach with stakeholder or user feedback",
                    metric="Qualitative validation (interviews, surveys, feedback score)",
                    baseline="No validation yet",
                    target="Positive signal from 5+ stakeholders/users",
                    rationale="External validation prevents building in a vacuum.",
                ),
            ]
            idx = len(key_results) - 3  # Will be negative, wrapping to grab fallbacks
            key_results.append(fallback_krs[len(key_results) % len(fallback_krs)])

    return key_results[:5]


@mcp.tool
def okr_generator(
    strategic_goal: Annotated[str, Field(
        description="The strategic goal to generate OKRs for (e.g., 'Launch our AI product to first 100 paying customers')"
    )],
    time_horizon: Annotated[str, Field(
        description="Time period for this OKR (e.g., 'Q2 2026', 'Next 90 days', 'H1 2026')"
    )],
    team_or_org: Annotated[str, Field(
        description="Who owns this OKR? (e.g., 'Product team', 'Growth squad', 'Entire company')"
    )],
    context: Annotated[str, Field(
        description="Relevant context: what's the current situation? (e.g., 'We have 50 beta users, product is stable, need to grow')"
    )],
    current_metrics: Annotated[list[dict], Field(
        description=(
            "Current metrics to base key results on. Each should have: "
            "'metric' (str, e.g., 'Monthly Active Users'), "
            "'current_value' (str, e.g., '500'), "
            "'target_value' (str, e.g., '2000'). "
            "Provide 1-5 metrics. Leave empty [] if you don't have metrics yet."
        ),
    )],
) -> str:
    """Generate well-formed OKRs from a strategic goal.

    Creates an inspirational objective with 3-5 measurable key results.
    Each key result has a specific metric, baseline, target, and rationale.

    Good OKRs follow the pattern:
    - Objective: qualitative, inspirational, time-bound
    - Key Results: quantitative, measurable, stretch (70% = success)
    """

    # Refine the objective
    objective = _refine_objective(strategic_goal)

    # Generate key results
    key_results = _generate_key_results(
        objective=objective,
        goal=strategic_goal,
        context=context,
        time_horizon=time_horizon,
        current_metrics=current_metrics,
    )

    # Assess objective quality
    quality_notes_parts = []

    # Check if objective is qualitative (good) vs. metric-driven (bad)
    if any(c.isdigit() for c in objective) or "%" in objective:
        quality_notes_parts.append("The objective contains numbers — objectives should be qualitative and inspirational. Move the metrics to key results.")
    else:
        quality_notes_parts.append("Objective is qualitative — good. It sets direction without being a metric.")

    # Check if it's inspirational
    if len(objective.split()) < 4:
        quality_notes_parts.append("Objective is very short — consider making it more descriptive to rally the team.")
    elif len(objective.split()) > 20:
        quality_notes_parts.append("Objective is wordy — try to tighten it to 10 words or fewer for memorability.")
    else:
        quality_notes_parts.append("Objective length is good — concise but descriptive.")

    # Check verb-leading
    first_word = objective.split()[0].lower()
    verb_starters = (
        "achieve", "build", "create", "deliver", "drive", "enable",
        "establish", "expand", "grow", "improve", "increase", "launch",
        "make", "reduce", "scale", "strengthen", "transform", "become",
        "accelerate", "deepen", "elevate", "prove", "unlock", "win",
    )
    if first_word in verb_starters:
        quality_notes_parts.append("Starts with an action verb — good, it's clear what direction to move.")
    else:
        quality_notes_parts.append(f"Consider starting with an action verb (e.g., 'Drive...', 'Launch...', 'Build...') for stronger direction.")

    objective_quality_notes = " ".join(quality_notes_parts)

    # Alignment notes
    alignment_notes = (
        f"This OKR is owned by **{team_or_org}** for **{time_horizon}**. "
        f"Context: {context}. "
        f"Ensure this OKR ladders up to a company-level objective. "
        f"If multiple teams have OKRs, check for dependencies and conflicts."
    )

    # Key results quality check
    has_real_baselines = any(
        m.get("current_value") and m.get("current_value") != "unknown"
        for m in current_metrics
    )
    metrics_provided = len(current_metrics)

    # Analysis
    analysis = (
        f"**Objective:** {objective}\n"
        f"**Owner:** {team_or_org} | **Period:** {time_horizon}\n\n"
        f"Generated **{len(key_results)} key results** "
        f"{'based on provided metrics' if metrics_provided > 0 else 'from strategic context (no baseline metrics provided)'}.\n\n"
    )

    if metrics_provided > 0:
        analysis += f"{metrics_provided} metric(s) provided as input — these anchor the KRs in real data.\n"
    else:
        analysis += "No baseline metrics provided — key results use placeholder targets. Replace these with real numbers ASAP.\n"

    analysis += (
        f"\nRemember: OKRs are not a to-do list. The objective should inspire, "
        f"and achieving 70% of key results should feel like a strong outcome."
    )

    # Next steps
    next_steps = []
    if not has_real_baselines:
        next_steps.append("Establish real baselines for each key result this week — you can't measure progress without a starting point.")
    next_steps.append(f"Share this OKR with {team_or_org} for feedback — OKRs work best when the team owns them, not just leadership.")
    next_steps.append("Set up a weekly check-in cadence to track KR progress (15 min, every Monday).")
    if len(key_results) > 3:
        next_steps.append(f"You have {len(key_results)} key results — consider cutting to 3 for sharper focus. Which ones matter most?")
    next_steps.append("At mid-cycle, score each KR 0.0-1.0 and adjust targets if needed (0.7 = on track).")
    next_steps = next_steps[:5]

    # Confidence
    if metrics_provided >= 2 and has_real_baselines:
        conf = "High"
        conf_rationale = "Baseline metrics provided — key results are grounded in real data."
    elif metrics_provided >= 1:
        conf = "Medium"
        conf_rationale = "Some metrics provided but baselines may need validation. Directionally useful."
    else:
        conf = "Low"
        conf_rationale = "No baseline metrics — key results use placeholder targets. Establish real baselines before committing to this OKR."

    # Pressure-test questions
    questions = [
        "If you achieve this objective, will it materially move the business? Or is it important-sounding but low-impact?",
        "Can each key result be measured without ambiguity? If two people measured it, would they get the same number?",
    ]
    if metrics_provided == 0:
        questions.append("You provided no baseline metrics. Do you actually have the instrumentation to measure these key results?")
    else:
        questions.append("Are the targets stretch goals (70% = success) or sandbagged? The best KRs make you slightly uncomfortable.")

    output = OkrGeneratorOutput(
        objective=objective,
        objective_quality_notes=objective_quality_notes,
        key_results=key_results,
        time_horizon=time_horizon,
        alignment_notes=alignment_notes,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
