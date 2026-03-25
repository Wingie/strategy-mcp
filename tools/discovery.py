"""Discovery tools — Assumption mapping and Jobs-to-be-Done analysis.

These tools help product teams validate what they think they know
and understand what users are actually trying to accomplish.
"""

from typing import Annotated
from pydantic import Field

from server import mcp
from schemas.models import (
    AssumptionInput,
    AssumptionResult,
    AssumptionMapOutput,
    JtbdOutput,
)


# ---------------------------------------------------------------------------
# Assumption Map
# ---------------------------------------------------------------------------

def _classify_quadrant(confidence: int, impact: int) -> str:
    """Classify an assumption into one of four quadrants.

    High impact + low confidence  → "Test Now"     (dangerous unknowns)
    High impact + high confidence → "Monitor"       (known and important)
    Low impact + low confidence   → "Research More"  (unknown but less urgent)
    Low impact + high confidence  → "Deprioritize"   (known and unimportant)

    Threshold: 3 on the 1-5 scale is the dividing line.
    """
    high_impact = impact >= 3
    high_confidence = confidence >= 3

    if high_impact and not high_confidence:
        return "Test Now"
    elif high_impact and high_confidence:
        return "Monitor"
    elif not high_impact and not high_confidence:
        return "Research More"
    else:
        return "Deprioritize"


def _urgency_score(confidence: int, impact: int) -> int:
    """Higher score = more urgent to address. Favors high-impact, low-confidence items."""
    return impact * (6 - confidence)


def _recommendation(quadrant: str, statement: str) -> str:
    """Generate a recommendation based on quadrant."""
    recs = {
        "Test Now": (
            f"Design a quick experiment to validate: \"{statement}\" — "
            "this is high-impact and you're not confident it's true. "
            "Consider user interviews, A/B tests, or prototype testing."
        ),
        "Monitor": (
            f"Keep tracking: \"{statement}\" — you're confident and it matters. "
            "Set up metrics or periodic check-ins to catch changes early."
        ),
        "Research More": (
            f"Gather more information on: \"{statement}\" — "
            "you're uncertain but the impact is lower. Desk research or "
            "lightweight surveys can help without heavy investment."
        ),
        "Deprioritize": (
            f"Park for now: \"{statement}\" — "
            "you're confident and the impact is low. Revisit only if the "
            "strategic context changes."
        ),
    }
    return recs[quadrant]


@mcp.tool
def assumption_map(
    assumptions: Annotated[list[dict], Field(
        description=(
            "List of assumptions to map. Each should have: "
            "'statement' (str), 'confidence_level' (1-5, how sure you are this is true), "
            "'impact_level' (1-5, how bad if this is wrong), "
            "and optionally 'category' (e.g., Market, Technical, User, Business)"
        ),
    )],
) -> str:
    """Map assumptions into a 2x2 matrix of confidence vs. impact.

    Quadrants:
    - Test Now: High impact, low confidence (dangerous unknowns — validate ASAP)
    - Monitor: High impact, high confidence (important knowns — track for changes)
    - Research More: Low impact, low confidence (unknowns that aren't urgent)
    - Deprioritize: Low impact, high confidence (known and unimportant)

    Returns prioritized assumptions with quadrant assignments, recommendations,
    and next steps for your product discovery process.
    """

    # Parse and validate inputs
    parsed = []
    for a in assumptions:
        inp = AssumptionInput(**a)
        parsed.append(inp)

    if not parsed:
        return '{"error": "No assumptions provided. Please provide at least one assumption."}'

    # Classify each assumption
    results: list[AssumptionResult] = []
    for a in parsed:
        quadrant = _classify_quadrant(a.confidence_level, a.impact_level)
        urgency = _urgency_score(a.confidence_level, a.impact_level)
        rec = _recommendation(quadrant, a.statement)

        results.append(AssumptionResult(
            statement=a.statement,
            confidence_level=a.confidence_level,
            impact_level=a.impact_level,
            category=a.category,
            quadrant=quadrant,
            urgency_score=urgency,
            recommendation=rec,
        ))

    # Sort by urgency (highest first)
    results.sort(key=lambda r: r.urgency_score, reverse=True)

    # Quadrant summary
    quadrant_counts = {"Test Now": 0, "Monitor": 0, "Research More": 0, "Deprioritize": 0}
    for r in results:
        quadrant_counts[r.quadrant] += 1

    # Generate analysis
    test_now_count = quadrant_counts["Test Now"]
    total = len(results)

    analysis_parts = [
        f"Mapped **{total} assumptions** across 4 quadrants.\n",
        f"- **Test Now:** {quadrant_counts['Test Now']} (high impact, low confidence — your riskiest bets)",
        f"- **Monitor:** {quadrant_counts['Monitor']} (high impact, high confidence — track these)",
        f"- **Research More:** {quadrant_counts['Research More']} (low impact, uncertain — investigate when bandwidth allows)",
        f"- **Deprioritize:** {quadrant_counts['Deprioritize']} (low impact, confident — safe to park)",
    ]

    if test_now_count > 0:
        top_risk = results[0].statement
        analysis_parts.append(f"\nHighest urgency: \"{top_risk}\"")

    analysis = "\n".join(analysis_parts)

    # Next steps
    next_steps = []
    if test_now_count > 0:
        next_steps.append(f"Design validation experiments for your {test_now_count} 'Test Now' assumption(s) this week.")
    if test_now_count > 2:
        next_steps.append("You have multiple high-risk assumptions — prioritize the top 2 and batch the rest.")
    next_steps.append("Schedule a team review of this assumption map to align on what to test first.")
    if quadrant_counts["Monitor"] > 0:
        next_steps.append("Set up dashboards or alerts for your 'Monitor' assumptions so you catch shifts early.")
    next_steps = next_steps[:5]
    if len(next_steps) < 2:
        next_steps.append("Revisit this map after each discovery cycle to update confidence levels.")

    # Confidence
    if total >= 4 and all(a.confidence_level != 3 and a.impact_level != 3 for a in parsed):
        conf = "High"
        conf_rationale = "Assumptions are well-distributed and ratings avoid the ambiguous midpoint."
    elif total >= 2:
        conf = "Medium"
        conf_rationale = "Reasonable input but some ratings may be anchored at midpoints — consider recalibrating."
    else:
        conf = "Low"
        conf_rationale = "Too few assumptions to draw reliable patterns. Add more to get a useful map."

    # Pressure-test questions
    questions = [
        "Are there critical assumptions you haven't listed? What are you taking for granted?",
        "Would your team rate these assumptions the same way? Try blind-rating to check alignment.",
    ]
    if test_now_count > 0:
        questions.append("For your 'Test Now' items — what's the fastest, cheapest way to get signal?")

    output = AssumptionMapOutput(
        total_assumptions=total,
        quadrant_summary=quadrant_counts,
        assumptions=results,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# Jobs-to-be-Done
# ---------------------------------------------------------------------------

@mcp.tool
def jobs_to_be_done(
    feature_or_problem: Annotated[str, Field(
        description="The feature you're building or problem you're solving"
    )],
    target_user: Annotated[str, Field(
        description="Who is the primary user (e.g., 'product managers at B2B SaaS companies')"
    )],
    context: Annotated[str, Field(
        description="When and where does this job arise? (e.g., 'during quarterly planning when prioritizing features')"
    )],
    current_alternatives: Annotated[list[str], Field(
        description="What do users currently use/do instead? (e.g., ['spreadsheets', 'gut feeling', 'JIRA voting'])"
    )],
    desired_outcomes: Annotated[list[str], Field(
        description="What outcomes does the user want? (e.g., ['faster decisions', 'stakeholder alignment', 'data-backed priorities'])"
    )],
) -> str:
    """Analyze a feature or problem through the Jobs-to-be-Done framework.

    Structures your input into the canonical JTBD format: job statement,
    functional/emotional/social dimensions, hiring criteria, firing triggers,
    and switching barriers. Helps you understand what users actually need
    (not just what they say they want).
    """

    # Build the canonical job statement
    # Format: "When [situation], I want to [motivation], so I can [outcome]."
    if len(desired_outcomes) >= 2:
        outcomes_text = f"achieve {desired_outcomes[0]} and {desired_outcomes[1]}"
    elif desired_outcomes:
        outcomes_text = f"achieve {desired_outcomes[0]}"
    else:
        outcomes_text = "get the job done more effectively"
    job_statement = f"When {context}, {target_user} want to {feature_or_problem}, so they can {outcomes_text}."

    # Derive functional job (the practical task)
    functional_job = (
        f"{target_user} need a reliable way to {feature_or_problem}. "
        f"Currently, they cobble together solutions using {', '.join(current_alternatives)}. "
        f"The functional outcome they need: {desired_outcomes[0] if desired_outcomes else 'a better way to get this done'}."
    )

    # Derive emotional job (how they want to feel)
    emotional_job = (
        f"{target_user} want to feel confident and in control when they {feature_or_problem}. "
        f"Current alternatives ({', '.join(current_alternatives[:2])}) likely leave them feeling "
        f"uncertain or overwhelmed. The emotional win: reducing anxiety around this decision."
    )

    # Derive social job (how they want to be perceived)
    social_job = (
        f"{target_user} want to be seen as strategic and data-driven by their peers and leadership. "
        f"Successfully {feature_or_problem.rstrip('.')} signals competence and builds trust with stakeholders."
    )

    # Hiring criteria — what makes them pick a solution
    hiring_criteria = [
        f"Does it directly help with: {desired_outcomes[0]}?" if desired_outcomes else "Does it solve the core problem?",
        f"Is it better than the current approach ({current_alternatives[0]})?" if current_alternatives else "Is it better than doing nothing?",
        "Can they start using it quickly without a steep learning curve?",
        "Does it produce outputs they can share with stakeholders?",
    ]

    # Firing triggers — what makes them abandon a solution
    firing_triggers = [
        f"The tool doesn't actually improve on {current_alternatives[0]}" if current_alternatives else "It's harder than the old way",
        "It requires too much manual input for the value delivered",
        "The output isn't credible enough to share with leadership",
        "It adds a new step without removing an old one",
    ]

    # Switching barriers
    switching_barriers = []
    if current_alternatives:
        switching_barriers.append(
            f"Familiarity with {current_alternatives[0]} — teams have workflows built around it"
        )
    switching_barriers.extend([
        "Time investment to learn a new approach",
        "Risk of looking foolish if the new tool doesn't work out",
        "Organizational inertia ('this is how we've always done it')",
    ])

    # Analysis
    alt_count = len(current_alternatives)
    outcome_count = len(desired_outcomes)
    analysis = (
        f"**Job context:** {target_user} trying to {feature_or_problem}.\n\n"
        f"They currently use **{alt_count} alternative(s)** ({', '.join(current_alternatives)}), "
        f"which suggests this is a real, recurring job — people are already hiring imperfect solutions.\n\n"
        f"The **{outcome_count} desired outcome(s)** point to both functional needs "
        f"({desired_outcomes[0] if desired_outcomes else 'core task'}) and emotional/social needs "
        f"(confidence, credibility).\n\n"
        f"The strongest signal: users have alternatives but none fully satisfy the job. "
        f"This is a classic underserved job — high frequency, available alternatives, low satisfaction."
    )

    # Next steps
    next_steps = [
        "Interview 5 target users and ask: 'Walk me through the last time you had to do this. What was hard?'",
        f"Audit the top alternative ({current_alternatives[0] if current_alternatives else 'current approach'}) — where exactly does it fall short?",
        "Prototype the minimum version that nails the functional job, then test if the emotional win follows.",
    ]
    if outcome_count > 2:
        next_steps.append(f"You have {outcome_count} desired outcomes — force-rank them. Build for #1 first.")
    next_steps.append("Write a 'job story' for your backlog: 'When [situation], I want [motivation], so I can [outcome].'")
    next_steps = next_steps[:5]

    # Confidence
    if alt_count >= 2 and outcome_count >= 2:
        conf = "High"
        conf_rationale = "Multiple alternatives and outcomes suggest a well-understood job with clear signal."
    elif alt_count >= 1 and outcome_count >= 1:
        conf = "Medium"
        conf_rationale = "Basic job structure is clear, but more user research would strengthen the analysis."
    else:
        conf = "Low"
        conf_rationale = "Limited input — the job may not be well-defined yet. More discovery needed."

    # Pressure-test questions
    questions = [
        "Is this the real job, or a symptom of a bigger job? (e.g., 'prioritize features' might be part of 'make better product decisions')",
        f"Are {target_user} actually dissatisfied with {current_alternatives[0] if current_alternatives else 'current solutions'}, or is this a 'nice to have'?",
        "If you built this tomorrow, would users switch? What's the activation energy required?",
    ]

    output = JtbdOutput(
        job_statement=job_statement,
        functional_job=functional_job,
        emotional_job=emotional_job,
        social_job=social_job,
        hiring_criteria=hiring_criteria,
        firing_triggers=firing_triggers,
        switching_barriers=switching_barriers,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
