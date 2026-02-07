"""
Hypothesis Management - Two-level hypothesis system.

Level 1: CAPABILITY (WHAT) - Technology-agnostic
Level 2: IMPLEMENTATION (HOW) - Technology-specific, may require user choice

This module handles:
1. Hypothesis creation at appropriate levels
2. Vendor/technology selection when needed
3. Preferences lookup to avoid unnecessary questions
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("1kh.hypothesis")


class HypothesisLevel(str, Enum):
    """Hypothesis abstraction level."""
    CAPABILITY = "capability"      # WHAT - technology-agnostic
    IMPLEMENTATION = "implementation"  # HOW - technology-specific


class VendorCategory(str, Enum):
    """Categories that typically need vendor selection."""
    PAYMENT = "payment"
    HOSTING = "hosting"
    DATABASE = "database"
    EMAIL = "email"
    ANALYTICS = "analytics"
    AUTH = "auth"
    STORAGE = "storage"
    CDN = "cdn"
    MONITORING = "monitoring"


# Default vendor options by category
DEFAULT_VENDOR_OPTIONS = {
    VendorCategory.PAYMENT: [
        {"id": "stripe", "name": "Stripe", "description": "Most popular, excellent docs, 2.9% + 30¢"},
        {"id": "square", "name": "Square", "description": "Great for in-person + online, 2.6% + 10¢"},
        {"id": "paypal", "name": "PayPal", "description": "Widely recognized, 3.49% + 49¢"},
        {"id": "other", "name": "Other", "description": "Specify your preferred provider"},
    ],
    VendorCategory.HOSTING: [
        {"id": "vercel", "name": "Vercel", "description": "Best for Next.js/React, easy deploys"},
        {"id": "netlify", "name": "Netlify", "description": "Great for static sites, generous free tier"},
        {"id": "aws", "name": "AWS", "description": "Most flexible, more complex"},
        {"id": "railway", "name": "Railway", "description": "Simple, good for backends"},
        {"id": "other", "name": "Other", "description": "Specify your preferred provider"},
    ],
    VendorCategory.DATABASE: [
        {"id": "supabase", "name": "Supabase", "description": "Postgres + auth + realtime, generous free tier"},
        {"id": "planetscale", "name": "PlanetScale", "description": "MySQL, great branching workflow"},
        {"id": "mongodb", "name": "MongoDB Atlas", "description": "Document DB, flexible schema"},
        {"id": "neon", "name": "Neon", "description": "Serverless Postgres, scales to zero"},
        {"id": "other", "name": "Other", "description": "Specify your preferred provider"},
    ],
    VendorCategory.EMAIL: [
        {"id": "resend", "name": "Resend", "description": "Modern API, React email support"},
        {"id": "sendgrid", "name": "SendGrid", "description": "Established, good deliverability"},
        {"id": "ses", "name": "AWS SES", "description": "Cheapest at scale, more setup"},
        {"id": "postmark", "name": "Postmark", "description": "Transactional focus, fast delivery"},
        {"id": "other", "name": "Other", "description": "Specify your preferred provider"},
    ],
    VendorCategory.AUTH: [
        {"id": "clerk", "name": "Clerk", "description": "Modern, great React components"},
        {"id": "auth0", "name": "Auth0", "description": "Enterprise-ready, many integrations"},
        {"id": "supabase_auth", "name": "Supabase Auth", "description": "Bundled with Supabase DB"},
        {"id": "nextauth", "name": "NextAuth.js", "description": "Open source, self-hosted"},
        {"id": "other", "name": "Other", "description": "Specify your preferred provider"},
    ],
}


@dataclass
class Preference:
    """A user's technology preference."""
    category: str
    preferred: Optional[str] = None  # Preferred vendor/technology
    avoid: list[str] = field(default_factory=list)  # Vendors to avoid
    reason: Optional[str] = None  # Why this preference


@dataclass
class VendorSelection:
    """Result of vendor selection process."""
    category: VendorCategory
    selected_vendor: str
    source: str  # "preference", "user_choice", "default"
    reason: Optional[str] = None


class PreferencesManager:
    """
    Manages user preferences for technology choices.

    Preferences can be stored in:
    1. context.md (critical preferences)
    2. .1kh/preferences.json (detailed preferences)
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.preferences_file = self.project_path / ".1kh" / "preferences.json"
        self._preferences: dict[str, Preference] = {}
        self._loaded = False

    def load(self) -> dict[str, Preference]:
        """Load preferences from file and context."""
        if self._loaded:
            return self._preferences

        # Load from preferences.json
        if self.preferences_file.exists():
            try:
                data = json.loads(self.preferences_file.read_text())
                for cat, pref_data in data.items():
                    # Handle both formats:
                    # Simple: {"payment": "stripe"}
                    # Full: {"payment": {"preferred": "stripe", "reason": "..."}}
                    if isinstance(pref_data, str):
                        self._preferences[cat] = Preference(
                            category=cat,
                            preferred=pref_data,
                            avoid=[],
                            reason=None,
                        )
                    elif isinstance(pref_data, dict):
                        self._preferences[cat] = Preference(
                            category=cat,
                            preferred=pref_data.get("preferred"),
                            avoid=pref_data.get("avoid", []),
                            reason=pref_data.get("reason"),
                        )
                    # Skip invalid entries
            except Exception as e:
                logger.warning(f"Failed to load preferences: {e}")

        # Also parse context.md for preferences
        self._parse_context_for_preferences()

        self._loaded = True
        return self._preferences

    def _parse_context_for_preferences(self):
        """Extract preferences from context.md."""
        context_path = self.project_path / ".1kh" / "foundation" / "context.md"
        if not context_path.exists():
            return

        content = context_path.read_text().lower()

        # Look for preference patterns
        # "we use Stripe" / "using Stripe" / "our payment is Stripe"
        for category, options in DEFAULT_VENDOR_OPTIONS.items():
            for opt in options:
                vendor_name = opt["name"].lower()
                vendor_id = opt["id"]

                # Check for explicit mentions
                if f"use {vendor_name}" in content or f"using {vendor_name}" in content:
                    if category.value not in self._preferences:
                        self._preferences[category.value] = Preference(
                            category=category.value,
                            preferred=vendor_id,
                            reason="Mentioned in context.md",
                        )

                # Check for "avoid" patterns
                if f"avoid {vendor_name}" in content or f"don't use {vendor_name}" in content:
                    if category.value in self._preferences:
                        self._preferences[category.value].avoid.append(vendor_id)
                    else:
                        self._preferences[category.value] = Preference(
                            category=category.value,
                            avoid=[vendor_id],
                        )

    def get_preference(self, category: str) -> Optional[Preference]:
        """Get preference for a category."""
        self.load()
        return self._preferences.get(category)

    def save_preference(self, preference: Preference):
        """Save a preference (from user choice)."""
        self.load()
        self._preferences[preference.category] = preference

        # Persist to file
        self.preferences_file.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for cat, pref in self._preferences.items():
            data[cat] = {
                "preferred": pref.preferred,
                "avoid": pref.avoid,
                "reason": pref.reason,
            }

        self.preferences_file.write_text(json.dumps(data, indent=2))

    def needs_vendor_selection(self, category: VendorCategory) -> bool:
        """Check if we need to ask user for vendor selection."""
        pref = self.get_preference(category.value)
        return pref is None or pref.preferred is None


class HypothesisManager:
    """
    Manages hypothesis creation and vendor selection.
    """

    def __init__(
        self,
        project_path: Path,
        ask_user_callback: Optional[Callable[[str, list[dict]], str]] = None,
    ):
        self.project_path = Path(project_path)
        self.preferences = PreferencesManager(project_path)
        self.ask_user = ask_user_callback  # Callback to ask user for choice

    def needs_implementation_decision(self, hypothesis: dict) -> bool:
        """
        Check if a capability hypothesis needs implementation details.

        Returns True if:
        1. Hypothesis involves a vendor category
        2. No preference exists for that category
        """
        category = self._extract_vendor_category(hypothesis)
        if category is None:
            return False

        return self.preferences.needs_vendor_selection(category)

    def _extract_vendor_category(self, hypothesis: dict) -> Optional[VendorCategory]:
        """Extract vendor category from hypothesis if applicable."""
        desc = hypothesis.get("description", "").lower()
        category_str = hypothesis.get("category", "").lower()

        # Check explicit category
        for cat in VendorCategory:
            if cat.value == category_str:
                return cat

        # Infer from description
        category_keywords = {
            VendorCategory.PAYMENT: ["payment", "checkout", "billing", "subscription", "stripe", "paypal"],
            VendorCategory.HOSTING: ["deploy", "hosting", "server", "infrastructure"],
            VendorCategory.DATABASE: ["database", "db", "postgres", "mysql", "mongodb"],
            VendorCategory.EMAIL: ["email", "mail", "smtp", "newsletter"],
            VendorCategory.AUTH: ["auth", "login", "signup", "authentication", "oauth"],
        }

        for cat, keywords in category_keywords.items():
            if any(kw in desc for kw in keywords):
                return cat

        return None

    def get_implementation_options(self, hypothesis: dict) -> list[dict]:
        """Get implementation options for a hypothesis."""
        category = self._extract_vendor_category(hypothesis)
        if category is None:
            return []

        options = DEFAULT_VENDOR_OPTIONS.get(category, [])

        # Filter out avoided vendors
        pref = self.preferences.get_preference(category.value)
        if pref and pref.avoid:
            options = [o for o in options if o["id"] not in pref.avoid]

        return options

    def select_implementation(
        self,
        hypothesis: dict,
        force_ask: bool = False,
    ) -> VendorSelection:
        """
        Select implementation for a hypothesis.

        1. Check preferences first
        2. If no preference, ask user (if callback provided)
        3. If can't ask, use first option as default
        """
        category = self._extract_vendor_category(hypothesis)
        if category is None:
            return VendorSelection(
                category=VendorCategory.PAYMENT,  # placeholder
                selected_vendor="generic",
                source="not_applicable",
            )

        # Check preference
        pref = self.preferences.get_preference(category.value)
        if pref and pref.preferred and not force_ask:
            return VendorSelection(
                category=category,
                selected_vendor=pref.preferred,
                source="preference",
                reason=pref.reason,
            )

        # Need to ask user
        options = self.get_implementation_options(hypothesis)

        if self.ask_user and options:
            prompt = self._build_vendor_prompt(category, hypothesis)
            selected = self.ask_user(prompt, options)

            # Save preference for future
            self.preferences.save_preference(Preference(
                category=category.value,
                preferred=selected,
                reason="User selected during hypothesis creation",
            ))

            return VendorSelection(
                category=category,
                selected_vendor=selected,
                source="user_choice",
            )

        # Default to first option
        default = options[0]["id"] if options else "unknown"
        return VendorSelection(
            category=category,
            selected_vendor=default,
            source="default",
            reason="No preference set, using most common option",
        )

    def _build_vendor_prompt(self, category: VendorCategory, hypothesis: dict) -> str:
        """Build prompt for vendor selection."""
        prompts = {
            VendorCategory.PAYMENT: "Which payment processor should we use?",
            VendorCategory.HOSTING: "Where should we host the application?",
            VendorCategory.DATABASE: "Which database should we use?",
            VendorCategory.EMAIL: "Which email service should we use?",
            VendorCategory.AUTH: "Which authentication provider should we use?",
        }
        return prompts.get(category, f"Which {category.value} provider should we use?")

    def create_implementation_hypothesis(
        self,
        capability_hypothesis: dict,
        vendor_selection: VendorSelection,
    ) -> dict:
        """
        Create an implementation hypothesis from a capability hypothesis.
        """
        vendor_name = vendor_selection.selected_vendor.title()

        return {
            "id": f"{capability_hypothesis['id']}-{vendor_selection.selected_vendor.upper()}",
            "level": HypothesisLevel.IMPLEMENTATION.value,
            "parent_id": capability_hypothesis["id"],
            "description": f"Implement {capability_hypothesis.get('description', '')} using {vendor_name}",
            "vendor": vendor_selection.selected_vendor,
            "vendor_category": vendor_selection.category.value,
            "feasibility": capability_hypothesis.get("feasibility", 0.7),
            "north_star_alignment": capability_hypothesis.get("north_star_alignment", 0.8),
            "estimated_effort": capability_hypothesis.get("estimated_effort", "medium"),
            "builds_component": capability_hypothesis.get("category", "general"),
        }


def is_prescriptive_hypothesis(hypothesis: dict) -> bool:
    """
    Check if a hypothesis is too prescriptive (mentions specific vendors).

    Used to flag hypotheses that should be split into capability + implementation.
    """
    desc = hypothesis.get("description", "").lower()

    # Vendor names that make a hypothesis prescriptive
    vendor_names = [
        "stripe", "square", "paypal", "braintree",  # Payment
        "vercel", "netlify", "aws", "gcp", "azure", "heroku", "railway",  # Hosting
        "supabase", "firebase", "mongodb", "postgres", "mysql", "planetscale",  # Database
        "sendgrid", "mailgun", "ses", "postmark", "resend",  # Email
        "auth0", "clerk", "okta", "cognito",  # Auth
    ]

    return any(vendor in desc for vendor in vendor_names)


def make_capability_hypothesis(prescriptive_hypothesis: dict) -> dict:
    """
    Convert a prescriptive hypothesis to a capability hypothesis.

    "Integrate Stripe for payments" -> "Enable payment processing"
    """
    desc = hypothesis.get("description", "")

    # Mapping of prescriptive patterns to capability descriptions
    capability_mappings = {
        r"integrate\s+\w+\s+(for\s+)?payment": "Enable customers to pay for the product",
        r"set\s*up\s+\w+\s+(for\s+)?hosting": "Deploy and host the application",
        r"implement\s+\w+\s+(for\s+)?auth": "Enable user authentication and authorization",
        r"use\s+\w+\s+(for\s+)?database": "Set up data storage and retrieval",
        r"configure\s+\w+\s+(for\s+)?email": "Enable email notifications and communications",
    }

    import re
    for pattern, capability_desc in capability_mappings.items():
        if re.search(pattern, desc.lower()):
            return {
                **prescriptive_hypothesis,
                "level": HypothesisLevel.CAPABILITY.value,
                "description": capability_desc,
                "original_description": desc,
            }

    # If no pattern matched, just return as-is
    return prescriptive_hypothesis
