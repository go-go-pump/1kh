# Contributing to 1KH

1KH is the standards engine for the PUMP ecosystem. It defines the protocols, templates, and patterns that govern how AI-driven development actually works. Contributions that improve these standards help every project in the ecosystem.

## What Lives Here

- **Protocols** — Executor Standards, Closing Ceremony (how work gets done and verified)
- **Templates** — Architecture, Journey Mappings, User Flows, Grooming, Delivery (what gets produced)
- **Patterns** — Reusable behavioral templates (Journey Mapping patterns, etc.)
- **Staging** — Future protocols not yet active (Opening Ceremony, Orchestrator, etc.)

## How to Contribute

### Proposing a Standard Change

Standards affect every project downstream. Changes should be deliberate:

1. **Open an issue** describing what's missing, broken, or unclear
2. Include concrete examples — "here's where the current standard failed me"
3. Propose a solution, or ask for discussion
4. If approved, fork and submit a PR to `main`

### Adding a New Template

1. Create the template in `thousandhand_v4/templates/`
2. Follow the existing naming convention: `UPPERCASE_WITH_UNDERSCORES.md`
3. Include a header block explaining when and how to use it
4. Update the README structure diagram
5. Submit a PR tagged `standards:template`

### Fixing Typos / Clarifications

Small fixes are welcome — fork, fix, PR. No issue needed.

## Branch Naming

| Prefix | Use |
|--------|-----|
| `standards/` | Changes to protocols or templates |
| `pattern/` | New or updated patterns |
| `docs/` | Documentation improvements |
| `fix/` | Corrections to existing standards |

## Commit Messages

```
<type>: <short description>
```

Types: `standards`, `pattern`, `docs`, `fix`

## Philosophy

1KH is opinionated by design. Not every suggestion will be accepted. The bar is: "Does this make every project that uses 1KH better?" If yes, it's in. If it's a personal preference, it stays out.

## Code of Conduct

Same as the co-op: be virtuous, be ferocious, build systems. Respect other contributors. Disagree on ideas, not people.
