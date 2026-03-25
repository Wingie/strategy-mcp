"""Tests for Phase 1 strategy-mcp tools.

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

    def test_medium_priority(self):
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
