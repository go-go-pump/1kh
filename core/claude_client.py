"""
Claude API client for intelligent probing and structuring.

This module handles all interactions with Claude API for:
- Generating probing questions during Initial Ceremony
- Structuring raw input into Oracle, North Star, Context, Seeds
- Other intelligent reasoning tasks
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class ClaudeClient:
    """
    Client for Claude API interactions.
    """

    def __init__(self, project_path: Optional[Path] = None):
        self.client = None
        self.project_path = project_path

        # Try to get API key from multiple sources
        api_key = self._get_api_key()

        if HAS_ANTHROPIC and api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

    def _get_api_key(self) -> Optional[str]:
        """Get API key from project .env, then environment."""
        # 1. Check project .env file
        if self.project_path:
            env_file = self.project_path / ".1kh" / ".env"
            if env_file.exists():
                key = self._read_key_from_env_file(env_file, "ANTHROPIC_API_KEY")
                if key:
                    return key

        # 2. Fall back to environment variable
        return os.environ.get("ANTHROPIC_API_KEY")

    def _read_key_from_env_file(self, env_path: Path, key_name: str) -> Optional[str]:
        """Read a specific key from .env file."""
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == key_name and value.strip():
                    return value.strip()
        except IOError:
            pass
        return None

    def is_available(self) -> bool:
        """Check if Claude API is available."""
        return self.client is not None

    def generate_probing_questions(
        self,
        raw_input: str,
        existing_answers: dict[str, str],
        system_type: str = "user",
    ) -> list[str]:
        """
        Generate clarifying questions based on raw input.

        Uses Claude to identify gaps in:
        - Values (what they won't do)
        - Objectives (measurable goals)
        - Constraints (time, money, skills)
        - Timeline
        """
        if not self.is_available():
            # Fallback questions if Claude is not available
            return self._fallback_probing_questions(system_type)

        # Tailor prompts based on system type
        if system_type == "biz":
            system_prompt = """You are helping a human clarify their BUSINESS idea for an autonomous system.

This is a BIZ SYSTEM - focused on generating revenue/profit for the owner.

Based on their input, identify gaps in:
1. VALUES: Core principles, what they'll never compromise on, ethical boundaries
   - Probe with scenarios: "Would you be okay with X to increase revenue?"
   - Surface deal-breakers: "What practices would you refuse even if profitable?"
2. OBJECTIVES: Measurable, time-bound BUSINESS goals
   - Revenue targets (ARR, MRR, total)
   - Customer/user targets
   - Timeline to profitability
3. CONSTRAINTS: Budget, time, skills, resources
4. BUSINESS MODEL: How will this make money?
5. COMPETITION: Who else does this? What's different?

Ask 5-7 specific, direct questions to fill the biggest gaps.
Be conversational but efficient. Don't be sycophantic.

IMPORTANT: Always probe for VALUES even if not mentioned. Use scenarios to surface them.
Example: "Would you be comfortable with aggressive sales tactics if they doubled revenue?"

Return ONLY a JSON array of question strings, nothing else.
Example: ["What's your target monthly revenue in 6 months?", "Would you be okay with showing ads to users?"]"""
        else:
            system_prompt = """You are helping a human clarify their USER SYSTEM idea for an autonomous system.

This is a USER SYSTEM - focused on providing utility/value, not revenue.

Based on their input, identify gaps in:
1. VALUES: What matters to them personally, quality standards
   - What does "good enough" look like?
   - What would make them proud vs embarrassed?
2. PURPOSE: Why are they building this?
   - Personal use? Learning? Portfolio? Future business?
3. SUCCESS CRITERIA: What does "done" look like?
   - Feature completeness checklist
   - Quality standards
4. CONSTRAINTS: Time, skills, resources
5. SCOPE: What's in vs out for version 1?

Ask 5-7 specific, direct questions to fill the biggest gaps.
Be conversational but efficient. Don't be sycophantic.

For USER SYSTEMS, focus more on scope and "done" criteria than metrics.
Hypothesis-driven testing is OPTIONAL - focus on building something useful.

Return ONLY a JSON array of question strings, nothing else.
Example: ["What's the minimum feature set that would make this useful?", "Is this for you or will others use it?"]"""

        user_content = f"""Raw input from human:
{raw_input}

Previously answered:
{json.dumps(existing_answers, indent=2) if existing_answers else "None yet"}

Generate probing questions to fill the gaps."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )

            # Parse JSON response
            content = response.content[0].text
            # Handle potential markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            questions = json.loads(content.strip())
            return questions

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_probing_questions()

    def structure_input(
        self,
        raw_input: str,
        probing_answers: dict[str, str],
    ) -> dict[str, Any]:
        """
        Structure raw input into Oracle, North Star, Context, Seeds, Preferences.

        Returns a dict with keys:
        - oracle_values: list[str]
        - oracle_never_do: list[str]
        - north_star_objectives: list[str]
        - success_metrics: list[str]
        - context_items: list[str]
        - seeds: list[str]
        - preferences: list[str]
        """
        if not self.is_available():
            return self._fallback_structure(raw_input, probing_answers)

        system_prompt = """You are structuring a human's business idea into categories for an autonomous system.

Categories:
1. ORACLE VALUES: Core values and principles (what they stand for). Infer from their language and priorities.
2. ORACLE NEVER DO: Things they will never do (ethical boundaries). Look for explicit and implicit limits.
3. NORTH STAR OBJECTIVES: Measurable, time-bound goals. Be SPECIFIC and include the FULL description.
4. SUCCESS METRICS: How to measure if objectives are met
5. CONTEXT: Constraints, resources, skills, existing assets, technical details
6. SEEDS: Initial hypotheses or hunches to test - specific ideas from their input
7. PREFERENCES: How they like to work, communicate, etc.

IMPORTANT:
- Capture the FULL description of their project, not just the first sentence
- Include ALL technical details they provided
- Extract multiple specific seeds/ideas from their input
- Infer values from tone and priorities even if not stated directly

Return ONLY valid JSON with these keys:
{
  "oracle_values": ["value1", "value2"],
  "oracle_never_do": ["never1", "never2"],
  "north_star_objectives": ["objective1", "objective2"],
  "success_metrics": ["metric1", "metric2"],
  "context_items": ["constraint1", "resource1"],
  "seeds": ["idea1", "idea2"],
  "preferences": ["pref1", "pref2"]
}"""

        user_content = f"""Raw input:
{raw_input}

Answers to clarifying questions:
{json.dumps(probing_answers, indent=2)}

Structure this into the categories. Be comprehensive - don't truncate their ideas."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,  # Increased to capture full input
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )

            content = response.content[0].text
            # Handle potential markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_structure(raw_input, probing_answers)

    def _fallback_probing_questions(self, system_type: str = "user") -> list[str]:
        """Fallback questions when Claude is not available."""
        if system_type == "biz":
            return [
                "What's your target monthly revenue? (e.g., $1k, $10k, $100k)",
                "By when do you want to hit that target?",
                "What's your budget for tools and services?",
                "How will customers find you? (marketing approach)",
                "Are there things you absolutely won't do, even if profitable? (e.g., spam, misleading claims)",
                "Who are your competitors? What makes you different?",
                "What's your pricing model? (subscription, one-time, freemium)",
            ]
        else:
            return [
                "Is this just for you, or will others use it?",
                "What's the minimum feature set that would make this useful?",
                "How many hours per week can you dedicate to this?",
                "What skills do you have? What do you need to learn?",
                "What does 'good enough' look like for version 1?",
                "Do you have any existing assets? (code, designs, etc.)",
                "What would make you proud of this project?",
            ]

    def detect_system_type(self, raw_input: str) -> dict[str, Any]:
        """
        Detect whether user is building a BIZ SYSTEM or USER SYSTEM.

        BIZ SYSTEM = maximizing owner satisfaction (revenue, profit, KPIs)
        USER SYSTEM = maximizing user utility/fulfillment

        Returns dict with:
        - system_type: "biz" or "user"
        - confidence: 0.0-1.0
        - reasoning: explanation
        - suggested_north_star_type: revenue/profit/users/utility/etc
        """
        if not self.is_available():
            return self._fallback_system_type_detection(raw_input)

        system_prompt = """You are analyzing a project description to determine the type of system being built.

There are TWO types:

1. BIZ SYSTEM = Building to generate revenue/profit for the owner
   - Keywords: revenue, profit, customers, sales, monetize, business, ARR, MRR
   - Focus: Making money, growing a business, acquiring customers
   - Example: "I want to build a SaaS that makes $10k/month"
   - Example: "My e-commerce store selling products"

2. USER SYSTEM = Building to provide utility/value to users
   - Keywords: hobby, learning, portfolio, open source, personal tool, side project
   - Focus: Solving a problem, building skills, creating something useful
   - MAY monetize later, but that's not the primary goal
   - Example: "I want to build a tool that helps me track my habits"

IMPORTANT: Infrastructure/platforms that ENABLE other businesses = USER SYSTEM
   - Keywords: infrastructure, platform, tooling, utility, framework, service for, enables
   - Example: Building "Stripe" or "Twilio" = USER SYSTEM (provides utility to others)
   - Example: Building a conversation service that businesses use = USER SYSTEM
   - Example: Building a CRM or internal tool for businesses = USER SYSTEM
   - The business USING the infrastructure = BIZ SYSTEM

The question is: Does this project maximize USER UTILITY or OWNER REVENUE?
- If the primary goal is providing utility that others use to run their businesses → USER SYSTEM
- If the primary goal is directly generating revenue from end-user transactions → BIZ SYSTEM

Key insight: A USER SYSTEM can exist without business goals (hobby, learning).
A BIZ SYSTEM MUST have a USER SYSTEM (someone has to find value in what you sell).

Return ONLY valid JSON:
{
    "system_type": "biz" or "user",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why",
    "suggested_north_star_type": "revenue|profit|users|engagement|utility|learning|portfolio|custom",
    "key_signals": ["signal1", "signal2"]
}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Analyze this project description:\n\n{raw_input}"}],
            )

            content = response.content[0].text
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_system_type_detection(raw_input)

    def detect_utility_subtype(self, raw_input: str) -> dict[str, Any]:
        """
        Detect what kind of utility system is being built.

        For USER SYSTEMS, different utility types have different natural KPIs:
        - POC: "IT JUST WORKS" (binary feature checklist)
        - Multi-tenant: Reliability, uptime, tenant isolation
        - Orchestrator: Configuration, visibility, interfaces
        - Scheduler: Event timing, throughput
        - Internal Tool: Task completion, time saved
        - Library: API clarity, developer experience
        - Data Pipeline: Throughput, accuracy
        - Automation: Success rate, error handling

        Returns dict with:
        - utility_subtype: one of the above
        - confidence: 0.0-1.0
        - reasoning: explanation
        """
        if not self.is_available():
            return self._fallback_utility_subtype_detection(raw_input)

        system_prompt = """You are analyzing a project description to determine what KIND of utility system is being built.

Utility subtypes and their characteristics:

1. POC (Proof of Concept)
   - Keywords: prototype, demo, test, experiment, MVP, proof, validate
   - Goal: Prove something works
   - KPI: Binary - "IT JUST WORKS"

2. MULTI_TENANT (Shared Service)
   - Keywords: multi-tenant, SaaS infrastructure, shared, tenant, isolation
   - Goal: Reliable service for multiple users/orgs
   - KPI: Uptime, latency, tenant isolation

3. ORCHESTRATOR (Service Manager)
   - Keywords: orchestration, manage services, deploy, configure, dashboard, visibility
   - Goal: Control and view other systems
   - KPI: Configuration ability, interface quality

4. SCHEDULER (Event-driven)
   - Keywords: schedule, cron, events, queue, jobs, timing, async
   - Goal: Execute things at the right time
   - KPI: Timing accuracy, throughput

5. INTERNAL_TOOL (Productivity)
   - Keywords: internal, productivity, admin, backoffice, tool for team
   - Goal: Help people do tasks faster
   - KPI: Task completion, time saved

6. LIBRARY (SDK/API)
   - Keywords: library, SDK, API, package, module, framework
   - Goal: Make it easy for developers to integrate
   - KPI: Time to first call, documentation

7. DATA_PIPELINE (ETL/Streaming)
   - Keywords: pipeline, ETL, transform, ingest, stream, data flow
   - Goal: Move and transform data reliably
   - KPI: Throughput, accuracy, latency

8. AUTOMATION (Workflow)
   - Keywords: automation, workflow, bot, automate, scripted
   - Goal: Do repetitive things automatically
   - KPI: Success rate, error handling

9. CUSTOM
   - Doesn't fit above categories

Return ONLY valid JSON:
{
    "utility_subtype": "poc|multi_tenant|orchestrator|scheduler|internal_tool|library|data_pipeline|automation|custom",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "key_signals": ["signal1", "signal2"]
}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Analyze this project description:\n\n{raw_input}"}],
            )

            content = response.content[0].text
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_utility_subtype_detection(raw_input)

    def _fallback_utility_subtype_detection(self, raw_input: str) -> dict[str, Any]:
        """Fallback utility subtype detection when Claude is unavailable."""
        raw_lower = raw_input.lower()

        # Subtype signals (order matters - check more specific first)
        subtype_signals = {
            "multi_tenant": ["multi-tenant", "tenant", "saas", "shared service", "isolation"],
            "orchestrator": ["orchestrat", "manage service", "deploy", "dashboard", "visibility"],
            "scheduler": ["schedule", "cron", "event", "queue", "job", "timing", "async"],
            "data_pipeline": ["pipeline", "etl", "transform", "ingest", "stream", "data flow"],
            "library": ["library", "sdk", "api", "package", "module", "framework"],
            "automation": ["automat", "workflow", "bot", "script"],
            "internal_tool": ["internal", "admin", "backoffice", "tool for"],
            "poc": ["prototype", "demo", "test", "experiment", "mvp", "proof", "validate"],
        }

        for subtype, signals in subtype_signals.items():
            count = sum(1 for s in signals if s in raw_lower)
            if count >= 2:
                return {
                    "utility_subtype": subtype,
                    "confidence": min(0.5 + (count * 0.1), 0.8),
                    "reasoning": f"Detected {subtype} signals in input",
                    "key_signals": [s for s in signals if s in raw_lower][:3]
                }

        # Default to POC
        return {
            "utility_subtype": "poc",
            "confidence": 0.3,
            "reasoning": "Defaulting to POC - no strong utility subtype signals detected",
            "key_signals": []
        }

    def _fallback_system_type_detection(self, raw_input: str) -> dict[str, Any]:
        """Fallback system type detection when Claude is unavailable."""
        raw_lower = raw_input.lower()

        # BIZ signals
        biz_signals = ["revenue", "profit", "customer", "sales", "monetize",
                       "business", "arr", "mrr", "saas", "startup", "pricing",
                       "subscription", "market", "compete"]
        biz_count = sum(1 for s in biz_signals if s in raw_lower)

        # USER signals
        user_signals = ["hobby", "learning", "portfolio", "personal", "open source",
                        "side project", "for myself", "for fun", "practice", "experiment",
                        # Platform/infrastructure signals
                        "infrastructure", "platform", "tooling", "utility", "framework",
                        "internal tool", "enables", "supports", "service for",
                        "multi-tenant", "api for", "sdk", "library"]
        user_count = sum(1 for s in user_signals if s in raw_lower)

        if biz_count > user_count:
            return {
                "system_type": "biz",
                "confidence": min(0.5 + (biz_count * 0.1), 0.9),
                "reasoning": "Detected business-related keywords in input",
                "suggested_north_star_type": "revenue",
                "key_signals": [s for s in biz_signals if s in raw_lower][:3]
            }
        elif user_count > biz_count:
            return {
                "system_type": "user",
                "confidence": min(0.5 + (user_count * 0.1), 0.9),
                "reasoning": "Detected user-focused keywords in input",
                "suggested_north_star_type": "utility",
                "key_signals": [s for s in user_signals if s in raw_lower][:3]
            }
        else:
            return {
                "system_type": "user",  # Default to USER (safer assumption)
                "confidence": 0.3,
                "reasoning": "Unclear from input - defaulting to USER system",
                "suggested_north_star_type": "utility",
                "key_signals": []
            }

    def _fallback_structure(
        self,
        raw_input: str,
        probing_answers: dict[str, str],
    ) -> dict[str, Any]:
        """
        Fallback structure when Claude is not available.
        Creates a more meaningful structure from the raw input.
        """
        # Extract meaningful content - don't truncate
        objectives = []
        if raw_input:
            # Use the full input as the primary objective
            objectives.append(raw_input.strip())

        # Extract context from probing answers
        context_items = []
        for question, answer in probing_answers.items():
            if answer and answer.strip():
                context_items.append(f"{question}: {answer}")

        # Extract any technical details (look for common patterns)
        seeds = []
        if "CAPABILITIES:" in raw_input or "capabilities:" in raw_input.lower():
            # They listed capabilities - extract them
            lines = raw_input.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    seeds.append(line.lstrip("-•").strip())

        if not seeds and raw_input:
            # Just use the raw input as a seed
            seeds.append(raw_input.strip())

        return {
            "oracle_values": [
                "(Values not explicitly captured - please review and edit oracle.md)"
            ],
            "oracle_never_do": [],
            "north_star_objectives": objectives,
            "success_metrics": [],
            "context_items": context_items,
            "seeds": seeds[:10],  # Limit to 10 seeds
            "preferences": [],
        }
