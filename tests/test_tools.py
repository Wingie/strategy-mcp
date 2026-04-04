"""Tests for all strategy-mcp tools (Phase 1, 2, and 3).

Each test uses a realistic product scenario and validates output structure.
"""

import json
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.prioritization import rice_score
from tools.discovery import assumption_map, jobs_to_be_done
from tools.positioning import competitive_position
from tools.business_model import business_model_review, tam_sam_som, pricing_strategy
from tools.execution import okr_generator, initiative_scoper
from tools.advanced import wardley_assessment, hypothesis_builder
from tools.governance import decision_log_entry


def _parse(result: str) -> dict:
    """Parse a JSON tool result string into a dict."""
    return json.loads(result)


def _assert_base_output(data: dict):
    """Assert that the output meets the BaseToolOutput standard."""
    assert "analysis" in data and len(data["analysis"]) > 0
    assert "next_steps" in data and 2 <= len(data["next_steps"]) <= 5
    assert data["confidence"] in ("High", "Medium", "Low")
    assert "confidence_rationale" in data and len(data["confidence_rationale"]) > 0
    assert "pressure_test_questions" in data and 2 <= len(data["pressure_test_questions"]) <= 3


class TestRiceScore:
    """Score a 'dark mode' feature for a B2B SaaS product."""

    def test_happy_path(self):
        result = _parse(rice_score(
            feature_name="Dark Mode",
            reach=5000,
            impact=1,
            confidence_pct=80,
            effort=2,
        ))

        _assert_base_output(result)
        assert result["feature_name"] == "Dark Mode"
        assert result["rice_score"] == 2000.0  # (5000 * 1 * 0.8) / 2
        assert result["priority_tier"] == "Critical"
        assert "RICE" in result["score_breakdown"]

    def test_low_priority_feature(self):
        result = _parse(rice_score(
            feature_name="Custom Favicon Upload",
            reach=200,
            impact=0.25,
            confidence_pct=40,
            effort=1,
        ))

        _assert_base_output(result)
        assert result["rice_score"] == 20.0  # (200 * 0.25 * 0.4) / 1
        assert result["priority_tier"] == "Low"

    def test_critical_from_high_reach(self):
        result = _parse(rice_score(
            feature_name="Improved Onboarding Flow",
            reach=3000,
            impact=2,
            confidence_pct=60,
            effort=4,
        ))

        _assert_base_output(result)
        assert result["rice_score"] == 900.0  # (3000 * 2 * 0.6) / 4
        assert result["priority_tier"] == "Critical"


class TestAssumptionMap:
    """Map assumptions for a new two-sided marketplace."""

    def test_happy_path(self):
        result = _parse(assumption_map(
            assumptions=[
                {
                    "statement": "Freelancers will pay a 15% platform fee",
                    "confidence_level": 2,
                    "impact_level": 5,
                    "category": "Business",
                },
                {
                    "statement": "We can acquire clients via LinkedIn outreach",
                    "confidence_level": 4,
                    "impact_level": 4,
                    "category": "Market",
                },
                {
                    "statement": "Our matching algorithm will be better than manual search",
                    "confidence_level": 2,
                    "impact_level": 3,
                    "category": "Technical",
                },
                {
                    "statement": "Freelancers will complete their profiles within 48 hours",
                    "confidence_level": 3,
                    "impact_level": 2,
                    "category": "User",
                },
            ]
        ))

        _assert_base_output(result)
        assert result["total_assumptions"] == 4
        assert "Test Now" in result["quadrant_summary"]
        assert result["quadrant_summary"]["Test Now"] >= 1  # The 15% fee assumption

        # Verify assumptions are sorted by urgency
        urgencies = [a["urgency_score"] for a in result["assumptions"]]
        assert urgencies == sorted(urgencies, reverse=True)

    def test_single_assumption(self):
        result = _parse(assumption_map(
            assumptions=[
                {
                    "statement": "Users want real-time collaboration",
                    "confidence_level": 3,
                    "impact_level": 4,
                },
            ]
        ))

        _assert_base_output(result)
        assert result["total_assumptions"] == 1


class TestJobsToBeDone:
    """Analyze JTBD for a project management tool feature."""

    def test_happy_path(self):
        result = _parse(jobs_to_be_done(
            feature_or_problem="prioritize features based on strategic impact",
            target_user="product managers at B2B SaaS companies",
            context="during quarterly planning when deciding what to build next",
            current_alternatives=[
                "spreadsheets with manual scoring",
                "gut feeling in leadership meetings",
                "JIRA voting plugins",
            ],
            desired_outcomes=[
                "faster, more confident prioritization decisions",
                "stakeholder alignment on what matters most",
                "data-backed justification for roadmap choices",
            ],
        ))

        _assert_base_output(result)
        assert "job_statement" in result and len(result["job_statement"]) > 0
        assert "functional_job" in result
        assert "emotional_job" in result
        assert "social_job" in result
        assert len(result["hiring_criteria"]) >= 2
        assert len(result["firing_triggers"]) >= 2
        assert len(result["switching_barriers"]) >= 2

    def test_minimal_input(self):
        result = _parse(jobs_to_be_done(
            feature_or_problem="track daily habits",
            target_user="busy professionals",
            context="at the end of each day when reviewing progress",
            current_alternatives=["pen and paper"],
            desired_outcomes=["consistency in building good habits"],
        ))

        _assert_base_output(result)
        assert "job_statement" in result


class TestCompetitivePosition:
    """Map 3 competitors in the design tools space."""

    def test_happy_path(self):
        result = _parse(competitive_position(
            your_product_name="DesignFlow",
            your_x_position=7,
            your_y_position=8,
            axis_x_name="Ease of Use",
            axis_y_name="Feature Depth",
            competitors=[
                {"name": "Figma", "x_position": 8, "y_position": 9},
                {"name": "Canva", "x_position": 9, "y_position": 4},
                {"name": "Adobe XD", "x_position": 5, "y_position": 8, "notes": "Losing market share"},
            ],
        ))

        _assert_base_output(result)
        assert result["axis_x"] == "Ease of Use"
        assert result["axis_y"] == "Feature Depth"
        assert result["your_position"]["name"] == "DesignFlow"
        assert len(result["competitors"]) == 3
        assert len(result["nearest_threats"]) >= 1
        assert len(result["white_space"]) >= 1
        assert len(result["differentiation_summary"]) > 0

    def test_isolated_position(self):
        """Test when your product is far from competitors."""
        result = _parse(competitive_position(
            your_product_name="NicheApp",
            your_x_position=2,
            your_y_position=2,
            axis_x_name="Price",
            axis_y_name="Complexity",
            competitors=[
                {"name": "Enterprise Giant", "x_position": 9, "y_position": 9},
                {"name": "Mid-Market Player", "x_position": 6, "y_position": 6},
            ],
        ))

        _assert_base_output(result)
        # Should identify that NicheApp has a distinct position
        assert "distinct" in result["differentiation_summary"].lower() or "separate" in result["differentiation_summary"].lower() or float(result["nearest_threats"][0].split("distance: ")[1].rstrip(")")) > 3


# =========================================================================
# Phase 2 Tests
# =========================================================================


class TestBusinessModelReview:
    """Review BMC for a B2B analytics startup."""

    def test_happy_path(self):
        result = _parse(business_model_review(
            product_name="DataPulse Analytics",
            customer_segments="Mid-market B2B SaaS companies with 50-500 employees, primarily marketing and product teams",
            value_propositions="Real-time product analytics with AI anomaly detection — finds revenue-impacting issues before users report them",
            channels="Product Hunt launch, content marketing, LinkedIn ads, partner integrations with Segment and Amplitude",
            customer_relationships="Self-serve with in-app onboarding, community Slack, dedicated CSM for enterprise accounts",
            revenue_streams="Freemium SaaS — free up to 10K events/mo, Growth $99/mo, Scale $399/mo, Enterprise custom",
            key_resources="Proprietary anomaly detection ML models, streaming data pipeline, engineering team of 6",
            key_activities="Model training and improvement, data pipeline scaling, customer onboarding, content creation",
            key_partnerships="Segment (data integration), AWS (infrastructure), dbt (analytics engineering community)",
            cost_structure="AWS infrastructure (variable, ~$8K/mo), engineering salaries (fixed, ~$80K/mo), marketing (fixed, $5K/mo)",
        ))

        _assert_base_output(result)
        assert result["product_name"] == "DataPulse Analytics"
        assert len(result["component_assessments"]) == 9
        assert result["overall_health"] in ("Strong", "Viable", "Gaps Present", "Incomplete")
        assert isinstance(result["critical_gaps"], list)
        assert isinstance(result["strongest_elements"], list)
        assert len(result["coherence_notes"]) > 0

    def test_sparse_model(self):
        """Test with only 2 components filled in."""
        result = _parse(business_model_review(
            product_name="Early Idea",
            customer_segments="Small business owners",
            value_propositions="Save time on invoicing",
        ))

        _assert_base_output(result)
        assert result["overall_health"] == "Incomplete"
        assert len(result["critical_gaps"]) >= 5  # Most components missing


class TestTamSamSom:
    """Size the market for an AI writing assistant."""

    def test_happy_path(self):
        result = _parse(tam_sam_som(
            product_name="WriteBot AI",
            industry="AI Writing and Content Generation Tools",
            total_market_size_usd=5_000_000_000,
            target_segment_pct=8,
            realistic_capture_pct=1.5,
            avg_revenue_per_customer_usd=1200,
            estimated_target_customers=200000,
            geographic_scope="North America and Europe",
        ))

        _assert_base_output(result)
        assert result["product_name"] == "WriteBot AI"
        assert result["industry"] == "AI Writing and Content Generation Tools"
        assert len(result["tiers"]) == 3
        tier_names = [t["tier"] for t in result["tiers"]]
        assert tier_names == ["TAM", "SAM", "SOM"]
        assert len(result["key_assumptions"]) >= 2
        assert len(result["sanity_checks"]) >= 2
        assert len(result["methodology"]) > 0

    def test_small_niche_market(self):
        result = _parse(tam_sam_som(
            product_name="NicheApp",
            industry="Boutique Consulting CRM",
            total_market_size_usd=50_000_000,
            target_segment_pct=20,
            realistic_capture_pct=5,
            avg_revenue_per_customer_usd=600,
            estimated_target_customers=5000,
        ))

        _assert_base_output(result)
        # SOM should flag the small market
        som_reasoning = result["tiers"][2]["reasoning"]
        assert len(som_reasoning) > 0


class TestPricingStrategy:
    """Analyze pricing for a developer tools product."""

    def test_happy_path(self):
        result = _parse(pricing_strategy(
            product_name="DevFlow CI",
            product_description="Cloud CI/CD platform optimized for monorepos, targeting engineering teams at mid-size startups",
            current_pricing="Free tier (100 build min/mo), Team $49/mo (1000 min), Business $199/mo (5000 min)",
            value_metric="per build minute",
            target_customer="VP Engineering at startups with 20-100 developers",
            positioning="Premium — fastest builds in the market with intelligent caching",
            competitors=[
                {"name": "CircleCI", "price_point": "$30-300/mo", "model": "per credit usage"},
                {"name": "GitHub Actions", "price_point": "Free-$44/user/mo", "model": "per minute, bundled with GitHub"},
                {"name": "BuildKite", "price_point": "$15/user/mo", "model": "per seat"},
            ],
        ))

        _assert_base_output(result)
        assert result["product_name"] == "DevFlow CI"
        assert len(result["recommended_model"]) > 0
        assert len(result["recommended_price_range"]) > 0
        assert result["value_metric"] == "per build minute"
        assert len(result["competitor_comparison"]) == 3
        assert len(result["pricing_risks"]) >= 1


class TestOkrGenerator:
    """Generate OKRs for a product launch."""

    def test_with_metrics(self):
        result = _parse(okr_generator(
            strategic_goal="Launch self-serve onboarding to reduce time-to-value below 5 minutes",
            time_horizon="Q2 2026",
            team_or_org="Growth squad",
            context="Current onboarding requires a 30-min call with CS. 40% of signups never complete setup. Need to unblock PLG motion.",
            current_metrics=[
                {"metric": "Onboarding completion rate", "current_value": "60%", "target_value": "90%"},
                {"metric": "Time to first value", "current_value": "45 minutes", "target_value": "5 minutes"},
                {"metric": "CS onboarding calls per week", "current_value": "25", "target_value": "5"},
            ],
        ))

        _assert_base_output(result)
        assert len(result["objective"]) > 0
        assert len(result["key_results"]) >= 3
        for kr in result["key_results"]:
            assert "key_result" in kr
            assert "metric" in kr
            assert "baseline" in kr
            assert "target" in kr
        assert result["time_horizon"] == "Q2 2026"
        assert result["confidence"] == "High"  # Metrics provided with real baselines

    def test_without_metrics(self):
        result = _parse(okr_generator(
            strategic_goal="Build a community around our open source project",
            time_horizon="H2 2026",
            team_or_org="Developer Relations",
            context="Just launched the repo, 50 GitHub stars, no community yet.",
            current_metrics=[],
        ))

        _assert_base_output(result)
        assert len(result["key_results"]) >= 3
        assert result["confidence"] == "Low"  # No metrics provided


class TestInitiativeScoper:
    """Scope initiatives for launching a mobile app."""

    def test_happy_path(self):
        result = _parse(initiative_scoper(
            strategic_goal="Launch a mobile app for our existing web product",
            time_horizon="Q3 2026",
            team_size=4,
            constraints=["No iOS developer on team yet", "Must reuse existing API", "App Store review adds 1-2 weeks"],
            known_dependencies=["Design system needs mobile components", "Push notification service selection"],
        ))

        _assert_base_output(result)
        assert len(result["initiatives"]) >= 5
        assert len(result["recommended_sequence"]) == len(result["initiatives"])
        assert len(result["critical_path"]) >= 1
        assert len(result["total_estimated_effort"]) > 0

        # Check that dependency resolution initiatives were created
        initiative_names = [i["name"] for i in result["initiatives"]]
        assert any("Design system" in name for name in initiative_names)

    def test_minimal_scope(self):
        result = _parse(initiative_scoper(
            strategic_goal="Write a landing page",
            time_horizon="1 week",
            team_size=1,
            constraints=[],
            known_dependencies=[],
        ))

        _assert_base_output(result)
        assert len(result["initiatives"]) >= 3  # Discovery, core build, polish at minimum


# =========================================================================
# Phase 3 Tests
# =========================================================================


class TestWardleyAssessment:
    """Assess components for an e-commerce platform."""

    def test_happy_path(self):
        result = _parse(wardley_assessment(
            value_chain_context="E-commerce platform for handmade goods",
            components=[
                {"name": "AI Recommendation Engine", "description": "Custom ML model for personalized product recommendations. Novel approach using artisan style matching. Experimental, no market equivalent."},
                {"name": "Product Search", "description": "Elasticsearch-based search. Multiple SaaS vendors available. Established market with Algolia, Typesense."},
                {"name": "Payment Processing", "description": "Stripe API integration. Commodity service, standardized APIs, utility pricing."},
                {"name": "Artisan Matching Algorithm", "description": "Proprietary in-house algorithm that matches buyers to artisans based on style preferences. Custom-built, no off-the-shelf solution."},
            ],
        ))

        _assert_base_output(result)
        assert len(result["components"]) == 4
        stages = [c["stage"] for c in result["components"]]
        assert "Genesis" in stages or "Custom-Built" in stages  # AI rec should be genesis/custom
        assert "Commodity" in stages  # Payment should be commodity
        assert sum(result["stage_distribution"].values()) == 4
        assert len(result["build_vs_buy_recommendations"]) == 4

    def test_single_component(self):
        result = _parse(wardley_assessment(
            value_chain_context="Simple blog platform",
            components=[{"name": "Hosting", "description": "AWS cloud hosting, commodity utility service"}],
        ))

        _assert_base_output(result)
        assert result["components"][0]["stage"] == "Commodity"


class TestHypothesisBuilder:
    """Build hypotheses for a fitness app."""

    def test_happy_path(self):
        result = _parse(hypothesis_builder(
            product_context="Mobile fitness app targeting busy professionals who want 15-minute workouts",
            assumptions=[
                {
                    "assumption": "Users will complete 3+ workouts per week if workouts are under 15 minutes",
                    "target_user": "Working professionals aged 25-45",
                    "expected_outcome": "Higher weekly engagement and retention",
                    "risk_level": "High",
                },
                {
                    "assumption": "Social accountability features will reduce churn by 30%",
                    "target_user": "Users who connected with at least one friend",
                    "expected_outcome": "Improved 30-day retention",
                    "risk_level": "Medium",
                },
            ],
        ))

        _assert_base_output(result)
        assert len(result["hypotheses"]) == 2
        for h in result["hypotheses"]:
            assert "hypothesis_statement" in h
            assert "success_metric" in h
            assert "success_threshold" in h
            assert "suggested_test_method" in h
            assert "risk_if_wrong" in h
        assert len(result["testing_priority"]) == 2
        # High risk should be tested first
        assert "High" in result["testing_priority"][0]

    def test_single_assumption(self):
        result = _parse(hypothesis_builder(
            product_context="Note-taking app",
            assumptions=[{
                "assumption": "Users prefer voice notes over typing on mobile",
                "target_user": "Mobile-first note takers",
                "expected_outcome": "More notes created per session",
            }],
        ))

        _assert_base_output(result)
        assert len(result["hypotheses"]) == 1


class TestDecisionLogEntry:
    """Log a technology decision for a startup."""

    def test_happy_path(self):
        result = _parse(decision_log_entry(
            decision_title="Adopt Next.js over Remix for frontend rebuild",
            decision_date="2026-03-15",
            decision_maker="CTO, Jamie Rivera",
            context="Current frontend is aging jQuery app. Need modern framework for rebuild. Team has React experience but no framework-specific expertise.",
            decision="Use Next.js 15 with App Router for the complete frontend rebuild. Deploy on Vercel.",
            alternatives_considered=[
                "Remix — better data loading patterns but smaller ecosystem and fewer learning resources",
                "Astro — great for content-heavy sites but our app is highly interactive",
                "SvelteKit — loved by developers but team has no Svelte experience",
            ],
            rationale="Next.js has the largest ecosystem, most learning resources, and Vercel deployment is zero-config. The team can ramp up fastest on Next.js given existing React knowledge.",
            expected_consequences=[
                "Fastest team ramp-up due to React familiarity and abundant Next.js resources",
                "Access to the largest ecosystem of UI libraries and integrations",
                "Risk of vendor lock-in with Vercel-specific optimizations",
                "May need to migrate away from App Router if performance issues arise at scale",
            ],
        ))

        _assert_base_output(result)
        assert result["decision_title"] == "Adopt Next.js over Remix for frontend rebuild"
        assert result["status"] == "Decided"
        assert len(result["alternatives_considered"]) == 3
        assert len(result["consequences"]) == 4
        assert len(result["revisit_conditions"]) >= 2

    def test_minimal_decision(self):
        """Decision with no alternatives or consequences."""
        result = _parse(decision_log_entry(
            decision_title="Use Slack for team communication",
            decision_date="2026-01-10",
            decision_maker="Ops Manager",
            context="Need a team chat tool for the new office.",
            decision="Adopted Slack Free tier.",
            alternatives_considered=[],
            rationale="Everyone already uses it.",
            expected_consequences=[],
        ))

        _assert_base_output(result)
        assert result["confidence"] == "Low"  # No alternatives = poor decision hygiene
