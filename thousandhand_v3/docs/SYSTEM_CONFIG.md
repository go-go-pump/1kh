# System Config (SC) & Product Config (PC)

> **Status:** DRAFT — concepts validated through discussion, not yet implemented.
> **Created:** 2026-02-25
> **Context:** Emerged from convergence work between 1KH (meta-framework) and MVH (first implementation). After building `journey-med-consult-labs-rx` by hand through 1KH's Executor, it became clear that a *generative* layer could produce journey mappings from declarative configuration, eliminating the blank page problem for new business capabilities.

---

## The Hierarchy

```
Product Config (PC)  →  System Config(s) (SC)  →  Journey Mapping(s) (JM)  →  User Flow(s) (UF)
```

Each layer has its own configuration format, its own lifecycle, and produces the layer below it through the builder.

**Product Config (PC):** Describes a product or business and the relationships between its System Configs. Relevant when multiple SCs need to coordinate (shared user pool, cross-journey data references, unified auth). Future architecture — not needed until multiple SCs exist for the same product.

**System Config (SC):** A declarative JSON specification describing a set of business capabilities. Fed into the SC Builder, it produces one or more complete Journey Mappings. The SC speaks the language of the business — capabilities, actors, data, workflows — not the language of infrastructure. This is the primary unit of generation.

**Journey Mapping (JM):** The generated output — docs, IaC, source code, tests, dashboards, seed data, deployment scripts. From the moment a JM is generated, it is a normal 1KH JM. The Executor works on it like any other. The fact that it was generated (vs. hand-built) is historical context, not an ongoing operational constraint.

**User Flow (UF):** Discrete user flows within a journey, as defined in existing 1KH methodology.

---

## Core Principles

### SC is a Generator, Not a Manager

A System Config produces a JM as a starting point — a structured, opinionated, working foundation. Once generated, the JM is owned by the development process. There is no ongoing sync between the SC and its generated JM. Think `create-react-app`, not `react-scripts`. Think `terraform init`, not ongoing `terraform apply`.

This means: generated JMs will diverge from their SC immediately upon first manual edit. That's expected. The value of the SC is skipping the blank page and starting from a working system, not maintaining perfect fidelity forever.

### Capabilities, Not Journeys

The SC author describes **business capabilities** — things the system should do from a user's perspective. The author does NOT define journey boundaries. The SC Builder's planning pass decomposes capabilities into JMs based on 1KH patterns (coherent end-to-end flows across actors).

The SC author thinks: "I want users to sign up, submit intake data, and get help when stuck."
The builder thinks: "That's two journeys — an onboarding journey and an issue-resolution journey."

The builder proposes JM decomposition. The author reviews and approves. If the split doesn't make sense, the author adjusts capabilities and the builder re-plans.

### Templates for Structure, LLM for Business Context

The builder uses a hybrid generation strategy:

**Deterministic (template-driven):** Project scaffolding, file layout, IaC definitions (SST config for Cognito, Aurora, S3, API Gateway, Lambda), auth flows, portal shells, navigation, routing, auth guards, testing dashboards, docker-compose files, deploy scripts, database migration framework.

**Semi-deterministic (template + variable substitution):** Intake forms (templated structure, SC-defined fields), user profile pages, admin CRUD views, data model migrations (table SQL from SC entity definitions), email templates (structure known, copy from SC or human input).

**LLM-generated (business context dependent):** Marketing site copy and layout, landing page design, conditional business logic, workflow decisions (what happens after intake?), business-specific admin tooling.

Over time, more patterns become deterministic as templates mature. The ratio shifts toward templates and away from LLM generation, making output more predictable and token-efficient.

### Infrastructure by Inference

The SC does not declare infrastructure requirements. The builder *infers* infrastructure from the flavor and capabilities. An intake portal with auth implies Cognito + a users table + S3 for documents + SES for OTP emails. The builder knows this because the flavor's template encodes those infrastructure requirements.

The SC can explicitly override defaults (e.g., specify a particular auth method or storage provider), but if it doesn't, the Founder's Playbook tech stack (see `ARCHITECTURE_TEMPLATE.md` → Preferred Tech Stack) provides the opinionated defaults.

The builder also checks whether system infrastructure already exists. If this is the first SC deployed to a system, JM generation includes the full infrastructure bootstrap (SST config, Cognito user pool, Aurora cluster, S3 buckets, docker-compose file, project scaffolding). If infrastructure exists from a prior SC/JM, only journey-specific artifacts are generated.

---

## SC Schema (Draft)

### Common Header (All Flavors)

Every SC shares a common header regardless of flavor:

```json
{
  "sc_version": "1.0.0",
  "flavor": "intake-portal",
  "journey_key_prefix": "acme-consult",
  "description": "Virtual consultation intake for Acme Consulting",
  "actors": [
    {
      "role": "client",
      "description": "End user seeking consultation services"
    },
    {
      "role": "admin",
      "description": "Operations staff reviewing intakes and managing users"
    }
  ],
  "human_inputs_required": [
    "Business-specific intake form copy",
    "Legal disclaimer / terms of service text",
    "Branding assets (logo, colors)"
  ],
  "tech_stack_overrides": {}
}
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `sc_version` | Yes | Schema version for this SC |
| `flavor` | Yes | Flavor identifier — determines which template set the builder uses and which fields are required in the body |
| `journey_key_prefix` | Yes | Namespace prefix for generated JM keys (e.g., `acme-consult` → `journey-acme-consult-onboarding`) |
| `description` | Yes | Human-readable description of the business capability |
| `actors` | Yes | Role definitions — who interacts with the system |
| `human_inputs_required` | Yes | Things the builder cannot generate — requires a person. If all provided upfront, the generated JM is production-ready. If some missing, JM is ready for local UAT with placeholders. |
| `tech_stack_overrides` | No | Explicit overrides to the default Founder's Playbook stack. Empty = use all defaults. |

### Flavor-Specific Body

The flavor declaration determines which additional fields are required. Each flavor has its own schema with required fields and nice-to-have fields. If nice-to-have fields are omitted, the builder uses intelligent defaults or LLM generation.

The builder validates: if the SC has not met the minimum threshold of information for its declared flavor, it is rejected with a clear note explaining what's required and what's nice-to-have. If sufficient, the builder fills in the rest and proceeds.

---

## Flavor: `intake-portal` (Minimum Viable SC)

The first supported flavor. Produces a complete system: marketing landing page, user signup with identity verification, intake form, client portal, and admin portal.

### Capabilities Produced

| Capability | Actor(s) | Description |
|------------|----------|-------------|
| Marketing landing | Visitor | Landing page with value proposition, CTA to signup |
| User signup + verification | Client | Email-based signup, OTP verification, account creation |
| Intake submission | Client | Multi-field intake form, validation, submission |
| Client portal | Client | Dashboard, intake review/edit, user profile, support page |
| Admin portal | Admin | Dashboard (new signups, pending intakes), user management, intake review, issues management |
| Support channel | Client, Admin | Issue submission, admin queue, response thread, resolution |

### Expected JM Decomposition

The builder's planning pass will typically decompose `intake-portal` into:

**JM-1: `journey-{prefix}-onboarding`** — Marketing landing → signup → OTP verification → intake form → submission → client dashboard. On admin side: notification of new signup, intake review workflow. This is the primary journey. If it's the first JM in the system, it triggers infrastructure bootstrap.

**JM-2: `journey-{prefix}-issue-resolution`** — Client submits issue from portal → admin sees issue in queue → admin responds → client sees response → resolution. Assumes JM-1 infrastructure exists.

### Flavor-Specific Schema

```json
{
  "flavor": "intake-portal",
  "capabilities": {
    "marketing": {
      "headline": "Expert consultation tailored to your needs",
      "value_props": [
        "Personalized approach",
        "Board-certified professionals",
        "Secure and confidential"
      ],
      "cta_text": "Get Started"
    },
    "identity_verification": {
      "method": "email_otp",
      "fallback": null
    },
    "intake": {
      "entities": [
        {
          "name": "client_intake",
          "fields": [
            { "key": "full_name", "type": "text", "required": true, "label": "Full Name" },
            { "key": "email", "type": "email", "required": true, "label": "Email Address" },
            { "key": "phone", "type": "phone", "required": false, "label": "Phone Number" },
            { "key": "reason_for_visit", "type": "textarea", "required": true, "label": "Reason for Visit" },
            { "key": "preferred_date", "type": "date", "required": false, "label": "Preferred Consultation Date" }
          ]
        }
      ],
      "on_submit": {
        "notify_admin": true,
        "confirmation_email": true,
        "redirect_to": "client_dashboard"
      }
    },
    "client_portal": {
      "pages": ["dashboard", "intake_review", "profile", "support"]
    },
    "admin_portal": {
      "pages": ["dashboard", "user_management", "intake_review", "issues_management"]
    },
    "support": {
      "enabled": true,
      "severity_levels": ["LOW", "MEDIUM", "HIGH"]
    }
  }
}
```

### Required vs. Nice-to-Have Fields

**Required (SC rejected without these):**

| Field | Why |
|-------|-----|
| `flavor` | Builder needs to know which template set to load |
| `actors` (at least 2) | Need at least a client and admin role |
| `intake.entities` (at least 1 entity with fields) | Core purpose of the flavor — no intake fields, no intake portal |
| `identity_verification.method` | Auth strategy must be explicit |

**Nice-to-Have (builder uses defaults or LLM generation if omitted):**

| Field | Default if omitted |
|-------|-------------------|
| `marketing.headline` | LLM generates from `description` |
| `marketing.value_props` | LLM generates from `description` and `intake.entities` |
| `intake.on_submit` | `{ notify_admin: true, confirmation_email: true, redirect_to: "client_dashboard" }` |
| `client_portal.pages` | All standard pages enabled |
| `admin_portal.pages` | All standard pages enabled |
| `support` | Enabled with default severity levels |
| `tech_stack_overrides` | Founder's Playbook defaults (Aurora, Cognito, SST v3, etc.) |

---

## Builder Workflow

```
1. INGEST
   Input: SC JSON (or MD draft → threshold check → mapped to SC JSON)
   Validate: required fields present for declared flavor
   Reject if insufficient (with clear requirements list)

2. PLAN
   Decompose capabilities into JM(s)
   Check: does system infrastructure exist?
   If no: first JM includes infrastructure bootstrap
   If yes: JMs are additive only
   Output: proposed JM decomposition for author review

3. REVIEW (Human)
   Author reviews proposed JM split
   Approve, adjust capabilities, or regenerate plan

4. GENERATE
   For each approved JM, produce:
   - Journey Mapping doc (JM markdown)
   - User Flow docs (UF markdowns per flow)
   - Architecture updates (if infra bootstrap)
   - IaC definitions (SST config, docker-compose)
   - Database migrations (from entity definitions)
   - Source code (Lambda functions, portal pages, admin pages)
   - Testing dashboard (step-by-step journey visualization)
   - Seed data and test fixtures
   - Deployment scripts (bash)
   - Human input placeholders (marked clearly for items in human_inputs_required)

5. OUTPUT
   Generated JM(s) ready for local UAT (docker-compose up → test)
   If all human inputs were provided: potentially production-ready
   If human inputs pending: UAT-ready with placeholders

6. HANDOFF
   JM is now a normal 1KH JM
   Executor takes over for iteration, bug fixes, enhancements
   SC is historical reference only — no ongoing sync
```

---

## SC Ingestion: Draft-to-SC Pipeline

For the initial implementation, SCs are authored through a draft document (markdown) rather than raw JSON. The pipeline:

1. **Author writes an MD draft** describing the business capability in natural language. No required structure — just describe what you want.

2. **Builder evaluates the draft** against the minimum threshold for the declared (or inferred) flavor. If the draft doesn't contain enough information to populate required fields, it's rejected with a clear note: "Here's what's required, here's what's nice-to-have, here's what's missing."

3. **Builder maps the draft to SC JSON.** LLM extracts structured data from the natural language description, fills in defaults for nice-to-have fields, and produces a valid SC JSON.

4. **Author reviews the SC JSON.** Approves, edits, or rewrites the draft and resubmits.

This is analogous to existing 1KH flows: DRAFT → breakdown (like DRAFT → ITEMS in current 1KH) and ITEMS → grooming (like SC JSON → builder planning).

Future: a CLI wizard (`kh sc create`) that walks through the required fields interactively. Further future: a web-based wizard UI.

---

## When to Create an SC

**Create an SC when:** You have a repeatable business capability that you want to stand up quickly — either for a new product, a new client, or a new offering within an existing product. The SC is worth the investment when the capability is substantial enough that hand-building it from scratch would take days or weeks.

**Don't create an SC when:** You're making a small enhancement, fixing a bug, or adding a feature to an existing JM. That's Executor work, not SC work.

**Before or after the first JM?** The practical pattern: **build the first JM of a type by hand** using the Executor and 1KH framework. Learn what the journey actually requires through implementation. Then **extract an SC from the realized JM** so that future instances of similar capabilities can be generated. The first time is discovery. The SC captures that discovery for reuse.

Over time, as SC templates mature and cover more patterns, it becomes viable to create SCs *before* hand-building — especially for well-understood flavors like `intake-portal` where the patterns are established.

---

## Relationship to Existing 1KH Concepts

| 1KH Concept | Relationship to SC |
|-------------|--------------------|
| **Orchestrator** | Handles imagination → intent → work (planning and sequencing). The SC Builder may *use* the Orchestrator for its planning pass, but they are separate concerns. The Orchestrator plans; the SC Builder generates. |
| **Executor** | Produces artifacts (code, docs, tests). The SC Builder delegates to the Executor for actual artifact generation. After SC generation, the Executor takes over for all subsequent iteration. |
| **Journey Mapping** | SC output. A generated JM is identical in structure and governance to a hand-built JM. |
| **User Flow** | Lives inside JMs as it does today. SC generation produces UFs as part of JM output. |
| **Shared Components** | Reusable building blocks (auth patterns, payment flows, notification systems, portal templates) that SCs *reference* and the builder *consumes*. Shared components are ingredients; SCs are recipes; JMs are the dish. |
| **Founder's Playbook** | The opinionated tech stack that the builder targets. SCs are stack-agnostic in theory, but the builder generates for the Playbook stack by default. |
| **Testing Dashboard** | Generated as part of JM output. Each JM gets dashboard entries for step-by-step UAT. |

---

## Future Considerations

**New flavors:** Each new flavor requires a template set and a flavor-specific schema. Flavors are added as patterns are proven through hand-built JMs. Examples that may emerge: `virtual-consultation` (scheduling, video/chat, follow-up automation), `product-catalog` (browsable catalog, cart, checkout), `monitoring-dashboard` (site health, analytics, alerting).

**Product Config (PC):** Becomes relevant when multiple SCs need to coordinate within one product. Defines shared infrastructure, cross-SC data relationships, unified auth, and deployment topology. Not needed until a product has 2+ SCs.

**Self-healing capabilities:** Future pattern where a generated system can review error logs, rewrite tests, and redeploy. Would be an optional SC-level configuration: enabled or disabled per capability, and ignored if the pattern isn't mature.

**SC versioning:** SCs themselves are versioned. When a flavor's template improves, you can regenerate a fresh JM from the same SC to get the updated patterns — but only if the JM hasn't been manually edited (or if you're willing to discard edits and start fresh).

**Immutability model:** Generated JMs are versioned artifacts. To update a JM via SC: create a new version (which replaces the prior). Direct edits to the JM are always allowed but mean the JM has diverged from its SC. No automatic reconciliation — that's a conscious tradeoff the author makes.
