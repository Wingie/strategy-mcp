"""Pydantic models for all strategy-mcp tool inputs and outputs.

Every tool output extends BaseToolOutput, which enforces the standard:
- Structured analysis with reasoning
- 2-5 actionable next steps
- Confidence indicator (High/Medium/Low) with rationale
- 2-3 pressure-test questions
"""

from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared base output — every tool must return this structure
# ---------------------------------------------------------------------------

class BaseToolOutput(BaseModel):
    """Base output that every strategy tool must include."""
    analysis: str = Field(description="Structured analysis with reasoning — not just a score")
    next_steps: list[str] = Field(
        description="Specific, actionable next steps (2-5 items)",
        min_length=2,
        max_length=5,
    )
    confidence: Literal["High", "Medium", "Low"] = Field(
        description="How confident is this analysis"
    )
    confidence_rationale: str = Field(
        description="Brief explanation for the confidence level"
    )
    pressure_test_questions: list[str] = Field(
        description="Questions to challenge this analysis (2-3 items)",
        min_length=2,
        max_length=3,
    )


# ---------------------------------------------------------------------------
# RICE Score
# ---------------------------------------------------------------------------

class RiceScoreOutput(BaseToolOutput):
    """Output for the RICE scoring tool."""
    feature_name: str
    reach: int = Field(description="Users reached per quarter")
    impact: float = Field(description="Impact multiplier (0.25 / 0.5 / 1 / 2 / 3)")
    confidence_pct: int = Field(description="Confidence percentage (0-100)")
    effort: float = Field(description="Effort in person-months")
    rice_score: float = Field(description="Calculated RICE score")
    priority_tier: Literal["Critical", "High", "Medium", "Low"] = Field(
        description="Priority classification based on score"
    )
    score_breakdown: str = Field(
        description="Human-readable breakdown of the calculation"
    )


# ---------------------------------------------------------------------------
# Assumption Map
# ---------------------------------------------------------------------------

class AssumptionInput(BaseModel):
    """A single assumption to map."""
    statement: str = Field(description="The assumption statement")
    confidence_level: int = Field(
        description="How confident are we this is true (1=very uncertain, 5=very confident)",
        ge=1, le=5,
    )
    impact_level: int = Field(
        description="How much impact if this is wrong (1=low, 5=critical)",
        ge=1, le=5,
    )
    category: str = Field(
        default="General",
        description="Optional category (e.g., Market, Technical, User, Business)",
    )


class AssumptionResult(BaseModel):
    """A single assumption with its quadrant assignment."""
    statement: str
    confidence_level: int
    impact_level: int
    category: str
    quadrant: Literal["Test Now", "Monitor", "Research More", "Deprioritize"]
    urgency_score: int = Field(description="Urgency ranking (higher = more urgent)")
    recommendation: str = Field(description="What to do about this assumption")


class AssumptionMapOutput(BaseToolOutput):
    """Output for the assumption mapping tool."""
    total_assumptions: int
    quadrant_summary: dict[str, int] = Field(
        description="Count of assumptions per quadrant"
    )
    assumptions: list[AssumptionResult] = Field(
        description="All assumptions with quadrant assignments, sorted by urgency"
    )


# ---------------------------------------------------------------------------
# Jobs-to-be-Done
# ---------------------------------------------------------------------------

class JtbdOutput(BaseToolOutput):
    """Output for the JTBD analysis tool."""
    job_statement: str = Field(
        description="Canonical JTBD statement: When [situation], I want to [motivation], so I can [outcome]"
    )
    functional_job: str = Field(description="The practical task the user needs done")
    emotional_job: str = Field(description="How the user wants to feel")
    social_job: str = Field(description="How the user wants to be perceived")
    hiring_criteria: list[str] = Field(
        description="What criteria does the user use to 'hire' a solution"
    )
    firing_triggers: list[str] = Field(
        description="What would make the user 'fire' the current solution"
    )
    switching_barriers: list[str] = Field(
        description="What makes switching away from current alternatives hard"
    )


# ---------------------------------------------------------------------------
# Competitive Position
# ---------------------------------------------------------------------------

class ProductPosition(BaseModel):
    """A product's position on the competitive map."""
    name: str = Field(description="Product or company name")
    x_position: float = Field(description="Position on the X axis (0-10)")
    y_position: float = Field(description="Position on the Y axis (0-10)")


class CompetitorInput(ProductPosition):
    """A competitor entry with optional notes."""
    notes: str = Field(default="", description="Optional notes about this competitor")


class QuadrantInfo(BaseModel):
    """Info about a quadrant in the competitive map."""
    name: str
    products: list[str]
    description: str


class CompetitivePositionOutput(BaseToolOutput):
    """Output for the competitive positioning tool."""
    axis_x: str = Field(description="What the X axis represents")
    axis_y: str = Field(description="What the Y axis represents")
    your_position: ProductPosition
    competitors: list[ProductPosition]
    quadrants: list[QuadrantInfo] = Field(
        description="The four quadrants with which products fall in each"
    )
    nearest_threats: list[str] = Field(
        description="Competitors closest to your position"
    )
    white_space: list[str] = Field(
        description="Underserved areas on the map"
    )
    differentiation_summary: str = Field(
        description="Summary of your competitive differentiation"
    )


# ---------------------------------------------------------------------------
# Business Model Canvas Review (Phase 2)
# ---------------------------------------------------------------------------

class BmcComponentAssessment(BaseModel):
    """Assessment of a single BMC component."""
    component: str = Field(description="BMC component name")
    provided: str = Field(description="What was provided for this component")
    strength: Literal["Strong", "Adequate", "Weak", "Missing"] = Field(
        description="How well-defined this component is"
    )
    feedback: str = Field(description="Specific feedback on this component")


class BusinessModelReviewOutput(BaseToolOutput):
    """Output for the business model canvas review tool."""
    product_name: str
    component_assessments: list[BmcComponentAssessment] = Field(
        description="Assessment of each BMC component"
    )
    overall_health: Literal["Strong", "Viable", "Gaps Present", "Incomplete"] = Field(
        description="Overall business model health"
    )
    critical_gaps: list[str] = Field(
        description="Components that need the most attention"
    )
    strongest_elements: list[str] = Field(
        description="Components that are well-defined"
    )
    coherence_notes: str = Field(
        description="How well the components fit together"
    )


# ---------------------------------------------------------------------------
# TAM/SAM/SOM (Phase 2)
# ---------------------------------------------------------------------------

class MarketTier(BaseModel):
    """A single market tier estimate."""
    tier: Literal["TAM", "SAM", "SOM"] = Field(description="Market tier")
    estimate_usd: str = Field(description="Estimated market size in USD")
    reasoning: str = Field(description="How this estimate was derived")


class TamSamSomOutput(BaseToolOutput):
    """Output for the TAM/SAM/SOM market sizing tool."""
    product_name: str
    industry: str
    tiers: list[MarketTier] = Field(description="TAM, SAM, and SOM estimates")
    methodology: str = Field(
        description="Which estimation approach was used (top-down, bottom-up, or hybrid)"
    )
    key_assumptions: list[str] = Field(
        description="Critical assumptions behind the estimates"
    )
    sanity_checks: list[str] = Field(
        description="Reality checks on the estimates"
    )


# ---------------------------------------------------------------------------
# OKR Generator (Phase 2)
# ---------------------------------------------------------------------------

class KeyResult(BaseModel):
    """A single key result within an OKR."""
    key_result: str = Field(description="The measurable key result statement")
    metric: str = Field(description="What metric is being measured")
    baseline: str = Field(description="Current/starting value")
    target: str = Field(description="Target value to achieve")
    rationale: str = Field(description="Why this KR matters for the objective")


class OkrGeneratorOutput(BaseToolOutput):
    """Output for the OKR generator tool."""
    objective: str = Field(description="The well-formed objective statement")
    objective_quality_notes: str = Field(
        description="Assessment of objective quality (aspirational, clear, time-bound)"
    )
    key_results: list[KeyResult] = Field(
        description="3-5 measurable key results"
    )
    time_horizon: str = Field(description="The time period for this OKR")
    alignment_notes: str = Field(
        description="How this OKR connects to broader strategy"
    )


# ---------------------------------------------------------------------------
# Pricing Strategy (Phase 2)
# ---------------------------------------------------------------------------

class CompetitorPricing(BaseModel):
    """A competitor's pricing for comparison."""
    name: str
    price_point: str
    model: str = Field(description="Their pricing model (subscription, usage, one-time, etc.)")
    notes: str = Field(default="")


class PricingStrategyOutput(BaseToolOutput):
    """Output for the pricing strategy analysis tool."""
    product_name: str
    recommended_model: str = Field(
        description="Recommended pricing model (e.g., freemium, tiered subscription, usage-based)"
    )
    recommended_price_range: str = Field(
        description="Suggested price range with reasoning"
    )
    value_metric: str = Field(
        description="The unit of value the price should be anchored to"
    )
    positioning_alignment: str = Field(
        description="How pricing aligns with product positioning"
    )
    competitor_comparison: list[CompetitorPricing] = Field(
        description="How competitors price their products"
    )
    pricing_risks: list[str] = Field(
        description="Risks with the recommended pricing approach"
    )
