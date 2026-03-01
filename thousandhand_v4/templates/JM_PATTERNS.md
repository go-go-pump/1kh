# Journey Mapping — Reusable Patterns

> Named behavioral patterns that repeat across journey flows.
> Flows reference patterns by name with specific parameters.
> Implementations live in code (Temporal workflows, shared components);
> this document defines the contract.

---

## Pattern: Abandonment

**Purpose:** Re-engage users who exit a flow before completing a critical action.

**Structure:**
```
TRIGGER (record created) →
  WAIT(duration_1) → CHECK(condition) →
    if met: CLOSE
    if not: REMIND(urgency_1, channel) →
  WAIT(duration_2) → CHECK(condition) →
    if met: CLOSE
    if not: REMIND(urgency_2, channel) →
  WAIT(duration_3) → CHECK(condition) →
    if met: CLOSE
    if not: ESCALATE(target, urgency) → CLOSE
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| trigger_table | Table whose creation starts the workflow | `intake_submissions` |
| trigger_event | What causes the workflow to start | `record created` |
| check_field | Field/condition to evaluate | `intake_submissions.status = complete` |
| reminders | Array of {wait_days, urgency, channel} | `[{1d, recommendation, email}, {3d, recommendation, email}]` |
| escalation | {target, urgency} or `none` | `{admin, notice}` |
| link_params | Query params included in reminder links | `client_id, step` |
| for_testing | Override for test execution | `{skip_waits: true}` |

**Urgency Tiers:**
- `recommendation` — Gentle nudge, no pressure (e.g., abandoned before payment)
- `urgent` — Time-sensitive, action required (e.g., abandoned after payment)

**Escalation Tiers:**
- `none` — No escalation, workflow closes silently
- `notice` — Admin notified, low priority (e.g., lead abandoned cart)
- `urgent` — Admin notified, high priority (e.g., paid customer not completing setup)

**Implementation:** Temporal workflow with configurable parameters. In LOCAL test mode, all wait durations become zero for instant execution.

**Invocation Example:**
```
Pattern: Abandonment(
  trigger: intake_submissions.created,
  check: intake_submissions.status = complete,
  reminders: [{1d, recommendation, email}, {3d, recommendation, email}],
  escalation: none,
  link_params: [client_id, last_step]
)
```

---

## Pattern: Session-Recovery

**Purpose:** Restore user state when they return to a page after session loss.

**Structure:**
```
PAGE_LOAD →
  CHECK auth session →
    if valid: RESTORE from Supabase → RESUME
    if invalid:
      CHECK query params (client_id) →
        if present: LOOKUP client →
          if exists: VERIFY (phone token) →
            if verified: CREATE session → RESTORE from Supabase → RESUME
            if not verified: PROMPT retry or restart or contact support
          if not exists: PROMPT start fresh or contact support
        if not present:
          CHECK local storage →
            if data present: RESUME from local storage
            if empty: PROMPT start fresh
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| verify_method | How to verify identity | `phone_token` |
| restore_source | Primary data source for restoration | `supabase` |
| fallback_source | Secondary data source | `local_storage` |
| query_params | Expected URL params for recovery | `[client_id, step]` |
| redirect_on_fail | Where to send unrecoverable users | `/intake/medical` |

**Implementation:** Shared JavaScript module used across all authenticated pages.

**Invocation Example:**
```
Pattern: Session-Recovery(
  verify: phone_token,
  restore: supabase,
  fallback: local_storage,
  params: [client_id, step]
)
```

---

## Pattern: Intake

**Purpose:** Multi-step form with progressive save, local storage backup, and completion gating.

**Structure:**
```
STEP_LOAD →
  CHECK completion status →
    if complete: GATE (redirect or allow re-entry based on context)
    if incomplete: LOAD step view from query param or last saved
  ON_INPUT →
    SAVE to local storage (per field/step)
  ON_NEXT_STEP →
    VALIDATE current step fields →
      if valid: PERSIST to Supabase → ADVANCE step → UPDATE query params
      if invalid: SHOW validation errors
  ON_FINAL_STEP →
    REQUIRE signatures/approvals → PERSIST final → MARK complete → REDIRECT
  ON_PAGE_RELOAD →
    Session-Recovery pattern → RESTORE step from query param or Supabase
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| intake_type | Enum value for this intake | `medical`, `jumpstart`, `fitness`, `nutrition` |
| submission_table | Where form data persists | `intake_submissions` |
| audit_table | Where submission events are logged | `intake_audit_log` |
| completion_redirect | Where to go after completion | `/intake/medical/recommendations` |
| requires_signing | Whether final step needs signature | `true` |
| gating_rules | What happens if already complete | `{paid: modal_choice, unpaid: redirect_to_recommendations}` |

**Implementation:** Shared page component with configuration object per intake type.

**Invocation Example:**
```
Pattern: Intake(
  type: medical,
  table: intake_submissions,
  audit: intake_audit_log,
  redirect: /intake/medical/recommendations,
  signing: true,
  gating: {paid: modal_choice, unpaid: redirect_recommendations}
)
```

---

## Pattern: Payment-Verification

**Purpose:** Verify Square payment independently of webhook, handle edge cases.

**Structure:**
```
PAGE_LOAD →
  GET payment_identifier (from local storage or query param) →
    if unavailable: SHOW "contact support" message
    if available: CALL Square verify →
      if payment not valid: SHOW error → ALLOW redirect back
      if payment valid: SHOW confirmation + receipt → PROCEED to post-payment flow
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| payment_source | Where payment ID comes from | `local_storage`, `query_param` |
| on_success | What to display/do after verification | `show_receipt, load_scheduler` |
| on_failure | Where to redirect on failure | `/intake/medical/recommendations` |
| sandbox_support | Whether to support sandbox mode | `true (via ?sandbox query param)` |

**Implementation:** Shared payment verification module.

**Invocation Example:**
```
Pattern: Payment-Verification(
  source: [local_storage, query_param],
  on_success: show_receipt,
  on_failure: redirect(/intake/medical/recommendations),
  sandbox: true
)
```

---

## Pattern: File-Readiness

**Purpose:** Wait for async file generation, poll with timeout and fallback.

**Structure:**
```
TRIGGER_GENERATION (upstream process) →
  POLL for file (interval, max_duration) →
    SHOW progress message →
    ON_READY: DISPLAY file (embed PDF, download link)
    ON_TIMEOUT: SHOW fallback message → NOTIFY admin
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| file_source | Where the file will appear | `s3_bucket` |
| file_reference | How to identify the file | `lab_order_documents.s3_key` |
| poll_interval | How often to check | `5s` |
| max_duration | How long to wait | `3m` |
| progress_message | What user sees while waiting | `"Processing your lab order..."` |
| timeout_message | What user sees on timeout | `"Issue with processor, admin alerted"` |
| display_mode | How to show the file | `embed_pdf`, `download_link` |

**Implementation:** Shared polling component with configurable display.

**Invocation Example:**
```
Pattern: File-Readiness(
  source: s3,
  reference: lab_order_documents.signed_s3_key,
  poll: 5s,
  timeout: 3m,
  display: embed_pdf,
  fallback: notify_admin
)
```

---

## Pattern: Scheduling

**Purpose:** Embed external scheduler, capture booking event, update state.

**Structure:**
```
EMBED scheduler (Cal.com) with prefill data →
  ON_BOOKING_CREATED →
    UPDATE visit record (status, booking_id, scheduled_at) →
    CONFIRM to user
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| provider | Scheduling platform | `cal.com` |
| event_type | Type of booking | `medical-consult` |
| prefill | Data to pre-fill in scheduler | `{name, email, phone}` |
| on_booking | What to update | `client_visits (status: scheduled, booking_id)` |

**Invocation Example:**
```
Pattern: Scheduling(
  provider: cal.com,
  event_type: medical-consult,
  prefill: {client.name, client.email, client.phone},
  on_booking: update(client_visits, {status: scheduled})
)
```

---

## Pattern: Admin-Escalation-Indicator

**Purpose:** Visually alert admin when a client-side action is overdue, complementing the client-side Abandonment workflow.

**Structure:**
```
PAGE_LOAD (admin ops queue or detail view) →
  For each item:
    CHECK (now - last_state_timestamp) > threshold AND state != expected_state →
      if overdue: APPLY escalation styling (color, badge, messaging)
      if not overdue: DISPLAY normal styling
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| state_field | Field to check current state | `lab_orders.status` |
| expected_state | State that would clear the indicator | `printed` |
| timestamp_field | When the state was last updated | `lab_orders.updated_at` |
| threshold | Time before escalation styling appears | `3d` |
| styling | Visual treatment to apply | `{color: warning, badge: "Action Overdue", message: "Lab order not printed after 3 days"}` |
| complements | The client-side Abandonment flow this mirrors | `abandoned-print-lab-order` |

**Key Distinction:** This is a **frontend-only UI rule** — no Temporal workflow, no side effects. The Temporal Abandonment workflow handles client reminders and eventual admin ticket creation. This pattern just makes the admin aware visually when viewing the queue.

**Implementation:** CSS class + timestamp check in the admin ops queue page rendering logic. For testing, seed data with timestamps older than threshold.

**Invocation Example:**
```
Pattern: Admin-Escalation-Indicator(
  state: lab_orders.status,
  expected: printed,
  timestamp: purchases.created_at,
  threshold: 3d,
  styling: {warning, "Lab Order Not Printed"},
  complements: abandoned-print-lab-order
)
```

---

## Testing Patterns

All patterns support a test mode:

| Pattern | Test-Local Behavior | Test-Prod Behavior |
|---------|--------------------|--------------------|
| Abandonment | Skip all waits, fire checks immediately | Temporal workflow with real waits |
| Session-Recovery | Use test client_id in query params | Same (browser-based) |
| Intake | Playwright fills form, asserts DB state | Same (against live data) |
| Payment-Verification | Use sandbox=true query param | Square sandbox environment |
| File-Readiness | Inject mock file to S3, skip poll | Real Lambda + S3 pipeline |
| Scheduling | Mock Cal.com response, assert DB state | Real Cal.com booking |
| Admin-Escalation-Indicator | Seed data with old timestamps, assert styling applied | Same (against live admin portal) |
