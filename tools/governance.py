"""Governance tools — Decision logging and structured documentation.

These tools help product teams capture decisions in a structured format
that future-you will actually thank present-you for writing down.
"""

from typing import Annotated
from pydantic import Field

from app import mcp
from schemas.models import DecisionLogEntryOutput


# ---------------------------------------------------------------------------
# Decision Log Entry
# ---------------------------------------------------------------------------

@mcp.tool
def decision_log_entry(
    decision_title: Annotated[str, Field(
        description="Short, clear title for the decision (e.g., 'Use PostgreSQL over MongoDB for user data')"
    )],
    decision_date: Annotated[str, Field(
        description="When the decision was made (e.g., '2026-03-28')"
    )],
    decision_maker: Annotated[str, Field(
        description="Who made or owns this decision (e.g., 'Sarah Chen, Head of Product')"
    )],
    context: Annotated[str, Field(
        description="Why did this decision need to be made? What was the situation? (e.g., 'Needed to choose a database before sprint 3. Data model has complex relationships and we need ACID transactions.')"
    )],
    decision: Annotated[str, Field(
        description="What was decided? Be specific. (e.g., 'We will use PostgreSQL as our primary database, hosted on Railway.')"
    )],
    alternatives_considered: Annotated[list[str], Field(
        description="What other options were evaluated? (e.g., ['MongoDB — flexible schema but weak joins', 'DynamoDB — scalable but vendor lock-in'])"
    )],
    rationale: Annotated[str, Field(
        description="Why this option over the alternatives? (e.g., 'PostgreSQL gives us ACID transactions, mature tooling, and the team has deep experience with it.')"
    )],
    expected_consequences: Annotated[list[str], Field(
        description="What are the expected consequences — both positive and negative? (e.g., ['Faster development due to team experience', 'May need to shard if we exceed 10M rows'])"
    )],
    status: Annotated[str, Field(
        description="Current status: 'Decided', 'Revisiting', or 'Superseded'",
        pattern="^(Decided|Revisiting|Superseded)$",
    )] = "Decided",
) -> str:
    """Structure a product decision for archiving and future reference.

    Creates a well-structured decision record following the ADR (Architecture
    Decision Record) pattern. Good decision logs capture not just WHAT was
    decided, but WHY — so future teams understand the reasoning and know
    when to revisit.
    """

    # Validate status
    valid_statuses = ("Decided", "Revisiting", "Superseded")
    if status not in valid_statuses:
        status = "Decided"

    # Generate revisit conditions based on context and decision
    revisit_conditions = []

    # Scale-related revisit triggers
    scale_words = ("scale", "growth", "users", "traffic", "data", "volume", "load")
    if any(w in context.lower() or w in decision.lower() for w in scale_words):
        revisit_conditions.append("If user/data volume exceeds 10x current projections.")

    # Tech-related revisit triggers
    tech_words = ("technology", "framework", "library", "tool", "database", "api", "platform")
    if any(w in context.lower() or w in decision.lower() for w in tech_words):
        revisit_conditions.append("If the chosen technology reaches end-of-life or a significantly better alternative emerges.")

    # Cost-related revisit triggers
    cost_words = ("cost", "price", "budget", "spend", "expense", "cheap", "afford")
    if any(w in context.lower() or w in decision.lower() for w in cost_words):
        revisit_conditions.append("If costs exceed 150% of initial projections.")

    # Team-related revisit triggers
    team_words = ("team", "hire", "expertise", "skill", "resource", "capacity")
    if any(w in context.lower() or w in decision.lower() for w in team_words):
        revisit_conditions.append("If team composition changes significantly (key departures, new hires with different expertise).")

    # Always include general revisit conditions
    revisit_conditions.append("If the original context or constraints change materially.")
    if len(revisit_conditions) < 2:
        revisit_conditions.append("At the next quarterly planning review — does this decision still serve the strategy?")

    revisit_conditions = revisit_conditions[:5]

    # Analysis
    alt_count = len(alternatives_considered)
    consequence_count = len(expected_consequences)
    positive_consequences = [c for c in expected_consequences if not any(neg in c.lower() for neg in ("risk", "downside", "negative", "may need", "limitation", "concern", "issue", "problem"))]
    negative_consequences = [c for c in expected_consequences if any(neg in c.lower() for neg in ("risk", "downside", "negative", "may need", "limitation", "concern", "issue", "problem"))]

    analysis = (
        f"**Decision: {decision_title}**\n"
        f"**Made by:** {decision_maker} on {decision_date}\n"
        f"**Status:** {status}\n\n"
        f"**{alt_count} alternative(s)** were considered, and **{consequence_count} consequence(s)** "
        f"were identified ({len(positive_consequences)} positive, {len(negative_consequences)} risks/downsides).\n\n"
    )

    if alt_count == 0:
        analysis += "No alternatives were listed — this may indicate a forced choice or insufficient exploration of options.\n"
    elif alt_count == 1:
        analysis += "Only one alternative was considered — consider whether other options were overlooked.\n"
    else:
        analysis += f"{alt_count} alternatives evaluated — good decision hygiene.\n"

    if not negative_consequences:
        analysis += "\nNo downside consequences were listed. Every decision has trade-offs — consider what you might be missing."
    else:
        analysis += f"\n{len(negative_consequences)} risk(s) identified — document mitigation strategies for each."

    # Next steps
    next_steps = [
        "Store this decision in your team's decision log (Notion, Confluence, or a git-tracked ADR folder).",
        "Share with the team — decisions made in isolation tend to get revisited unnecessarily.",
    ]
    if negative_consequences:
        next_steps.append(f"Create mitigation plans for the {len(negative_consequences)} identified risk(s).")
    if status == "Decided":
        next_steps.append(f"Set a calendar reminder to review this decision when: '{revisit_conditions[0]}'")
    if status == "Revisiting":
        next_steps.append("Gather new data since the original decision. What has changed? Does the original rationale still hold?")
    next_steps = next_steps[:5]
    if len(next_steps) < 2:
        next_steps.append("Link this decision to the relevant project or initiative for easy discovery.")

    # Confidence
    if alt_count >= 2 and len(rationale.split()) >= 10 and consequence_count >= 2:
        conf = "High"
        conf_rationale = "Multiple alternatives evaluated, clear rationale provided, and consequences mapped."
    elif alt_count >= 1 and rationale.strip():
        conf = "Medium"
        conf_rationale = "Rationale provided but the analysis could be deeper. Consider more alternatives or consequences."
    else:
        conf = "Low"
        conf_rationale = "Limited alternatives or rationale. This decision may not be well-examined."

    # Pressure-test questions
    questions = [
        "If this decision turns out to be wrong in 6 months, what will the early warning signs be?",
        f"Did {decision_maker} have the right information and authority to make this call? Who else should have been consulted?",
    ]
    if alt_count <= 1:
        questions.append("Were there really no other options, or was this a default choice disguised as a decision?")
    else:
        questions.append("Would someone who disagreed with this decision say the alternatives were fairly evaluated?")

    output = DecisionLogEntryOutput(
        decision_title=decision_title,
        decision_date=decision_date,
        decision_maker=decision_maker,
        status=status,
        context=context,
        decision=decision,
        alternatives_considered=alternatives_considered,
        rationale=rationale,
        consequences=expected_consequences,
        revisit_conditions=revisit_conditions,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
