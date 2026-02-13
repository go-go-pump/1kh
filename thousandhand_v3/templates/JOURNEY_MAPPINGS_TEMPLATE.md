# Journey Mappings — [PROJECT_NAME]

> The Book of Journeys. This document defines the end-to-end user journeys that constitute the product.
> Every task, user flow, and test traces back to a step in a journey.
> This is the primary reference for grooming, execution, and delivery.

## How This Document Works

Journey Mappings define the complete lifecycle of a user experience from trigger to outcome.
They are the **base truth** — features, tasks, and tests derive from journey steps.

### Hierarchy
- **Journey Mapping** → The full movie (multiple actors, systems, time boundaries)
- **User Flow** → A scene within the movie (single actor, specific system interaction)
- **Task** → A buildable unit that implements part of a user flow

### Format Reference

Each journey follows this structure:
- **Journey Header**: ID, actors, trigger, outcome, status
- **Steps**: High-level sequence with data lineage (Produces/Reads)
- **User Flows**: Detailed flow-level specification per step
- **Data Lineage**: Table-level read/write map across all steps
- **Paths**: Happy-major, minor, sad paths (mapped or unmapped)
- **External Dependencies**: Functions, services, integrations outside the flows

Each User Flow follows this structure:
- **Header**: Flow ID, scenario, reads, writes, patterns used, dependencies, leads-to
- **Steps**: Numbered sequence (e.g., 1.0, 1.1, 1.2)
- **Notes**: Edge cases, business rules, recovery logic keyed to step numbers

### Pattern References
Flows reference named patterns defined in JM_PATTERNS.md:
- Patterns are reusable behavioral templates (e.g., Abandonment, Session-Recovery)
- Multiple patterns can apply to a single flow
- Pattern parameters are specified inline

---

## Journey Template

### JOURNEY: [Name]
```
ID: journey-[kebab-case-id]
Actors: [Actor1, Actor2, System (list systems)]
Trigger: [What starts this journey]
Outcome: [What the end state looks like]
Status: [Which steps are implemented]
```

#### STEPS

```
STEP N | Actor: [Who] | System: [Where]
  Action: [What happens]
  Produces: [table1 (fields), table2 (fields)]
  Reads: [table3, table4]
  Validates: [What can be asserted]
  Test-local: [How to test locally]
  Test-prod: [How to test in production]
```

#### USER FLOWS

```
User Flow ([flow-id])
  Scenario: [When/why this flow occurs]
  Reads: [tables]
  Writes: [tables]
  Patterns: [Pattern1(params), Pattern2(params)]
  Depends-on: [prior flow that must complete]
  Leads-to: [next flow or GATEWAY]

[Numbered steps]
  1.0 [Step description]
  1.1 [Substep description]
  1.2 [Substep description]

Notes ([flow-id])
  [Edge cases and business rules keyed to step numbers]
```

#### DATA LINEAGE
```
[table] ──> step N (WRITE) ──> step M (READ)
```

#### PATHS
```
Happy-Major: Steps 1→2→3→...→N (full cycle)
Known Minor: [description]
Known Sad: [description]
Unmapped: [ ] [description]
```

#### EXTERNAL DEPENDENCIES
```
[Function/Service name] | Status: [exists/planned/mocked] | Called by: [step N]
```

---

## Usage Notes

- Copy this template for each new journey mapping document
- Replace `[PROJECT_NAME]` in the header with your actual project name
- Use kebab-case for IDs (e.g., `journey-user-onboarding`)
- Keep journey definitions concise; user flows contain detailed specifications
- Data Lineage should map the complete read/write sequence across all steps
- Mark unmapped paths clearly; they represent future work or known gaps
- External Dependencies ensure third-party integrations are documented and tracked
