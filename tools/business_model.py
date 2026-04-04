"""Business model tools — BMC review, TAM/SAM/SOM, and pricing strategy.

These tools help product teams evaluate, size, and price their business models
using structured frameworks that turn hand-wavy strategy into concrete analysis.
"""

from typing import Annotated
from pydantic import Field

from app import mcp
from schemas.models import (
    BmcComponentAssessment,
    BusinessModelReviewOutput,
    MarketTier,
    TamSamSomOutput,
    CompetitorPricing,
    PricingStrategyOutput,
)


# ---------------------------------------------------------------------------
# Business Model Canvas Review
# ---------------------------------------------------------------------------

_BMC_COMPONENTS = [
    "customer_segments",
    "value_propositions",
    "channels",
    "customer_relationships",
    "revenue_streams",
    "key_resources",
    "key_activities",
    "key_partnerships",
    "cost_structure",
]

_BMC_LABELS = {
    "customer_segments": "Customer Segments",
    "value_propositions": "Value Propositions",
    "channels": "Channels",
    "customer_relationships": "Customer Relationships",
    "revenue_streams": "Revenue Streams",
    "key_resources": "Key Resources",
    "key_activities": "Key Activities",
    "key_partnerships": "Key Partnerships",
    "cost_structure": "Cost Structure",
}

_BMC_GUIDANCE = {
    "customer_segments": {
        "strong": "Well-defined segments with clear characteristics and needs.",
        "weak": "Segments are too broad or undefined. Who exactly are you serving? Be specific about demographics, behaviors, and needs.",
        "missing": "No customer segments defined. This is foundational — everything else depends on knowing who you serve.",
    },
    "value_propositions": {
        "strong": "Clear, differentiated value that connects to customer needs.",
        "weak": "Value proposition is generic or doesn't clearly differentiate from alternatives. What specific problem do you solve better than anyone?",
        "missing": "No value proposition defined. Without this, there's no reason for customers to choose you.",
    },
    "channels": {
        "strong": "Multiple channels aligned with how customers prefer to buy and engage.",
        "weak": "Channels are unclear or may not match customer behavior. How do your customers actually discover and purchase solutions?",
        "missing": "No channels defined. How will customers find and purchase your product?",
    },
    "customer_relationships": {
        "strong": "Relationship model fits customer expectations and supports retention.",
        "weak": "Relationship approach is vague. Are you self-service, high-touch, community-driven? Be explicit.",
        "missing": "No customer relationship model defined. How will you acquire, retain, and grow accounts?",
    },
    "revenue_streams": {
        "strong": "Clear revenue model with defined pricing and willingness-to-pay evidence.",
        "weak": "Revenue model exists but pricing logic or willingness-to-pay is unclear. What are customers actually paying for?",
        "missing": "No revenue streams defined. How does this make money?",
    },
    "key_resources": {
        "strong": "Resources are well-identified and map to delivering the value proposition.",
        "weak": "Resources listed are generic. What specific assets, IP, or capabilities give you an advantage?",
        "missing": "No key resources defined. What do you need to deliver the value proposition?",
    },
    "key_activities": {
        "strong": "Activities clearly map to delivering value and operating the business.",
        "weak": "Activities are too high-level. What are the specific things you must do well to succeed?",
        "missing": "No key activities defined. What must you actually do to deliver your value proposition?",
    },
    "key_partnerships": {
        "strong": "Partnerships are strategic and fill clear capability gaps.",
        "weak": "Partnerships are mentioned but the strategic rationale is unclear. What do partners provide that you can't do yourself?",
        "missing": "No partnerships defined. Can you deliver everything yourself, or are there gaps?",
    },
    "cost_structure": {
        "strong": "Costs are well-understood with clear fixed vs. variable breakdown.",
        "weak": "Cost structure is vague. What are your biggest cost drivers? Fixed vs. variable?",
        "missing": "No cost structure defined. What does it cost to operate this business model?",
    },
}


def _assess_component(component: str, value: str) -> BmcComponentAssessment:
    """Assess a single BMC component."""
    label = _BMC_LABELS[component]
    guidance = _BMC_GUIDANCE[component]

    if not value or value.strip() == "":
        return BmcComponentAssessment(
            component=label,
            provided="(not provided)",
            strength="Missing",
            feedback=guidance["missing"],
        )

    value = value.strip()
    word_count = len(value.split())

    # Simple heuristic: longer, more specific answers tend to be better-defined
    if word_count >= 15 and "," in value:
        strength = "Strong"
        feedback = guidance["strong"]
    elif word_count >= 5:
        strength = "Adequate"
        feedback = f"Defined but could be sharper. {guidance['weak']}"
    else:
        strength = "Weak"
        feedback = guidance["weak"]

    return BmcComponentAssessment(
        component=label,
        provided=value,
        strength=strength,
        feedback=feedback,
    )


@mcp.tool
def business_model_review(
    product_name: Annotated[str, Field(description="Name of the product or business")],
    customer_segments: Annotated[str, Field(
        description="Who are your customers? Be specific (e.g., 'B2B SaaS product managers at companies with 50-500 employees')"
    )] = "",
    value_propositions: Annotated[str, Field(
        description="What value do you deliver? What problem do you solve? (e.g., 'Reduce feature prioritization time from days to hours with AI-powered RICE scoring')"
    )] = "",
    channels: Annotated[str, Field(
        description="How do customers find and buy your product? (e.g., 'Product Hunt launch, SEO content, LinkedIn thought leadership, direct sales')"
    )] = "",
    customer_relationships: Annotated[str, Field(
        description="What type of relationship? (e.g., 'Self-serve freemium with upgrade prompts, community Slack, quarterly business reviews for enterprise')"
    )] = "",
    revenue_streams: Annotated[str, Field(
        description="How do you make money? (e.g., 'Freemium SaaS — free tier, $49/mo team, $199/mo enterprise, annual discount')"
    )] = "",
    key_resources: Annotated[str, Field(
        description="What key assets do you need? (e.g., 'AI/ML models, product strategy IP, engineering team, customer data')"
    )] = "",
    key_activities: Annotated[str, Field(
        description="What must you do well? (e.g., 'Model training, framework research, content marketing, customer onboarding')"
    )] = "",
    key_partnerships: Annotated[str, Field(
        description="Who are your key partners? (e.g., 'Anthropic (AI provider), Jira/Linear (integrations), product influencers')"
    )] = "",
    cost_structure: Annotated[str, Field(
        description="What are your main costs? (e.g., 'AI API costs (variable), engineering salaries (fixed), hosting (variable), marketing (fixed)')"
    )] = "",
) -> str:
    """Review a business model using the Business Model Canvas framework.

    Assesses each of the 9 BMC components for clarity, completeness, and coherence.
    Identifies gaps, strengths, and how well the components fit together.
    Provide as many components as you can — missing ones will be flagged.
    """

    inputs = {
        "customer_segments": customer_segments,
        "value_propositions": value_propositions,
        "channels": channels,
        "customer_relationships": customer_relationships,
        "revenue_streams": revenue_streams,
        "key_resources": key_resources,
        "key_activities": key_activities,
        "key_partnerships": key_partnerships,
        "cost_structure": cost_structure,
    }

    # Assess each component
    assessments = [_assess_component(comp, inputs[comp]) for comp in _BMC_COMPONENTS]

    # Calculate health metrics
    strengths_map = {"Strong": 3, "Adequate": 2, "Weak": 1, "Missing": 0}
    scores = [strengths_map[a.strength] for a in assessments]
    avg_score = sum(scores) / len(scores)

    critical_gaps = [a.component for a in assessments if a.strength in ("Missing", "Weak")]
    strongest = [a.component for a in assessments if a.strength == "Strong"]
    missing_count = sum(1 for a in assessments if a.strength == "Missing")
    weak_count = sum(1 for a in assessments if a.strength == "Weak")

    # Overall health
    if avg_score >= 2.5 and missing_count == 0:
        overall_health = "Strong"
    elif avg_score >= 1.8 and missing_count <= 1:
        overall_health = "Viable"
    elif missing_count <= 3:
        overall_health = "Gaps Present"
    else:
        overall_health = "Incomplete"

    # Coherence analysis
    coherence_parts = []
    has_segments = bool(customer_segments.strip())
    has_value = bool(value_propositions.strip())
    has_revenue = bool(revenue_streams.strip())
    has_channels = bool(channels.strip())

    if has_segments and has_value:
        coherence_parts.append("Customer segments and value propositions are both defined — check that the value directly addresses segment needs.")
    if has_value and has_revenue:
        coherence_parts.append("Value proposition and revenue streams are both present — ensure pricing reflects the value delivered.")
    if has_channels and has_segments:
        coherence_parts.append("Channels are defined alongside segments — verify these channels actually reach your target customers.")
    if not has_segments or not has_value:
        coherence_parts.append("Cannot fully assess coherence — customer segments and value propositions are the foundation. Define these first.")

    coherence_notes = " ".join(coherence_parts) if coherence_parts else "Limited components provided — coherence assessment requires more inputs."

    # Analysis
    filled_count = 9 - missing_count
    analysis = (
        f"**{product_name}** business model review: **{filled_count}/9** components provided, "
        f"overall health is **{overall_health}**.\n\n"
    )

    if strongest:
        analysis += f"Strongest areas: **{', '.join(strongest)}**.\n"
    if critical_gaps:
        analysis += f"Needs work: **{', '.join(critical_gaps)}**.\n"

    analysis += f"\n{weak_count} weak and {missing_count} missing component(s) identified."

    # Next steps
    next_steps = []
    if missing_count > 0:
        top_missing = [a.component for a in assessments if a.strength == "Missing"][:2]
        next_steps.append(f"Fill in missing components first: {', '.join(top_missing)}.")
    if weak_count > 0:
        top_weak = [a.component for a in assessments if a.strength == "Weak"][:2]
        next_steps.append(f"Strengthen weak components: {', '.join(top_weak)} — add specifics and evidence.")
    if has_segments and has_value:
        next_steps.append("Validate the segment-value fit with 5 customer interviews this month.")
    next_steps.append("Share this canvas with your team and iterate — a BMC is a living document, not a one-time exercise.")
    if has_revenue:
        next_steps.append("Stress-test your revenue model: what happens if your main revenue stream underperforms by 50%?")
    next_steps = next_steps[:5]
    if len(next_steps) < 2:
        next_steps.append("Revisit this canvas monthly as your understanding of the business evolves.")

    # Confidence
    if filled_count >= 7 and avg_score >= 2.0:
        conf = "High"
        conf_rationale = f"{filled_count}/9 components provided with reasonable depth — solid basis for assessment."
    elif filled_count >= 5:
        conf = "Medium"
        conf_rationale = f"{filled_count}/9 components provided — directionally useful but gaps limit the analysis."
    else:
        conf = "Low"
        conf_rationale = f"Only {filled_count}/9 components provided — too many gaps for a reliable assessment."

    # Pressure-test questions
    questions = [
        "Is your value proposition truly differentiated, or could a competitor describe themselves the same way?",
        "Do your revenue streams cover your cost structure with healthy margins? Have you modeled this?",
    ]
    if has_segments:
        questions.append("Have you actually talked to people in your customer segments, or are these assumptions?")
    else:
        questions.append("Who is your customer? Until you define segments, everything else is guesswork.")

    output = BusinessModelReviewOutput(
        product_name=product_name,
        component_assessments=assessments,
        overall_health=overall_health,
        critical_gaps=critical_gaps,
        strongest_elements=strongest,
        coherence_notes=coherence_notes,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# TAM / SAM / SOM
# ---------------------------------------------------------------------------

def _format_usd(amount: float) -> str:
    """Format a dollar amount with appropriate suffix."""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,.0f}"


@mcp.tool
def tam_sam_som(
    product_name: Annotated[str, Field(description="Name of your product or business")],
    industry: Annotated[str, Field(
        description="The industry or market category (e.g., 'Project Management Software', 'AI-powered HR Tech')"
    )],
    total_market_size_usd: Annotated[float, Field(
        description="Estimated total market size in USD (the entire industry). Use annual revenue figures. (e.g., 7000000000 for $7B)",
        gt=0,
    )],
    target_segment_pct: Annotated[float, Field(
        description="What percentage of TAM is your addressable segment? (e.g., 15 for 15%). Consider geography, company size, and use case fit.",
        gt=0, le=100,
    )],
    realistic_capture_pct: Annotated[float, Field(
        description="What percentage of SAM can you realistically capture in 2-3 years? (e.g., 3 for 3%). Be honest.",
        gt=0, le=100,
    )],
    avg_revenue_per_customer_usd: Annotated[float, Field(
        description="Average annual revenue per customer in USD (e.g., 2400 for $200/month)",
        gt=0,
    )],
    estimated_target_customers: Annotated[int, Field(
        description="Estimated number of potential customers in your serviceable segment",
        gt=0,
    )],
    geographic_scope: Annotated[str, Field(
        description="Geographic scope of your target market (e.g., 'Global', 'North America', 'MENA region')"
    )] = "Global",
) -> str:
    """Estimate market size using the TAM/SAM/SOM framework.

    TAM = Total Addressable Market (the entire pie)
    SAM = Serviceable Addressable Market (the slice you could serve)
    SOM = Serviceable Obtainable Market (the slice you can realistically capture)

    Uses a hybrid approach: top-down for TAM, bottom-up validation for SAM/SOM.
    """

    # Calculate tiers
    tam = total_market_size_usd
    sam = tam * (target_segment_pct / 100)
    som = sam * (realistic_capture_pct / 100)

    # Bottom-up validation for SOM
    bottom_up_som = avg_revenue_per_customer_usd * estimated_target_customers * (realistic_capture_pct / 100)

    tiers = [
        MarketTier(
            tier="TAM",
            estimate_usd=_format_usd(tam),
            reasoning=(
                f"The total {industry} market is estimated at {_format_usd(tam)} annually. "
                f"This represents all potential revenue if you had 100% market share with zero constraints."
            ),
        ),
        MarketTier(
            tier="SAM",
            estimate_usd=_format_usd(sam),
            reasoning=(
                f"{target_segment_pct}% of the TAM is serviceable based on your geographic scope ({geographic_scope}), "
                f"target customer profile, and product capabilities. "
                f"This is the segment you could theoretically serve with your current product."
            ),
        ),
        MarketTier(
            tier="SOM",
            estimate_usd=_format_usd(som),
            reasoning=(
                f"{realistic_capture_pct}% of SAM is a realistic capture target over 2-3 years. "
                f"Top-down: {_format_usd(som)}. Bottom-up validation ({estimated_target_customers:,} customers × "
                f"{_format_usd(avg_revenue_per_customer_usd)}/yr × {realistic_capture_pct}%): {_format_usd(bottom_up_som)}. "
                f"{'These estimates are aligned.' if abs(som - bottom_up_som) / max(som, 1) < 0.5 else 'There is a significant gap between top-down and bottom-up — investigate which is more realistic.'}"
            ),
        ),
    ]

    # Methodology
    methodology = (
        "Hybrid approach: TAM uses top-down industry sizing. SAM applies your segment filter (geography, customer profile, use case). "
        "SOM uses both top-down (% of SAM) and bottom-up (customer count × ARPC × capture rate) for cross-validation."
    )

    # Key assumptions
    key_assumptions = [
        f"The total {industry} market is {_format_usd(tam)} — verify this against recent analyst reports (Gartner, Statista, CB Insights).",
        f"Your serviceable segment is {target_segment_pct}% of the total market — based on {geographic_scope} scope and product fit.",
        f"You can capture {realistic_capture_pct}% of your serviceable market in 2-3 years.",
        f"Average revenue per customer is {_format_usd(avg_revenue_per_customer_usd)}/year — validate against actual or comparable pricing.",
    ]

    # Sanity checks
    sanity_checks = []
    som_per_customer = som / max(estimated_target_customers * (realistic_capture_pct / 100), 1)
    if som < 1_000_000:
        sanity_checks.append(f"SOM is {_format_usd(som)} — this is a small market. Ensure unit economics work at this scale.")
    elif som > 100_000_000:
        sanity_checks.append(f"SOM is {_format_usd(som)} — ambitious. Validate that your capture rate assumptions are realistic for a 2-3 year horizon.")
    else:
        sanity_checks.append(f"SOM of {_format_usd(som)} is in a reasonable range for a growth-stage product.")

    if abs(som - bottom_up_som) / max(som, 1) > 0.5:
        sanity_checks.append(
            f"Top-down SOM ({_format_usd(som)}) and bottom-up ({_format_usd(bottom_up_som)}) diverge by >50%. "
            f"Investigate: is your customer count estimate off, or is your capture rate unrealistic?"
        )
    else:
        sanity_checks.append("Top-down and bottom-up SOM estimates are reasonably aligned — good signal.")

    if realistic_capture_pct > 10:
        sanity_checks.append(f"Capturing {realistic_capture_pct}% of SAM is aggressive for most markets. Industry leaders rarely exceed 20-30%.")

    # Analysis
    analysis = (
        f"**{product_name}** market sizing in {industry} ({geographic_scope}):\n\n"
        f"- **TAM:** {_format_usd(tam)} (total industry)\n"
        f"- **SAM:** {_format_usd(sam)} ({target_segment_pct}% serviceable)\n"
        f"- **SOM:** {_format_usd(som)} ({realistic_capture_pct}% capturable in 2-3 years)\n\n"
        f"Bottom-up validation: {estimated_target_customers:,} target customers × "
        f"{_format_usd(avg_revenue_per_customer_usd)}/yr × {realistic_capture_pct}% capture = {_format_usd(bottom_up_som)}.\n\n"
    )

    if abs(som - bottom_up_som) / max(som, 1) < 0.3:
        analysis += "Top-down and bottom-up estimates are well-aligned, increasing confidence in the SOM figure."
    else:
        analysis += "There's a notable gap between top-down and bottom-up estimates — dig deeper before using these numbers in a pitch."

    # Next steps
    next_steps = [
        f"Validate the TAM figure ({_format_usd(tam)}) against 2-3 independent sources (analyst reports, industry associations).",
        f"Refine the SOM by listing your first 50-100 target accounts to make the bottom-up estimate concrete.",
    ]
    if realistic_capture_pct > 5:
        next_steps.append(f"Pressure-test the {realistic_capture_pct}% capture rate — model the sales velocity needed to hit this in 2-3 years.")
    next_steps.append("Build a sensitivity model: what if TAM is 30% smaller or capture rate is half what you expect?")
    next_steps.append("Use this sizing to set revenue targets: SOM should inform your 3-year revenue goal, not TAM.")
    next_steps = next_steps[:5]

    # Confidence
    if abs(som - bottom_up_som) / max(som, 1) < 0.3 and realistic_capture_pct <= 10:
        conf = "High"
        conf_rationale = "Top-down and bottom-up estimates align and capture rate is conservative."
    elif abs(som - bottom_up_som) / max(som, 1) < 0.5:
        conf = "Medium"
        conf_rationale = "Estimates are in the right ballpark but the gap between approaches suggests room for refinement."
    else:
        conf = "Low"
        conf_rationale = "Significant divergence between top-down and bottom-up, or aggressive assumptions. Treat as directional."

    # Pressure-test questions
    questions = [
        f"Is the {_format_usd(tam)} TAM figure based on current market data, or is it a projection? What year is the source?",
        f"Can you name 10 real companies in your serviceable segment that would pay {_format_usd(avg_revenue_per_customer_usd)}/year?",
    ]
    if realistic_capture_pct > 5:
        questions.append(f"What specific go-to-market strategy gets you to {realistic_capture_pct}% market share in 2-3 years?")
    else:
        questions.append("Is the market growing? A small share of a growing market may be worth more than a large share of a stagnant one.")

    output = TamSamSomOutput(
        product_name=product_name,
        industry=industry,
        tiers=tiers,
        methodology=methodology,
        key_assumptions=key_assumptions,
        sanity_checks=sanity_checks,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# Pricing Strategy
# ---------------------------------------------------------------------------

@mcp.tool
def pricing_strategy(
    product_name: Annotated[str, Field(description="Name of the product")],
    product_description: Annotated[str, Field(
        description="Brief description of what the product does and who it's for"
    )],
    current_pricing: Annotated[str, Field(
        description="Current pricing model and price points (or 'Not yet priced' if new). E.g., 'Freemium — free tier, $49/mo pro, $199/mo team'"
    )],
    value_metric: Annotated[str, Field(
        description="The unit of value customers pay for (e.g., 'per seat', 'per project', 'per API call', 'per analysis run')"
    )],
    target_customer: Annotated[str, Field(
        description="Who is the buyer? (e.g., 'Head of Product at mid-market SaaS companies')"
    )],
    positioning: Annotated[str, Field(
        description="Where is the product positioned? (e.g., 'Premium — best-in-class features', 'Value — affordable alternative', 'Freemium — grow through free tier')"
    )],
    competitors: Annotated[list[dict], Field(
        description=(
            "Competitor pricing for comparison. Each should have: "
            "'name' (str), 'price_point' (str, e.g., '$29/mo'), 'model' (str, e.g., 'per seat subscription'), "
            "and optionally 'notes' (str)"
        ),
    )],
) -> str:
    """Analyze pricing strategy against positioning and competitive landscape.

    Evaluates whether your pricing aligns with your value proposition,
    how you compare to competitors, and what pricing risks to watch for.
    Recommends a pricing model and range based on the analysis.
    """

    # Parse competitors
    parsed_competitors = [CompetitorPricing(**c) for c in competitors]

    # Determine recommended model based on positioning and target
    positioning_lower = positioning.lower()
    target_lower = target_customer.lower()

    if "freemium" in positioning_lower or "free" in positioning_lower:
        recommended_model = "Freemium with tiered upgrades"
        model_reasoning = (
            "Freemium aligns with your stated positioning. The key is designing a free tier that "
            "delivers enough value to hook users while creating clear upgrade triggers."
        )
    elif "enterprise" in target_lower or "premium" in positioning_lower:
        recommended_model = "Tiered subscription with annual contracts"
        model_reasoning = (
            "Enterprise/premium positioning works best with tiered pricing that offers clear value "
            "progression. Annual contracts reduce churn and improve predictability."
        )
    elif "usage" in value_metric.lower() or "api" in value_metric.lower() or "call" in value_metric.lower():
        recommended_model = "Usage-based pricing"
        model_reasoning = (
            f"Your value metric ('{value_metric}') maps naturally to usage-based pricing. "
            "Customers pay proportionally to value received, which reduces adoption friction."
        )
    else:
        recommended_model = "Tiered subscription"
        model_reasoning = (
            "A tiered subscription model provides predictable revenue while allowing customers "
            "to self-select into the tier that matches their needs and budget."
        )

    # Analyze competitor pricing to determine range
    competitor_notes = []
    for c in parsed_competitors:
        competitor_notes.append(f"{c.name}: {c.price_point} ({c.model})")

    if "value" in positioning_lower or "affordable" in positioning_lower:
        price_position = "below the competitive midpoint"
        range_advice = "Price 20-30% below the market average to reinforce your value positioning."
    elif "premium" in positioning_lower or "best" in positioning_lower:
        price_position = "at or above the top of the competitive range"
        range_advice = "Price at or above the highest competitor to signal quality. Ensure features justify the premium."
    else:
        price_position = "at the competitive midpoint"
        range_advice = "Price near the market average and compete on features, UX, or service rather than price alone."

    recommended_price_range = (
        f"Position {price_position}. {range_advice} "
        f"Reference competitors: {'; '.join(competitor_notes[:3])}."
    )

    # Positioning alignment
    alignment_parts = []
    if "free" in current_pricing.lower() and "premium" in positioning_lower:
        alignment_parts.append("Warning: offering a free tier while positioning as premium can undermine perceived value. Consider a free trial instead of a permanent free tier.")
    if "enterprise" in target_lower and "free" in current_pricing.lower():
        alignment_parts.append("Enterprise buyers often distrust free products. Consider a pilot/POC model instead of freemium for enterprise sales.")

    alignment_parts.append(f"Your value metric ('{value_metric}') should be the anchor for pricing. Customers should feel they pay more as they get more value.")

    if parsed_competitors:
        alignment_parts.append(f"With {len(parsed_competitors)} competitors priced, your pricing should be a conscious choice relative to the market, not arbitrary.")

    positioning_alignment = " ".join(alignment_parts)

    # Pricing risks
    pricing_risks = []
    if "not yet" in current_pricing.lower() or "new" in current_pricing.lower():
        pricing_risks.append("No pricing history means no willingness-to-pay data. Run pricing conversations with 10+ potential customers before finalizing.")
    if len(parsed_competitors) < 2:
        pricing_risks.append("Limited competitor pricing data makes market positioning harder. Research more alternatives.")
    pricing_risks.append("Price anchoring: once customers see a price, it becomes the reference point. Starting too low makes it hard to raise later.")
    pricing_risks.append("Feature-tier complexity: too many tiers confuse buyers. Start with 2-3 tiers maximum.")
    if "usage" in recommended_model.lower():
        pricing_risks.append("Usage-based pricing creates revenue unpredictability. Consider a base fee + usage component for more stable revenue.")

    pricing_risks = pricing_risks[:5]

    # Analysis
    analysis = (
        f"**{product_name}** pricing analysis:\n\n"
        f"**Current:** {current_pricing}\n"
        f"**Positioning:** {positioning}\n"
        f"**Target buyer:** {target_customer}\n"
        f"**Value metric:** {value_metric}\n\n"
        f"**Recommended model:** {recommended_model}. {model_reasoning}\n\n"
        f"**Competitive context:** {len(parsed_competitors)} competitor(s) analyzed. "
        f"{'The market has established pricing norms — position deliberately against them.' if len(parsed_competitors) >= 2 else 'Limited competitive data — more research recommended.'}"
    )

    # Next steps
    next_steps = [
        "Run 10 pricing conversations with target customers: 'If this solved [problem], what would you expect to pay?'",
        f"Model 3 pricing scenarios (low/mid/high) and project revenue at each with realistic customer counts.",
    ]
    if "not yet" in current_pricing.lower():
        next_steps.append("Start with a beta price (20-30% below target) to reduce adoption friction, then raise to full price at GA.")
    else:
        next_steps.append("A/B test your current pricing page with a higher price point to test willingness-to-pay elasticity.")
    next_steps.append(f"Ensure your {value_metric} value metric scales with customer success — the best pricing grows as customers grow.")
    next_steps = next_steps[:5]

    # Confidence
    if len(parsed_competitors) >= 3 and "not yet" not in current_pricing.lower():
        conf = "High"
        conf_rationale = "Good competitive data and existing pricing provide a solid basis for analysis."
    elif len(parsed_competitors) >= 1:
        conf = "Medium"
        conf_rationale = "Some competitive data available but willingness-to-pay remains unvalidated."
    else:
        conf = "Low"
        conf_rationale = "Insufficient competitive data and no market validation. Treat as starting hypothesis."

    # Pressure-test questions
    questions = [
        f"Have you actually asked target customers ({target_customer}) what they'd pay? Or is this based on competitor copying?",
        f"Does '{value_metric}' as your value metric align with how customers perceive value? Test this assumption.",
    ]
    if len(parsed_competitors) >= 2:
        questions.append("Are the competitor prices you listed their actual prices, or just their listed prices? (Enterprise often has unlisted discounting.)")
    else:
        questions.append("Can you find at least 3 more competitor price points to build a fuller market picture?")

    output = PricingStrategyOutput(
        product_name=product_name,
        recommended_model=recommended_model,
        recommended_price_range=recommended_price_range,
        value_metric=value_metric,
        positioning_alignment=positioning_alignment,
        competitor_comparison=parsed_competitors,
        pricing_risks=pricing_risks,
        analysis=analysis,
        next_steps=next_steps,
        confidence=conf,
        confidence_rationale=conf_rationale,
        pressure_test_questions=questions,
    )

    return output.model_dump_json(indent=2)
