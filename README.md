# 1KH — Thousand Hands v4

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Standards](https://img.shields.io/badge/version-v4-green)](./thousandhand_v4/)
[![Part of PUMP](https://img.shields.io/badge/ecosystem-PUMP-blue)](https://github.com/pump-engine)

**Design-first AI governance standards for autonomous development.**

1KH is the standards engine that powers [PUMP](https://github.com/pump-engine/god-mode). It provides the protocols, templates, patterns, and staging documents that transform a raw prompt into a supercharged PUMP — a prompt pre-loaded with business context, execution standards, quality gates, and shared component awareness.

> **Open source.** These standards benefit everyone. If you're an indy founder using AI to build systems, use them freely.

---

## Installation

```bash
git clone git@github.com:pump-engine/1kh.git
```

No build step. 1KH is a spec repo — protocols and templates consumed by the PUMP pipeline and by humans directly.

---

## What's Inside

```
thousandhand_v4/
├── PUMP.md              # Pointer to the master spec (lives in god-mode repo)
├── protocols/           # How to execute and close
│   ├── EXECUTOR_STANDARDS.md
│   └── CLOSING_CEREMONY.md
├── templates/           # Copied to projects on init
│   ├── MASTER_GROOMING_STANDARDS.md
│   ├── MASTER_DELIVERY_HANDOFF_TEMPLATE.md
│   ├── ARCHITECTURE_TEMPLATE.md
│   ├── JOURNEY_MAPPINGS_TEMPLATE.md
│   ├── USER_FLOWS_TEMPLATE.md
│   ├── JM_COMPLETENESS_CHECKLIST.md
│   └── JM_PATTERNS.md
├── patterns/            # Reusable behavioral templates
│   └── JM_PATTERNS.md
├── staging/             # Future protocols (not yet active)
│   ├── OPENING_CEREMONY.md
│   ├── ORCHESTRATOR_STANDARDS.md
│   └── INTERMEDIATE_ARTIFACTS.md
└── docs/                # (future) per-version architecture decisions
```

---

## How 1KH Fits Into PUMP

```
God Mode (catches founder intent)
    │
    ├── loads standards from ──→ 1KH (this repo)
    ├── resolves components from ──→ Greenspaces
    │
    ▼
OpenClaw (executes with governance)
```

1KH answers: "What standards, protocols, and templates should govern this execution?" God Mode answers: "What does the founder want?" Greenspaces answers: "What building blocks already exist?"

---

## The Three Repos

| Repo | Purpose | Visibility |
|------|---------|-----------|
| [god-mode](https://github.com/pump-engine/god-mode) | Entry point + PUMP master spec | Private |
| **1kh** (this repo) | Standards engine | Public |
| [greenspaces](https://github.com/pump-engine/greenspaces) | Shared components + services | Public |

---

## Core Concepts

### Five-Dimensional Execution Sequencing

The heart of 1KH. Every execution follows this priority model:

1. **Path:** Happy → Critical Escalation → Remaining
2. **Work Unit:** Journey Mapping → User Flow → Task
3. **Stage:** Local → Mixed → Production
4. **Layer:** Data → App → UX Minimal → UX Final
5. **Scope:** Core/Shared → Specialized

Complete each dimension before advancing.

### Journey-First Development

Start with the journey, derive the features. Every line of code traces back to a journey step. Every test verifies a user experience. The User Flow Catalog is the book of life.

### Execution Contexts

**LOCAL** — SQLite, mock auth, local filesystem, mocked services, localhost.
**MIXED** — Real database, configured auth, sandbox payments, seed into actual DB.
**PRODUCTION** — Everything live, explicit approval for payments, clearly removable seed data.

---

## For MilliPrimes

This repo is public because the standards benefit everyone. If you're an indy founder using AI to build systems, these protocols and templates will help you ship faster with fewer feedback loops.

The MilliPrime Co-Op is a network of operators sharing primitives, infrastructure, and culture. Read the [Manifesto](https://github.com/pump-engine/god-mode) to understand the philosophy. Read the [Greenspaces catalog](https://github.com/pump-engine/greenspaces) to see what shared components exist.

The thesis: **Co-ops beat empires when creation is cheap.** Shared primitives create leverage. That's what this repo provides.

---

## History

| Version | Era | Focus |
|---------|-----|-------|
| v0-v2 | 2024 | Exploration — simulation engines, Python CLIs, orchestration blueprints |
| v3 | 2025 | Executor — bash CLI (`kh`), filesystem workflows, journey-first methodology |
| **v4** | 2026 | **PUMP — spec-as-governance, supercharging pipeline, co-op infrastructure** |

Archives of v0-v3 are preserved locally but not published (gitignored). The institutional knowledge lives in v4.
