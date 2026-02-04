# THOUSANDHAND BACKLOG
## Work Items Queue

---

## How This Works
- Items are atomic and completable
- Status: TODO | IN_PROGRESS | BLOCKED | DONE
- Priority: P0 (now) | P1 (this week) | P2 (post-launch) | P3 (later)
- Autonomy: FULL | REVIEW | CONFIRM (per Constitution)

---

## PRIORITY 1: LAUNCH

### Infrastructure Discovery (P0)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| L001 | Inventory current Man Plan build state | BLOCKED | CONFIRM | Paul input | What exists? What's the tech stack? |
| L002 | Document current Kajabi setup | BLOCKED | FULL | Paul access | Pages, products, integrations |
| L003 | Audit AWS infrastructure | BLOCKED | FULL | AWS creds | SES, hosting, databases |
| L004 | Map Stripe product/pricing structure | BLOCKED | FULL | Stripe access | What's configured? |
| L005 | List all domains and DNS config | BLOCKED | FULL | Registrar access | What points where? |

### Man Plan - Free Tier (P0)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| MP-F001 | Define Free tier feature set | TODO | REVIEW | L001 | What exactly is included? |
| MP-F002 | Create Free tier onboarding flow | TODO | REVIEW | MP-F001 | First-time user experience |
| MP-F003 | Build basic nutrition plan generator | TODO | REVIEW | L001 | Meal plans based on inputs |
| MP-F004 | Build basic exercise plan generator | TODO | REVIEW | L001 | Workout plans based on inputs |
| MP-F005 | Implement basic RADAR | TODO | REVIEW | L001 | Recommendations and escalations |
| MP-F006 | Create Free tier dashboard | TODO | REVIEW | MP-F003, MP-F004, MP-F005 | Central user interface |

### Man Plan - Premium Tier (P0)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| MP-P001 | Define Premium tier feature set | TODO | CONFIRM | MP-F001 | What's the upgrade value? |
| MP-P002 | Set Premium pricing | BLOCKED | CONFIRM | Paul decision | Monthly? Annual? One-time? |
| MP-P003 | Create Premium upsell flow | TODO | REVIEW | MP-P001, MP-P002 | Conversion from Free |
| MP-P004 | Build Premium-exclusive features | TODO | REVIEW | MP-P001, L001 | Advanced customization |
| MP-P005 | Implement payment integration | BLOCKED | CONFIRM | L004, MP-P002 | Stripe checkout |

### Chat Capabilities (P0 - Limited)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| CH001 | Define limited chat scope | DONE | REVIEW | - | See outputs/CH001_chat_scope.md |
| CH002 | Build chat interface | TODO | REVIEW | CH001 | UI component |
| CH003 | Implement chat backend | TODO | REVIEW | CH001 | Message handling, AI integration |
| CH004 | Create chat guardrails | TODO | REVIEW | CH001 | What it can't do, escalation triggers |

### Book Sales (P0)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| BK001 | Finalize MCL for sale | TODO | REVIEW | - | Final formatting, ISBN if needed |
| BK002 | Create book sales page | TODO | REVIEW | BK001 | Landing page, purchase flow |
| BK003 | Set book pricing | BLOCKED | CONFIRM | Paul decision | Price point |
| BK004 | Implement book delivery | TODO | REVIEW | BK001, L004 | Digital delivery after purchase |
| BK005 | Write book sales copy | DONE | FULL | BK001 | Headlines, bullets, testimonials - see outputs/ |

### PHO Services (P0)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| PHO001 | Define PHO service offerings | DONE | REVIEW | - | See outputs/PHO001_service_definitions.md |
| PHO002 | Set PHO pricing | BLOCKED | CONFIRM | Paul decision | Per service pricing |
| PHO003 | Create PHO sales pages | TODO | REVIEW | PHO001, PHO002 | One per service |
| PHO004 | Build PHO booking flow | TODO | REVIEW | PHO001 | Calendar integration |
| PHO005 | Create PHO intake forms | TODO | REVIEW | PHO001 | Pre-session data collection |

### Medical Consults (P0)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| MED001 | Define medical service offerings | BLOCKED | CONFIRM | Wife input | What services, what states |
| MED002 | Set medical pricing | BLOCKED | CONFIRM | Wife/Paul | Per service pricing |
| MED003 | Create medical sales pages | TODO | REVIEW | MED001, MED002 | Compliant copy |
| MED004 | Build medical intake flow | TODO | REVIEW | MED001 | HIPAA-appropriate |
| MED005 | Create physician handoff process | TODO | CONFIRM | MED001 | How Paul hands to wife |

### Marketing - Post Launch (P1)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| MKT001 | Build cold email campaign | TODO | REVIEW | Launch complete | Sequence, copy, targeting |
| MKT002 | Set up cold email infrastructure | BLOCKED | FULL | AWS creds | Warming, reputation management |
| MKT003 | Design Auto DM strategy | TODO | REVIEW | - | Platforms, triggers, copy |
| MKT004 | Implement Auto DM system | TODO | REVIEW | MKT003 | Technical execution |
| MKT005 | Create MvH Episode 1 script | DONE | FULL | - | Insulin resistance topic - see outputs/ |
| MKT006 | Create MvH Episode 1 assets | TODO | FULL | MKT005 | Thumbnails, descriptions |
| MKT007 | Create MvH Episode 2 script | TODO | FULL | - | Topic TBD |
| MKT008 | Create MvH Episode 2 assets | TODO | FULL | MKT007 | Thumbnails, descriptions |

---

## DISCOVERED WORK (Add as found)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| | | | | | |

---

## VALIDATION TASKS (Self-check items)

| ID | Task | Status | Autonomy | Dependencies | Notes |
|----|------|--------|----------|--------------|-------|
| V001 | Review all copy for Paul voice | TODO | FULL | Any copy task | Does it sound like him? |
| V002 | Test all user flows | TODO | FULL | Any UI task | Does it work? |
| V003 | Validate mobile responsiveness | TODO | FULL | Any UI task | Works on phone? |
| V004 | Check compliance on medical pages | TODO | CONFIRM | MED003 | Legal review needed? |
| V005 | Verify pricing displays correctly | TODO | FULL | Payment tasks | No errors in checkout |

---

## QUICK WINS (Can do now without blockers)

### COMPLETED THIS SESSION:
- ✅ **BK005** - Book sales copy → outputs/BK005_book_sales_copy.md
- ✅ **CH001** - Chat scope definition → outputs/CH001_chat_scope.md
- ✅ **PHO001** - PHO service definitions → outputs/PHO001_service_definitions.md
- ✅ **MKT005** - Episode 1 script (insulin resistance) → outputs/MKT005_episode1_script.md

### STILL AVAILABLE:
5. Draft email sequences for cold outreach
6. Create content calendar framework
7. Design RADAR recommendation logic
8. Write FAQs for Man Plan
9. Episode 2 script
10. Thumbnail designs (descriptions)

---

## BACKLOG NOTES

- This backlog will grow as work reveals more work
- Items shift priority based on discoveries
- Blocked items get unblocked when Paul provides input or credentials
- Done items move to COMPLETED.md with outcomes
