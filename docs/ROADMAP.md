# ThousandHand Development Roadmap

## Current Phase: 1 (PRE-EXECUTION DEVELOPMENT) - ~80-85% Complete

---

## Phase Overview

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| 1 | Pre-Execution Development | Framework architecture, core loops | **IN PROGRESS** |
| 2 | Pre-Execution Simulation | Mock simulations with real Claude, BIZ + USER systems | Not Started |
| 3 | Pre-Execution Live Workflows | Temporal integration testing | Not Started |
| 4 | Execution Development (Local) | BUILD/TEST/OPS workflow design | Not Started |
| 5 | Execution Simulation (Local) | Test execution workflows | Not Started |
| 6 | Execution Live Workflows | Temporal execution testing | Not Started |
| 7 | End-to-End Development (Local) | Full cycle integration | Not Started |
| 8 | End-to-End Simulation (Local) | Full cycle testing | Not Started |
| 9 | End-to-End Live Workflows | Full Temporal integration | Not Started |
| 10 | Real World - USER SYSTEM | Build actual user system | Not Started |
| 11 | Real World - BIZ SYSTEM | Build actual business system | Not Started |
| 12 | Real World - Integration | Integrate USER into BIZ | Not Started |
| 13 | Shared Components | Multi-project component sharing | Not Started |

---

## Phase 1: Pre-Execution Development

### Hardened (Cement Dry)
- [x] Four Loops concept (IMAGINATION → INTENT → WORK → EXECUTION)
- [x] REFLECTION feeding into IMAGINATION
- [x] BIZ vs USER system distinction (conceptually)
- [x] Foundation-level vs Imagination-level change types
- [x] Demo mode with scenarios (AUGMENT, OPTIMIZE, PIVOT, vendor-choice)
- [x] Phase callbacks and loading indicators
- [x] Cycle persistence and resume
- [x] BIZ vs USER system detection (with platform/infrastructure distinction)
- [x] Utility subtypes (20 types across 6 categories)
- [x] OPERATE phase with SLA monitoring
- [x] `1kh operate` CLI command (auto-generates operations.md)
- [x] System lifecycle (BUILD → LAUNCH → OPERATE → OPTIMIZE)

### Setting (Cement Wet, Hardening)
- [ ] **Foundation intake flow** ← CURRENT PRIORITY
  - [x] BIZ vs USER system detection
  - [ ] Value surfacing conversation
  - [ ] North Star type confirmation
  - [x] Utility subtype detection
- [ ] Hypothesis definition (needs test conditions)
- [ ] WORK ITEMS layer between HYPOTHESIS and TASKS
- [ ] Task types (BUILD/TEST/OPS conceptually mapped)
- [ ] When to challenge Foundation (REFLECTION triggers)
- [ ] STORY as part of Context in Foundation
- [ ] REFLECTION reading operations.md in OPERATE phase

### Still Wet (Not Hardened)
- [ ] Actual hypothesis generation prompts
- [ ] Task breakdown logic
- [ ] Claude prompt engineering for imagination

### Not Poured Yet (Future Phases)
- [ ] Temporal integration details
- [ ] Real execution (BUILD/TEST/OPS workflows)
- [ ] META-BUILD (factory of factories)
- [ ] Shared components / multi-project

---

## Key Milestones

### Phase 1 Exit Criteria
- Foundation intake properly detects system type
- Foundation documents have clear structure
- Hypothesis generation produces testable hypotheses
- REFLECTION can recommend Foundation-level changes
- Demo scenarios all work correctly

### Phase 2 Entry Requirements
- Phase 1 complete
- Mock data representing realistic human behaviors
- Test cases for both BIZ and USER systems
- Real Claude integration (not mocked)

---

## Deferred Items (Explicitly Not Now)

| Item | Deferred To | Reason |
|------|-------------|--------|
| Shared components | Phase 13 | Need proven pattern first |
| Hypothesis conflict resolution | Phase 2+ | May be edge case, need data |
| Multi-project management | Phase 13 | After single project works |
| Live SLA monitoring integration | Phase 6+ | operations.md framework ready, needs dashboard integration |

---

## Notes

- "Cement settling" principle: Early cycles allow flexibility, later cycles require commitment
- Foundation documents are sensitive, not sacred - changes cascade significantly
- TEST and OPS are both PRODUCTION artifacts (TDD thinking, not environments)
- META-BUILD is experimental - expect failures, plan for human intervention
- Platform/infrastructure that ENABLES other businesses = USER SYSTEM
- System lifecycle: BUILD (feature checklist) → OPERATE (SLA monitoring) → OPTIMIZE
- 20 utility subtypes provide natural KPIs and SLA defaults

---

*Last Updated: 2026-02-04*
