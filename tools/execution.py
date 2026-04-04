"""Execution tools — OKR generator and initiative scoping.

These tools help product teams translate strategy into executable plans
with measurable outcomes and clear accountability.
"""

from typing import Annotated
from pydantic import Field

from app import mcp
from schemas.models import KeyResult, OkrGeneratorOutput, Initiative, InitiativeScoperOutput


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


# ---------------------------------------------------------------------------
# Initiative Scoper
# ---------------------------------------------------------------------------

@mcp.tool
def initiative_scoper(
    strategic_goal: Annotated[str, Field(
        description="The strategic goal to break down (e.g., 'Launch AI-powered analytics dashboard for enterprise customers')"
    )],
    time_horizon: Annotated[str, Field(
        description="Available time for execution (e.g., 'Q2 2026', '8 weeks', '90 days')"
    )],
    team_size: Annotated[int, Field(
        description="Number of people available to work on this (e.g., 3)",
        ge=1,
    )],
    constraints: Annotated[list[str], Field(
        description="Known constraints or limitations (e.g., ['No backend engineer until April', 'Must use existing auth system', 'Budget limited to $5K/month'])"
    )],
    known_dependencies: Annotated[list[str], Field(
        description="Known external dependencies (e.g., ['API access from partner', 'Design system update', 'Legal review for data handling']). Pass empty [] if none."
    )],
) -> str:
    """Break a strategic goal into scoped initiatives with dependencies.

    Takes a high-level goal and decomposes it into concrete initiatives,
    each with effort estimates, priorities, dependencies, and success criteria.
    Identifies the critical path and recommended execution sequence.
    """

    goal_lower = strategic_goal.lower()

    # Generate initiatives based on goal analysis
    initiatives: list[Initiative] = []

    # Discovery/research initiative (almost always needed)
    initiatives.append(Initiative(
        name="Discovery & Requirements",
        description=f"Validate assumptions, define detailed requirements, and map user needs for: {strategic_goal}",
        priority="P0 — Must have",
        estimated_effort="1-2 weeks",
        dependencies=[],
        success_criteria="Clear requirements document, validated user needs, and aligned team on scope.",
    ))

    # Technical foundation
    needs_tech_setup = any(w in goal_lower for w in ("build", "launch", "develop", "create", "implement", "platform", "product", "app", "dashboard", "system"))
    if needs_tech_setup:
        initiatives.append(Initiative(
            name="Technical Architecture & Setup",
            description="Design the technical architecture, set up infrastructure, and establish development workflow.",
            priority="P0 — Must have",
            estimated_effort="1-2 weeks",
            dependencies=["Discovery & Requirements"],
            success_criteria="Architecture documented, dev environment running, CI/CD pipeline configured.",
        ))

    # Core build
    core_deps = ["Discovery & Requirements", "Technical Architecture & Setup"] if needs_tech_setup else ["Discovery & Requirements"]
    initiatives.append(Initiative(
        name="Core Feature Build",
        description=f"Build the minimum viable version that delivers the core value: {strategic_goal}",
        priority="P0 — Must have",
        estimated_effort=f"{'3-4 weeks' if team_size <= 2 else '2-3 weeks'}",
        dependencies=core_deps,
        success_criteria="Core functionality working end-to-end, passing basic QA, and ready for internal testing.",
    ))

    # Integration initiative if relevant
    if any(w in goal_lower for w in ("integrat", "api", "connect", "sync", "partner")):
        initiatives.append(Initiative(
            name="Integration Development",
            description="Build and test integrations with external systems or APIs.",
            priority="P0 — Must have",
            estimated_effort="1-2 weeks",
            dependencies=["Core Feature Build"],
            success_criteria="All required integrations working with error handling and retry logic.",
        ))

    # Testing & QA
    initiatives.append(Initiative(
        name="Testing & Quality Assurance",
        description="Comprehensive testing including edge cases, performance, and user acceptance testing.",
        priority="P0 — Must have",
        estimated_effort="1-2 weeks",
        dependencies=["Core Feature Build"],
        success_criteria="All critical paths tested, no P0 bugs, performance meets targets.",
    ))

    # Go-to-market if launching
    if any(w in goal_lower for w in ("launch", "release", "ship", "go live", "beta", "customers", "users")):
        initiatives.append(Initiative(
            name="Go-to-Market Preparation",
            description="Prepare launch materials: documentation, marketing assets, support processes, and onboarding flows.",
            priority="P1 — Should have",
            estimated_effort="1-2 weeks",
            dependencies=["Core Feature Build"],
            success_criteria="Landing page live, onboarding flow tested, support documentation complete.",
        ))

    # Analytics & monitoring
    if any(w in goal_lower for w in ("analytics", "metric", "data", "dashboard", "monitor")):
        initiatives.append(Initiative(
            name="Analytics & Monitoring Setup",
            description="Implement tracking, dashboards, and alerting to measure success post-launch.",
            priority="P1 — Should have",
            estimated_effort="1 week",
            dependencies=["Core Feature Build"],
            success_criteria="Key metrics tracked, dashboards accessible, alerts configured for critical thresholds.",
        ))

    # Add constraint-driven initiatives
    for dep in known_dependencies:
        if dep.strip():
            initiatives.append(Initiative(
                name=f"Resolve: {dep.strip()}",
                description=f"Address external dependency: {dep.strip()}. This must be resolved before dependent work can proceed.",
                priority="P0 — Must have",
                estimated_effort="Varies — depends on external party",
                dependencies=[],
                success_criteria=f"'{dep.strip()}' is fully resolved and unblocking downstream work.",
            ))

    # Polish/enhancement initiative
    initiatives.append(Initiative(
        name="Polish & Enhancement Pass",
        description="UX improvements, performance optimization, and addressing feedback from testing.",
        priority="P2 — Nice to have",
        estimated_effort="1 week",
        dependencies=["Testing & Quality Assurance"],
        success_criteria="Top 5 feedback items addressed, UX reviewed and polished.",
    ))

    # Build recommended sequence (topological sort-ish by dependencies and priority)
    completed: set[str] = set()
    sequence: list[str] = []
    remaining = list(initiatives)

    while remaining:
        # Find initiatives whose dependencies are all completed
        ready = [i for i in remaining if all(d in completed for d in i.dependencies)]
        if not ready:
            # Circular dependency or missing dep — add remaining by priority
            ready = sorted(remaining, key=lambda x: x.priority)

        # Sort ready items by priority
        priority_order = {"P0 — Must have": 0, "P1 — Should have": 1, "P2 — Nice to have": 2}
        ready.sort(key=lambda x: priority_order.get(x.priority, 3))

        next_init = ready[0]
        sequence.append(next_init.name)
        completed.add(next_init.name)
        remaining.remove(next_init)

    # Critical path: longest chain of P0 dependencies
    critical_path = [i.name for i in initiatives if i.priority == "P0 — Must have"]

    # Total effort estimate
    effort_weeks_low = 0
    effort_weeks_high = 0
    for init in initiatives:
        effort_str = init.estimated_effort.lower()
        if "varies" in effort_str:
            effort_weeks_low += 1
            effort_weeks_high += 3
        elif "-" in effort_str:
            parts = effort_str.split("-")
            try:
                effort_weeks_low += int(parts[0].strip().split()[0])
                effort_weeks_high += int(parts[1].strip().split()[0])
            except (ValueError, IndexError):
                effort_weeks_low += 1
                effort_weeks_high += 2
        elif "week" in effort_str:
            try:
                num = int(effort_str.split()[0])
                effort_weeks_low += num
                effort_weeks_high += num
            except (ValueError, IndexError):
                effort_weeks_low += 1
                effort_weeks_high += 2
        else:
            effort_weeks_low += 1
            effort_weeks_high += 2

    # Parallelization factor
    parallel_factor = min(team_size, 3)  # Realistically, max 3 parallel streams
    calendar_weeks_low = max(effort_weeks_low // parallel_factor, effort_weeks_low // 2)
    calendar_weeks_high = max(effort_weeks_high // parallel_factor, effort_weeks_high // 2)

    total_effort = (
        f"{effort_weeks_low}-{effort_weeks_high} person-weeks of effort. "
        f"With {team_size} people and some parallelization, "
        f"expect ~{calendar_weeks_low}-{calendar_weeks_high} calendar weeks."
    )

    # Analysis
    p0_count = sum(1 for i in initiatives if "P0" in i.priority)
    analysis = (
        f"Broke **'{strategic_goal}'** into **{len(initiatives)} initiatives**.\n\n"
        f"- **P0 (Must have):** {p0_count} initiatives\n"
        f"- **P1 (Should have):** {sum(1 for i in initiatives if 'P1' in i.priority)}\n"
        f"- **P2 (Nice to have):** {sum(1 for i in initiatives if 'P2' in i.priority)}\n\n"
        f"**Total effort:** {total_effort}\n"
        f"**Team size:** {team_size}\n"
        f"**Time horizon:** {time_horizon}\n"
    )

    if constraints:
        analysis += f"\n**Constraints:** {'; '.join(constraints)}"

    # Next steps
    next_steps = [
        "Review and adjust the initiative breakdown with your team — add, remove, or re-scope as needed.",
        f"Start with '{sequence[0]}' immediately — it unblocks everything else.",
    ]
    if len(constraints) > 0:
        next_steps.append("Address constraints early — each unresolved constraint is a risk to the timeline.")
    next_steps.append("Set up a weekly check-in against this plan to track progress and catch slippage early.")
    next_steps.append("Identify owners for each initiative — unowned work doesn't get done.")
    next_steps = next_steps[:5]

    # Confidence
    if len(constraints) <= 2 and len(known_dependencies) <= 1:
        conf = "High"
        conf_rationale = "Manageable constraints and dependencies — this breakdown is likely achievable."
    elif len(constraints) <= 4:
        conf = "Medium"
        conf_rationale = "Multiple constraints may impact timeline — build in buffer."
    else:
        conf = "Low"
        conf_rationale = "Many constraints and dependencies increase risk of delays. Simplify scope if possible."

    # Pressure-test questions
    questions = [
        "Is the scope realistic for the time horizon and team size? What would you cut if you had half the time?",
        "Are there hidden dependencies not listed here? (Stakeholder approvals, vendor contracts, hiring needs?)",
    ]
    if team_size <= 2:
        questions.append(f"With only {team_size} people, are there initiatives that should be deferred to a later phase?")
    else:
        questions.append("Does the team have the right skills for every initiative, or are there capability gaps?")

    output = InitiativeScoperOutput(
        strategic_goal=strategic_goal,
        initiatives=initiatives,
        recommended_sequence=sequence,
        total_estimated_effort=total_effort,
        critical_path=critical_path,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
