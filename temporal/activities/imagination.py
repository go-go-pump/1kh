"""
Imagination Activities - Generate and evaluate hypotheses.

These activities use Claude to:
1. Generate hypotheses for achieving the North Star
2. Evaluate each hypothesis on multiple dimensions
3. Identify relationships and dependencies between hypotheses
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime

from temporalio import activity

# Logger for when running outside Temporal context
logger = logging.getLogger("1kh.imagination")


def _safe_heartbeat(msg: str):
    """Send heartbeat if in activity context, otherwise log."""
    try:
        activity.heartbeat(msg)
    except RuntimeError:
        logger.debug(f"Heartbeat: {msg}")


def _safe_log_info(msg: str):
    """Log info whether in activity context or not."""
    try:
        activity.logger.info(msg)
    except RuntimeError:
        logger.info(msg)


def _safe_log_warning(msg: str):
    """Log warning whether in activity context or not."""
    try:
        activity.logger.warning(msg)
    except RuntimeError:
        logger.warning(msg)


def _safe_log_error(msg: str):
    """Log error whether in activity context or not."""
    try:
        activity.logger.error(msg)
    except RuntimeError:
        logger.error(msg)


@dataclass
class HypothesisScore:
    """Multi-dimensional scoring for a hypothesis."""
    # Can we actually build/execute this?
    feasibility: float  # 0.0-1.0: Technical/resource feasibility

    # Will it achieve the goal?
    north_star_alignment: float  # 0.0-1.0: How directly does this serve objectives?

    # Overall confidence (computed)
    @property
    def overall(self) -> float:
        return (self.feasibility * 0.4) + (self.north_star_alignment * 0.6)


@dataclass
class Hypothesis:
    """A potential path toward the North Star."""
    id: str
    description: str
    rationale: str

    # Which North Star objectives does this serve?
    serves_objectives: list[str]  # List of objective indices/descriptions

    # How does it serve them?
    objective_mapping: str  # Explanation of how this connects to North Star

    # Effort and timeline
    estimated_effort: str  # "hours", "days", "weeks", "months"
    estimated_hours: int  # Concrete hour estimate

    # Multi-dimensional scoring
    feasibility: float  # Can we build it?
    north_star_alignment: float  # Will it achieve the goal?

    # Dependencies and relationships
    depends_on: list[str] = field(default_factory=list)  # Other hypothesis IDs
    blocks: list[str] = field(default_factory=list)  # What this blocks
    parent_id: Optional[str] = None  # For nested/child hypotheses

    # Risks and assumptions
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    # Resource declarations for conflict detection
    touches_resources: list[dict] = field(default_factory=list)  # [{type, identifier, access}]

    # Status
    status: str = "proposed"  # proposed, accepted, rejected, exploring, completed


@activity.defn
async def generate_hypotheses(
    project_path: str,
    oracle: dict,
    north_star: dict,
    context: dict,
    existing_hypotheses: list[dict],
    max_new: int = 5,
    reflection: dict = None,
) -> list[dict]:
    """
    Generate hypotheses that map to North Star objectives.

    This is a COMPREHENSIVE generation - we want to explore the full solution space,
    not just pick 5 random ideas. The hypotheses should:
    1. Cover ALL North Star objectives
    2. Include both high-level strategies and tactical approaches
    3. Identify dependencies and relationships
    4. Be explicit about what they achieve

    If reflection data is provided, it will guide the hypothesis generation
    to prioritize missing system components (payment, channel, etc.)
    """
    _safe_log_info("Generating hypotheses with Claude")

    from anthropic import Anthropic

    # Load API key
    env_path = Path(project_path) / ".1kh" / ".env"
    api_key = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        _safe_log_error("No ANTHROPIC_API_KEY found")
        return []

    client = Anthropic(api_key=api_key)

    # Extract objectives for explicit mapping
    objectives_list = north_star.get('objectives', [])
    objectives_formatted = "\n".join([f"  {i+1}. {obj}" for i, obj in enumerate(objectives_list)])

    # Build reflection guidance if available
    reflection_guidance = ""
    if reflection:
        completeness = reflection.get("completeness", {})
        can_generate = completeness.get("can_generate_revenue", True)
        blockers = completeness.get("blockers", [])
        recommendations = reflection.get("recommendations", [])

        if not can_generate:
            reflection_guidance = f"""
## ⚠️ CRITICAL: SYSTEM CANNOT GENERATE REVENUE

The REFLECTION loop has identified that the system is MISSING critical components:
{chr(10).join(f'  - {b}' for b in blockers)}

**YOU MUST PRIORITIZE** hypotheses that address these blockers FIRST.
Without these components, no revenue can be generated, regardless of other work.

Recommendations from REFLECTION:
{chr(10).join(f'  - [{r.get("type", "unknown").upper()}] {r.get("title", "Unknown")}' for r in recommendations)}

Generate hypotheses that:
1. FIRST: Address the missing components (payment, channel, product, fulfillment)
2. THEN: Optimize and improve existing components
3. FINALLY: Add new features and capabilities
"""
        elif recommendations:
            reflection_guidance = f"""
## Recommendations from REFLECTION Loop

The system has analyzed trajectory and suggests:
{chr(10).join(f'  - [{r.get("type", "unknown").upper()}] {r.get("title", "Unknown")}' for r in recommendations)}

Consider incorporating these recommendations into your hypotheses.
"""

    prompt = f"""You are the IMAGINATION loop of ThousandHand, an autonomous business-building system.
{reflection_guidance}

Your job is to generate a COMPREHENSIVE set of hypotheses - potential paths toward achieving the human's North Star objectives.

## Oracle (Values & Boundaries - MUST RESPECT)
{oracle.get('raw', 'No oracle defined')}

## North Star (Objectives - MUST MAP TO THESE)
{north_star.get('raw', 'No objectives defined')}

Numbered Objectives:
{objectives_formatted}

## Context (Resources & Constraints)
{context.get('raw', 'No context defined')}

## Already Explored
{_format_existing(existing_hypotheses)}

## Your Task

Generate hypotheses that COMPREHENSIVELY cover how to achieve the North Star. Consider:

1. **Coverage**: Every objective should have at least one hypothesis addressing it
2. **Hierarchy**: Include both high-level strategic approaches AND tactical sub-hypotheses
3. **Dependencies**: Identify what must happen before other things can happen
4. **Alternatives**: For critical objectives, propose multiple approaches
5. **Reality check**: Be honest about feasibility given the constraints

For each hypothesis, you MUST provide:
- **id**: Unique identifier (e.g., "hyp-001", use "hyp-001a" for sub-hypotheses)
- **description**: Full, detailed description (don't truncate - be thorough)
- **rationale**: Why this approach might work
- **serves_objectives**: Which numbered objectives this addresses (e.g., [1, 3, 5])
- **objective_mapping**: HOW this connects to those objectives (be specific)
- **estimated_effort**: "hours" | "days" | "weeks" | "months"
- **estimated_hours**: Concrete number (e.g., 8, 40, 160)
- **feasibility**: 0.0-1.0 - Can we actually BUILD/EXECUTE this given context?
- **north_star_alignment**: 0.0-1.0 - How directly does this achieve the objectives?
- **depends_on**: List of hypothesis IDs this depends on (empty if independent)
- **blocks**: List of hypothesis IDs that can't proceed until this is done
- **parent_id**: If this is a sub-hypothesis, the parent's ID (null otherwise)
- **risks**: Key risks that could derail this
- **assumptions**: What we're assuming is true
- **touches_resources**: List of resources this hypothesis will modify. Each resource has:
  - "type": "file" | "file_glob" | "api" | "database" | "service" | "deployment" | "budget"
  - "identifier": The specific resource (file path, API endpoint, service name)
  - "access": "read" | "write"

IMPORTANT: Resource declarations enable conflict detection. Two hypotheses that both write to the same file CANNOT run in parallel - they must be sequenced. Be specific about what files/APIs/services will be modified.

Generate as many hypotheses as needed to comprehensively cover the objectives.
Minimum: one per objective. Maximum: use your judgment based on complexity.

Respond in JSON format:
```json
{{
  "analysis": {{
    "objective_coverage": {{
      "1": ["hyp-001", "hyp-002"],
      "2": ["hyp-003"],
      ...
    }},
    "critical_dependencies": ["List of critical path items"],
    "highest_risk_areas": ["Areas that need human attention"],
    "recommended_starting_point": "hyp-XXX"
  }},
  "hypotheses": [
    {{
      "id": "hyp-001",
      "description": "Full detailed description...",
      "rationale": "Why this works...",
      "serves_objectives": [1, 2],
      "objective_mapping": "This achieves objective 1 by... and objective 2 by...",
      "estimated_effort": "days",
      "estimated_hours": 24,
      "feasibility": 0.8,
      "north_star_alignment": 0.9,
      "depends_on": [],
      "blocks": ["hyp-002"],
      "parent_id": null,
      "risks": ["Risk 1", "Risk 2"],
      "assumptions": ["Assumption 1"],
      "touches_resources": [
        {{"type": "file", "identifier": "src/api/main.py", "access": "write"}},
        {{"type": "api", "identifier": "stripe.com/v1/customers", "access": "read"}}
      ]
    }}
  ]
}}
```
"""

    _safe_heartbeat("Calling Claude API for hypothesis generation")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,  # Increased for comprehensive output
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text

    # Extract JSON from response
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            hypotheses = result.get("hypotheses", [])
            analysis = result.get("analysis", {})

            # Attach analysis to each hypothesis for context
            for hyp in hypotheses:
                hyp["_analysis"] = analysis

            _safe_log_info(f"Generated {len(hypotheses)} hypotheses covering {len(analysis.get('objective_coverage', {}))} objectives")
            return hypotheses
        except json.JSONDecodeError as e:
            _safe_log_error(f"Failed to parse hypothesis JSON: {e}")
            # Try to extract just the hypotheses array
            hyp_match = re.search(r'"hypotheses"\s*:\s*(\[.*?\])', text, re.DOTALL)
            if hyp_match:
                try:
                    return json.loads(hyp_match.group(1))
                except:
                    pass
            return []

    _safe_log_warning("No JSON found in Claude response")
    return []


@activity.defn
async def evaluate_hypothesis(
    project_path: str,
    hypothesis: dict,
    oracle: dict,
    context: dict,
    north_star: dict,
) -> dict:
    """
    Deeply evaluate a single hypothesis.

    This provides detailed scoring on:
    1. Feasibility - Can we actually do this?
    2. North Star Alignment - Will it achieve the goal?
    3. Oracle Compliance - Does it respect our values?
    4. Risk Assessment - What could go wrong?
    """
    _safe_log_info(f"Evaluating hypothesis: {hypothesis.get('id', 'unknown')}")

    from anthropic import Anthropic

    env_path = Path(project_path) / ".1kh" / ".env"
    api_key = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return hypothesis

    client = Anthropic(api_key=api_key)

    prompt = f"""Evaluate this hypothesis for a business-building project.

## Hypothesis to Evaluate
ID: {hypothesis.get('id')}
Description: {hypothesis.get('description')}
Rationale: {hypothesis.get('rationale')}
Claimed Objectives: {hypothesis.get('serves_objectives')}
Objective Mapping: {hypothesis.get('objective_mapping')}
Initial Feasibility: {hypothesis.get('feasibility')}
Initial Alignment: {hypothesis.get('north_star_alignment')}

## Oracle (Values - MUST NOT VIOLATE)
Values: {oracle.get('values', [])}
Never Do: {oracle.get('never_do', [])}

## North Star (What we're trying to achieve)
Objectives: {north_star.get('objectives', [])}
Success Metrics: {north_star.get('success_metrics', [])}

## Context (Resources & Constraints)
{context.get('raw', 'No context')}

## Evaluation Tasks

1. **Oracle Compliance**: Does this violate any values or "never do" items?
2. **Feasibility Reality Check**: Given the ACTUAL constraints (budget, time, skills), can this be done?
3. **North Star Alignment**: Will completing this ACTUALLY move toward the objectives?
4. **Gap Analysis**: What's missing from this hypothesis?
5. **Risk Assessment**: What are the real risks?

Be HONEST and CRITICAL. It's better to surface problems now than fail later.

Respond in JSON:
```json
{{
  "oracle_compliance": {{
    "compliant": true/false,
    "violations": ["Any violations"],
    "concerns": ["Any concerns that aren't violations but need attention"]
  }},
  "feasibility": {{
    "score": 0.0-1.0,
    "can_we_build_it": true/false,
    "blockers": ["What prevents this"],
    "enablers": ["What makes this possible"],
    "missing_resources": ["What we'd need but don't have"],
    "realistic_hours": 24
  }},
  "north_star_alignment": {{
    "score": 0.0-1.0,
    "will_it_achieve_goal": true/false,
    "objective_impact": {{
      "1": "How it impacts objective 1",
      "2": "How it impacts objective 2"
    }},
    "gaps": ["What objectives this doesn't address"],
    "indirect_benefits": ["Secondary benefits"]
  }},
  "risks": {{
    "high": ["High severity risks"],
    "medium": ["Medium severity risks"],
    "low": ["Low severity risks"]
  }},
  "recommendation": {{
    "proceed": true/false,
    "confidence": 0.0-1.0,
    "modifications_needed": ["Suggested changes"],
    "questions_for_human": ["Things that need human input"]
  }}
}}
```
"""

    _safe_heartbeat("Evaluating hypothesis with Claude")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)

    if json_match:
        try:
            evaluation = json.loads(json_match.group(1))

            # Update hypothesis with evaluation
            hypothesis["evaluation"] = evaluation
            hypothesis["feasibility"] = evaluation.get("feasibility", {}).get("score", hypothesis.get("feasibility", 0.5))
            hypothesis["north_star_alignment"] = evaluation.get("north_star_alignment", {}).get("score", hypothesis.get("north_star_alignment", 0.5))
            hypothesis["evaluated_at"] = datetime.utcnow().isoformat()

            # Flag if there are oracle violations
            if not evaluation.get("oracle_compliance", {}).get("compliant", True):
                hypothesis["status"] = "oracle_violation"
                hypothesis["feasibility"] = 0.0

            return hypothesis
        except json.JSONDecodeError:
            pass

    return hypothesis


# Keep old function name for compatibility
@activity.defn
async def estimate_confidence(
    project_path: str,
    hypothesis: dict,
    oracle: dict,
    context: dict,
) -> dict:
    """Legacy wrapper - calls evaluate_hypothesis with empty north_star."""
    # For backward compatibility
    return await evaluate_hypothesis(
        project_path=project_path,
        hypothesis=hypothesis,
        oracle=oracle,
        context=context,
        north_star={"objectives": [], "success_metrics": []},
    )


def _format_existing(hypotheses: list[dict]) -> str:
    """Format existing hypotheses for the prompt."""
    if not hypotheses:
        return "(none yet)"

    lines = []
    for h in hypotheses:
        status = h.get("status", "unknown")
        desc = h.get("description", "No description")[:100]
        serves = h.get("serves_objectives", [])
        lines.append(f"- [{status}] {h.get('id', '?')}: {desc}... (objectives: {serves})")

    return "\n".join(lines)
