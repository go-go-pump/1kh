# User Flow Catalog

> The "Book of Life" for this project. Each entry describes a discrete user journey — what a person experiences, not what we build. Managed by the AI during grooming; maintained across sessions as the living source of truth for flow coverage.

---

## How Flows Work

**USER FLOWS are not TASKS.** Tasks describe what to BUILD. User flows describe what a PERSON EXPERIENCES. A single user flow may span multiple tasks. A single task may serve multiple user flows. Some tasks (infrastructure, documentation, chores) serve no flow at all — that's fine.

**Lifecycle states:**

| State | Meaning |
|-------|---------|
| `NEW` | First-time user encountering this journey |
| `EXISTING` | Returning user with history |
| `RETURNING_INTERRUPTED` | User resuming an abandoned or incomplete journey |

**Verification modes:**

| Mode | When to use |
|------|------------|
| `playwright` | Fully automatable end-to-end browser test |
| `manual` | Requires human judgment (visual design, subjective quality) |
| `mixed` | Automated steps with manual checkpoints |

---

## Flow Catalog

<!-- Flows are added and updated by the AI during grooming. Each flow follows this format:

### [Flow Name]
- **ID:** flow-[short-name]
- **Lifecycle:** NEW | EXISTING | RETURNING_INTERRUPTED
- **Description:** [One sentence: who does what and why]
- **Steps:**
  1. [Step description]
  2. [Step description]
  ...
- **Serves tasks:** [task-id-1, task-id-2]
- **Verification:** playwright | manual | mixed
- **Test file:** [path to test file, or "none" if not yet created]
- **Status:** DEFINED | IMPLEMENTED | TESTED | VERIFIED

-->

_No flows defined yet. Flows will be identified and added during grooming as tasks are processed._

---

## Coverage Summary

| Status | Count |
|--------|-------|
| Defined | 0 |
| Implemented | 0 |
| Tested | 0 |
| Verified (closing ceremony) | 0 |

---

*This catalog is the verification checklist for the Closing Ceremony. When all CRITICAL and HIGH flows are VERIFIED, the system is ready for UAT.*
