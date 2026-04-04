"""Positioning tools — Competitive positioning and differentiation analysis.

Maps your product and competitors on a 2-axis chart to identify
threats, white space, and differentiation opportunities.
"""

import math
from typing import Annotated
from pydantic import Field

from app import mcp
from schemas.models import (
    CompetitorInput,
    ProductPosition,
    QuadrantInfo,
    CompetitivePositionOutput,
)


def _distance(p1: ProductPosition, p2: ProductPosition) -> float:
    """Euclidean distance between two positions on the map."""
    return math.sqrt((p1.x_position - p2.x_position) ** 2 + (p1.y_position - p2.y_position) ** 2)


def _quadrant_label(x: float, y: float, axis_x: str, axis_y: str) -> str:
    """Label for a quadrant based on position (midpoint = 5 on 0-10 scale)."""
    x_label = f"High {axis_x}" if x >= 5 else f"Low {axis_x}"
    y_label = f"High {axis_y}" if y >= 5 else f"Low {axis_y}"
    return f"{x_label} / {y_label}"


def _find_white_space(your_pos: ProductPosition, competitors: list[CompetitorInput]) -> list[str]:
    """Identify underserved quadrants or areas with no products."""
    all_positions = [your_pos] + competitors

    # Check each quadrant for occupancy
    quadrant_occupied: dict[str, list[str]] = {
        "high-high": [],
        "high-low": [],
        "low-high": [],
        "low-low": [],
    }

    for p in all_positions:
        x_key = "high" if p.x_position >= 5 else "low"
        y_key = "high" if p.y_position >= 5 else "low"
        quadrant_occupied[f"{x_key}-{y_key}"].append(p.name)

    white_space = []
    quadrant_labels = {
        "high-high": "top-right (high on both axes)",
        "high-low": "bottom-right (high X, low Y)",
        "low-high": "top-left (low X, high Y)",
        "low-low": "bottom-left (low on both axes)",
    }

    for key, products in quadrant_occupied.items():
        if not products:
            white_space.append(f"The {quadrant_labels[key]} quadrant is empty — potential unserved positioning.")
        elif len(products) == 1:
            white_space.append(f"The {quadrant_labels[key]} quadrant has only {products[0]} — limited competition there.")

    if not white_space:
        white_space.append("All quadrants are occupied — differentiation must come from execution, brand, or features beyond these two axes.")

    return white_space


@mcp.tool
def competitive_position(
    your_product_name: Annotated[str, Field(description="Your product or company name")],
    your_x_position: Annotated[float, Field(description="Your product's position on the X axis (0-10)", ge=0, le=10)],
    your_y_position: Annotated[float, Field(description="Your product's position on the Y axis (0-10)", ge=0, le=10)],
    axis_x_name: Annotated[str, Field(description="What the X axis represents (e.g., 'Price', 'Ease of Use', 'Feature Depth')")],
    axis_y_name: Annotated[str, Field(description="What the Y axis represents (e.g., 'Enterprise Readiness', 'Design Quality', 'Community Size')")],
    competitors: Annotated[list[dict], Field(
        description=(
            "List of competitors. Each should have: 'name' (str), "
            "'x_position' (0-10), 'y_position' (0-10), and optionally 'notes' (str)"
        ),
    )],
) -> str:
    """Map your product and competitors on a 2-axis positioning chart.

    Analyzes competitive positioning to identify your quadrant,
    nearest threats, white space opportunities, and differentiation.
    Use this when evaluating market positioning, planning launches,
    or preparing competitive strategy.
    """

    your_pos = ProductPosition(
        name=your_product_name,
        x_position=your_x_position,
        y_position=your_y_position,
    )

    # Parse competitors
    parsed_competitors: list[CompetitorInput] = []
    for c in competitors:
        comp = CompetitorInput(**c)
        parsed_competitors.append(comp)

    if not parsed_competitors:
        return '{"error": "No competitors provided. Please provide at least one competitor."}'

    # Build competitor positions for output
    competitor_positions = [
        ProductPosition(name=c.name, x_position=c.x_position, y_position=c.y_position)
        for c in parsed_competitors
    ]

    # Calculate distances and find nearest threats
    distances = [
        (c.name, _distance(your_pos, c))
        for c in parsed_competitors
    ]
    distances.sort(key=lambda d: d[1])
    nearest_threats = [
        f"{name} (distance: {dist:.1f})" for name, dist in distances[:3]
    ]

    # Build quadrant map
    all_products = [your_pos] + competitor_positions
    quadrant_products: dict[str, list[str]] = {}
    for p in all_products:
        label = _quadrant_label(p.x_position, p.y_position, axis_x_name, axis_y_name)
        if label not in quadrant_products:
            quadrant_products[label] = []
        quadrant_products[label].append(p.name)

    quadrants = []
    for label, products in quadrant_products.items():
        crowded = "crowded" if len(products) > 2 else "sparse" if len(products) == 1 else "moderate"
        quadrants.append(QuadrantInfo(
            name=label,
            products=products,
            description=f"{crowded} quadrant with {len(products)} product(s)",
        ))

    # Find white space
    white_space = _find_white_space(your_pos, parsed_competitors)

    # Your quadrant
    your_quadrant = _quadrant_label(your_pos.x_position, your_pos.y_position, axis_x_name, axis_y_name)

    # Differentiation summary
    closest_name, closest_dist = distances[0]
    if closest_dist < 1.5:
        diff_summary = (
            f"{your_product_name} is positioned very close to {closest_name} "
            f"(distance: {closest_dist:.1f}). This is a crowded position — "
            f"you'll need strong differentiation on dimensions beyond {axis_x_name} and {axis_y_name} "
            f"(e.g., brand, pricing model, integrations, support quality)."
        )
    elif closest_dist < 3:
        diff_summary = (
            f"{your_product_name} has moderate separation from {closest_name} "
            f"(distance: {closest_dist:.1f}). You have some positioning room but "
            f"should actively communicate what makes you different on {axis_x_name} and {axis_y_name}."
        )
    else:
        diff_summary = (
            f"{your_product_name} occupies a distinct position — your nearest competitor "
            f"({closest_name}) is {closest_dist:.1f} units away. This suggests a differentiated "
            f"positioning. Validate that this position aligns with where customers actually want to be."
        )

    # Analysis
    total_competitors = len(parsed_competitors)
    same_quadrant = quadrant_products.get(your_quadrant, [])
    same_quadrant_others = [p for p in same_quadrant if p != your_product_name]

    analysis = (
        f"**{your_product_name}** is positioned in the **{your_quadrant}** quadrant "
        f"on a {axis_x_name} vs. {axis_y_name} map with {total_competitors} competitor(s).\n\n"
    )

    if same_quadrant_others:
        analysis += (
            f"You share this quadrant with **{', '.join(same_quadrant_others)}** — "
            f"direct competition on both axes. Differentiation is critical here.\n\n"
        )
    else:
        analysis += "You're the **only product** in your quadrant — a potentially strong position if the market values it.\n\n"

    analysis += (
        f"Nearest threat: **{closest_name}** at distance {closest_dist:.1f}. "
        f"{'This is dangerously close — customers may see you as interchangeable.' if closest_dist < 1.5 else 'You have some breathing room.'}"
    )

    # Next steps
    next_steps = [
        f"Validate your positioning: do customers actually perceive you as {your_quadrant.lower()}?",
        f"Analyze {closest_name} closely — what's their messaging strategy on {axis_x_name} and {axis_y_name}?",
    ]
    if any("empty" in ws.lower() for ws in white_space):
        next_steps.append("Explore the empty quadrants — is there unmet demand there, or is it empty for a reason?")
    if closest_dist < 1.5:
        next_steps.append("Urgently find a third dimension to differentiate on — brand, pricing, speed, support.")
    next_steps.append("Share this map with your team and debate whether you should move your position or defend it.")
    next_steps = next_steps[:5]

    # Confidence
    if total_competitors >= 3:
        conf = "High"
        conf_rationale = f"With {total_competitors} competitors mapped, the competitive landscape is well-represented."
    elif total_competitors >= 2:
        conf = "Medium"
        conf_rationale = "Decent view of the landscape but may be missing key players."
    else:
        conf = "Low"
        conf_rationale = "Only one competitor mapped — the positioning analysis is incomplete."

    # Pressure-test questions
    questions = [
        f"Are {axis_x_name} and {axis_y_name} the axes your customers actually care about when choosing?",
        f"Is your self-assessed position ({your_x_position}, {your_y_position}) backed by customer perception data?",
    ]
    if total_competitors < 4:
        questions.append(f"Are there competitors you've missed? {total_competitors} feels like an incomplete map.")
    else:
        questions.append("Would new entrants (startups, adjacent products) change this map significantly?")

    output = CompetitivePositionOutput(
        axis_x=axis_x_name,
        axis_y=axis_y_name,
        your_position=your_pos,
        competitors=competitor_positions,
        quadrants=quadrants,
        nearest_threats=nearest_threats,
        white_space=white_space,
        differentiation_summary=diff_summary,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
