# MilliPrime Architecture: n8n + Opportunity Manager

## Project Overview

**Business:** Man vs Health - Men's metabolic health platform
**Owner:** Paul (Engineer/Founder) + Wife (Physician, licensed FL/NC/SC)
**Target:** Men 40+ with insulin resistance and metabolic dysfunction

**Core Principle:** Data vs Execution Separation
- **Supabase** = Source of truth for business logic (what to do)
- **n8n** = Execution engine (how to do it)
- **Admin** = UI for managing business logic
- **Marketing/App** = Customer-facing interfaces

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ADMIN APPLICATION                             │
│                     (Opportunity Manager)                            │
│                                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │Opportunities│ │   Flows     │ │  Templates  │ │  Resources  │   │
│  │  Manager    │ │  Builder    │ │   Editor    │ │  Manager    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ CRUD Operations
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SUPABASE                                     │
│                   (Source of Truth)                                  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BUSINESS LOGIC TABLES                                        │   │
│  │ • opportunities  - What we sell                              │   │
│  │ • flows          - What happens after purchase               │   │
│  │ • flow_steps     - Individual steps in a flow                │   │
│  │ • templates      - Email/SMS content                         │   │
│  │ • resources      - People who fulfill (PHO, MED, COACH)      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ OPERATIONAL TABLES                                           │   │
│  │ • clients        - Customer records                          │   │
│  │ • orders         - Purchases made                            │   │
│  │ • tasks          - Assigned work for resources               │   │
│  │ • intake_responses - Form submissions                        │   │
│  │ • workflow_logs  - Execution history (written by n8n)        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Reads config, Writes logs
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           n8n                                        │
│                    (Execution Engine)                                │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ GENERIC WORKFLOWS (not per-offer)                            │   │
│  │                                                               │   │
│  │ 1. Fulfillment Executor                                      │   │
│  │    - Reads flow definition from Supabase                     │   │
│  │    - Executes steps dynamically                              │   │
│  │    - Handles: email, sms, wait, task, check, branch          │   │
│  │                                                               │   │
│  │ 2. Scheduled Jobs                                            │   │
│  │    - Daily reminder checks                                   │   │
│  │    - Appointment notifications                               │   │
│  │    - Stale task escalation                                   │   │
│  │                                                               │   │
│  │ 3. Webhook Receivers                                         │   │
│  │    - Square payment.completed                                │   │
│  │    - Supabase triggers (intake, etc.)                        │   │
│  │    - Manual triggers from Admin                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Sends via
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                 │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ AWS SES  │  │  Twilio  │  │  Square  │  │  Google  │           │
│  │ (Email)  │  │  (SMS)   │  │(Payments)│  │(Calendar)│           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Supabase)

### Business Logic Tables

```sql
-- ============================================
-- OPPORTUNITIES
-- What we sell (offers, products, services)
-- ============================================
CREATE TABLE opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identity
  name TEXT NOT NULL,                    -- "JumpStart Session"
  slug TEXT UNIQUE NOT NULL,             -- "jumpstart" (URL-safe)
  description TEXT,                      -- Short description for internal use
  
  -- Pricing
  price_cents INTEGER NOT NULL,          -- 9700 = $97.00
  currency TEXT DEFAULT 'USD',
  
  -- Payment Integration
  square_catalog_id TEXT,                -- Square catalog item ID
  square_variation_id TEXT,              -- Square variation ID (if applicable)
  payment_link_url TEXT,                 -- Generated Square payment link
  
  -- Flow Assignment
  flow_id UUID REFERENCES flows(id),     -- Which flow executes after purchase
  
  -- Marketing
  landing_page_url TEXT,                 -- "/jumpstart.html"
  confirmation_page_url TEXT,            -- "/purchase-complete.html"
  intake_form_url TEXT,                  -- "/intake/jumpstart/"
  
  -- Targeting
  targets JSONB DEFAULT '{}',            -- {audience: "men-40+", source: "organic", campaign: "..."}
  
  -- Status
  status TEXT DEFAULT 'draft',           -- 'draft', 'active', 'paused', 'archived'
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common queries
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_slug ON opportunities(slug);


-- ============================================
-- FLOWS
-- Defines what happens after purchase (sequence of steps)
-- ============================================
CREATE TABLE flows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identity
  name TEXT NOT NULL,                    -- "Consultation Onboarding"
  description TEXT,                      -- Internal notes
  
  -- Status
  status TEXT DEFAULT 'active',          -- 'active', 'archived'
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================
-- FLOW_STEPS
-- Individual steps within a flow
-- ============================================
CREATE TABLE flow_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Parent flow
  flow_id UUID NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
  
  -- Ordering
  step_order INTEGER NOT NULL,           -- 1, 2, 3... (execution order)
  
  -- Step Definition
  step_type TEXT NOT NULL,               -- 'email', 'sms', 'wait', 'task', 'check', 'branch', 'webhook'
  step_name TEXT,                        -- Human-readable name for this step
  
  -- Configuration (varies by step_type)
  config JSONB NOT NULL DEFAULT '{}',
  /*
    For 'email':
      {template_id: "uuid", to: "client" | "resource"}
    
    For 'sms':
      {template_id: "uuid", to: "client" | "resource"}
    
    For 'wait':
      {duration: "24h" | "3d" | "1w", until: "specific_time"}
    
    For 'task':
      {
        resource_role: "PHO" | "MED" | "COACH",
        task_type: "review" | "call" | "meeting",
        title: "Review intake form",
        due_in: "48h"
      }
    
    For 'check':
      {
        condition: "intake_complete" | "task_complete" | "appointment_scheduled",
        field: "column_name",
        operator: "equals" | "exists" | "gt" | "lt",
        value: "expected_value"
      }
    
    For 'branch':
      {
        condition_step_id: "uuid",  -- references the check step
        on_true: next_step_order,
        on_false: next_step_order | "end"
      }
    
    For 'webhook':
      {
        url: "https://...",
        method: "POST",
        payload: {...}
      }
  */
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Ensure unique ordering within a flow
  UNIQUE(flow_id, step_order)
);

-- Index for fetching steps in order
CREATE INDEX idx_flow_steps_flow_order ON flow_steps(flow_id, step_order);


-- ============================================
-- TEMPLATES
-- Email and SMS content templates
-- ============================================
CREATE TABLE templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identity
  name TEXT NOT NULL,                    -- "JumpStart Confirmation"
  type TEXT NOT NULL,                    -- 'email', 'sms'
  
  -- Content (for email)
  subject TEXT,                          -- Email subject line
  body_html TEXT,                        -- HTML body (for email)
  body_text TEXT,                        -- Plain text body (for SMS or email fallback)
  
  -- Variables available (documentation)
  available_variables JSONB DEFAULT '[]', -- ["client_name", "order_amount", "intake_url"]
  
  -- Status
  status TEXT DEFAULT 'active',          -- 'active', 'archived'
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for type filtering
CREATE INDEX idx_templates_type ON templates(type);


-- ============================================
-- RESOURCES
-- People who fulfill tasks (PHO, MED, COACH, etc.)
-- ============================================
CREATE TABLE resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identity
  name TEXT NOT NULL,                    -- "Dr. Smith"
  role TEXT NOT NULL,                    -- 'PHO', 'MED', 'COACH', 'ADMIN'
  
  -- Contact
  email TEXT NOT NULL,
  phone TEXT,
  
  -- Scheduling
  calendar_url TEXT,                     -- Google Calendar booking link
  availability JSONB DEFAULT '{}',       -- {mon: ["9:00-17:00"], tue: [...]}
  
  -- Status
  status TEXT DEFAULT 'active',          -- 'active', 'inactive'
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for role filtering
CREATE INDEX idx_resources_role ON resources(role);
```

### Operational Tables

```sql
-- ============================================
-- CLIENTS
-- Customer records
-- ============================================
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identity
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  phone TEXT,
  
  -- Profile (populated from intake)
  profile JSONB DEFAULT '{}',            -- {age: 45, goals: [...], conditions: [...]}
  
  -- Status
  status TEXT DEFAULT 'lead',            -- 'lead', 'prospect', 'active', 'inactive', 'churned'
  
  -- Source tracking
  source JSONB DEFAULT '{}',             -- {opportunity_slug: "jumpstart", utm_source: "..."}
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for email lookup
CREATE INDEX idx_clients_email ON clients(email);


-- ============================================
-- ORDERS
-- Purchase records
-- ============================================
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- References
  client_id UUID NOT NULL REFERENCES clients(id),
  opportunity_id UUID NOT NULL REFERENCES opportunities(id),
  
  -- Payment details
  square_payment_id TEXT,                -- Square payment ID
  square_order_id TEXT,                  -- Square order ID
  amount_cents INTEGER NOT NULL,
  currency TEXT DEFAULT 'USD',
  payment_status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
  
  -- Fulfillment tracking
  fulfillment_status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
  workflow_execution_id TEXT,            -- n8n execution ID
  
  -- Timestamps
  paid_at TIMESTAMPTZ,
  fulfilled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_orders_client ON orders(client_id);
CREATE INDEX idx_orders_opportunity ON orders(opportunity_id);
CREATE INDEX idx_orders_status ON orders(fulfillment_status);


-- ============================================
-- TASKS
-- Work items assigned to resources
-- ============================================
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- References
  order_id UUID REFERENCES orders(id),
  client_id UUID NOT NULL REFERENCES clients(id),
  resource_id UUID REFERENCES resources(id),
  flow_step_id UUID REFERENCES flow_steps(id),
  
  -- Task details
  task_type TEXT NOT NULL,               -- 'review', 'call', 'meeting', 'follow_up'
  title TEXT NOT NULL,
  description TEXT,
  
  -- Status
  status TEXT DEFAULT 'pending',         -- 'pending', 'in_progress', 'completed', 'cancelled'
  priority TEXT DEFAULT 'normal',        -- 'low', 'normal', 'high', 'urgent'
  
  -- Timing
  due_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
  -- Notes
  notes TEXT,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tasks_resource ON tasks(resource_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due_at);


-- ============================================
-- INTAKE_RESPONSES
-- Form submissions from clients
-- ============================================
CREATE TABLE intake_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- References
  client_id UUID REFERENCES clients(id),
  order_id UUID REFERENCES orders(id),
  opportunity_slug TEXT,                 -- Which intake form
  
  -- Response data
  responses JSONB NOT NULL DEFAULT '{}', -- All form field responses
  
  -- Status
  status TEXT DEFAULT 'submitted',       -- 'partial', 'submitted', 'reviewed'
  
  -- Timestamps
  submitted_at TIMESTAMPTZ DEFAULT NOW(),
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for client lookup
CREATE INDEX idx_intake_client ON intake_responses(client_id);


-- ============================================
-- WORKFLOW_LOGS
-- Execution history (written by n8n)
-- ============================================
CREATE TABLE workflow_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- References
  order_id UUID REFERENCES orders(id),
  client_id UUID REFERENCES clients(id),
  flow_id UUID REFERENCES flows(id),
  flow_step_id UUID REFERENCES flow_steps(id),
  
  -- n8n reference
  n8n_execution_id TEXT,
  n8n_workflow_id TEXT,
  
  -- Execution details
  step_type TEXT,
  step_name TEXT,
  status TEXT NOT NULL,                  -- 'started', 'completed', 'failed', 'skipped'
  
  -- Error handling
  error_message TEXT,
  error_details JSONB,
  
  -- Timing
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  
  -- Debug info
  input_data JSONB,                      -- What was passed to this step
  output_data JSONB                      -- What this step produced
);

-- Indexes for common queries
CREATE INDEX idx_workflow_logs_order ON workflow_logs(order_id);
CREATE INDEX idx_workflow_logs_client ON workflow_logs(client_id);
CREATE INDEX idx_workflow_logs_status ON workflow_logs(status);
CREATE INDEX idx_workflow_logs_time ON workflow_logs(started_at);
```

### Row Level Security (RLS) Policies

```sql
-- Enable RLS on all tables
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE flow_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_logs ENABLE ROW LEVEL SECURITY;

-- For now, allow service role full access (n8n uses service role)
-- Admin app will also use service role
-- Add more granular policies as needed for client-facing features

-- Example: Clients can only see their own data
CREATE POLICY "Clients see own data" ON clients
  FOR SELECT
  USING (auth.uid()::text = id::text OR auth.role() = 'service_role');

CREATE POLICY "Clients see own orders" ON orders
  FOR SELECT
  USING (
    client_id IN (SELECT id FROM clients WHERE auth.uid()::text = id::text)
    OR auth.role() = 'service_role'
  );

-- Service role can do everything
CREATE POLICY "Service role full access" ON opportunities
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON flows
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON flow_steps
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON templates
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON resources
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON clients
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON orders
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON tasks
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON intake_responses
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON workflow_logs
  FOR ALL USING (auth.role() = 'service_role');
```

---

## n8n Workflow Architecture

### Principle: Generic Workflows, Not Per-Offer

n8n should have a SMALL number of generic workflows that read their configuration from Supabase. This means:

- Adding a new offer = Add row to `opportunities` table + assign a `flow_id`
- Modifying a flow = Update `flow_steps` table
- Changing email content = Update `templates` table

**n8n does NOT need to be modified when business logic changes.**

### Workflow 1: Fulfillment Executor (Core Workflow)

**Trigger:** Webhook (receives order_id and client_id)

**Logic:**
```
1. INPUT: {order_id, client_id}

2. FETCH ORDER DETAILS
   Query: SELECT o.*, op.flow_id, op.name as opportunity_name
          FROM orders o
          JOIN opportunities op ON o.opportunity_id = op.id
          WHERE o.id = $order_id

3. FETCH FLOW STEPS
   Query: SELECT * FROM flow_steps
          WHERE flow_id = $flow_id
          ORDER BY step_order ASC

4. INITIALIZE EXECUTION
   Insert: workflow_logs (order_id, client_id, flow_id, status='started')

5. LOOP THROUGH STEPS
   For each step in flow_steps:
   
   a. LOG STEP START
      Insert: workflow_logs (step started)
   
   b. EXECUTE BASED ON step_type:
   
      IF 'email':
        - Fetch template by config.template_id
        - Replace variables (client_name, etc.)
        - Send via SES
        - Log completion
      
      IF 'sms':
        - Fetch template by config.template_id
        - Replace variables
        - Send via Twilio
        - Log completion
      
      IF 'wait':
        - Calculate wait_until based on config.duration
        - Use n8n Wait node
        - Continue after wait
      
      IF 'task':
        - Fetch resource by config.resource_role
        - Insert task record
        - (Optional) Notify resource
        - Log completion
      
      IF 'check':
        - Query Supabase based on config.condition
        - Store result for branch step
        - Log result
      
      IF 'branch':
        - Read result from previous check
        - Jump to config.on_true or config.on_false step
        - (Modify loop index accordingly)
   
   c. LOG STEP COMPLETE
      Update: workflow_logs (step completed)

6. FINALIZE
   Update: orders.fulfillment_status = 'completed'
   Update: workflow_logs (flow completed)
```

### Workflow 2: Payment Webhook Receiver

**Trigger:** Webhook (Square payment.completed)

**Logic:**
```
1. PARSE SQUARE WEBHOOK
   Extract: payment_id, order_id, amount, customer_email

2. FIND OR CREATE CLIENT
   Query: SELECT * FROM clients WHERE email = $customer_email
   If not found: INSERT INTO clients (email, status='lead')

3. IDENTIFY OPPORTUNITY
   Match Square catalog_id to opportunities.square_catalog_id
   Query: SELECT * FROM opportunities WHERE square_catalog_id = $catalog_id

4. CREATE ORDER RECORD
   Insert: orders (client_id, opportunity_id, amount, payment_status='completed')

5. TRIGGER FULFILLMENT
   Call Workflow 1 with {order_id, client_id}
```

### Workflow 3: Scheduled Daily Jobs

**Trigger:** Cron (daily at 8:00 AM ET)

**Logic:**
```
1. APPOINTMENT REMINDERS
   Query: SELECT * FROM tasks 
          WHERE task_type = 'meeting' 
          AND status = 'pending'
          AND due_at BETWEEN NOW() AND NOW() + INTERVAL '48 hours'
   
   For each: Send reminder email/SMS

2. STALE TASK ESCALATION
   Query: SELECT * FROM tasks
          WHERE status = 'pending'
          AND due_at < NOW()
   
   For each: Update priority, notify admin

3. INTAKE FOLLOW-UPS
   Query: SELECT o.* FROM orders o
          LEFT JOIN intake_responses i ON o.id = i.order_id
          WHERE o.fulfillment_status = 'in_progress'
          AND i.id IS NULL
          AND o.paid_at < NOW() - INTERVAL '24 hours'
   
   For each: Send intake reminder
```

### Workflow 4: Manual Admin Trigger

**Trigger:** Webhook (from Admin UI)

**Logic:**
```
1. INPUT: {action, order_id, client_id, ...}

2. SWITCH on action:
   
   'retry_flow':
     - Reset order.fulfillment_status
     - Call Workflow 1
   
   'send_reminder':
     - Fetch client
     - Send specified template
   
   'create_task':
     - Insert task with provided details
     - Notify resource
```

---

## Admin Application (Opportunity Manager)

### Pages & Features

```
ADMIN APP STRUCTURE
─────────────────────────────────────────────────────────────

/dashboard
├── Overview stats (orders today, pending tasks, active flows)
├── Recent activity feed (from workflow_logs)
└── Quick actions (manual triggers)

/opportunities
├── List view (all offers with status)
├── Create new opportunity
├── Edit opportunity
│   ├── Basic info (name, slug, description)
│   ├── Pricing (amount, currency)
│   ├── Square integration (catalog ID, payment link)
│   ├── URLs (landing, confirmation, intake)
│   ├── Flow assignment (dropdown of flows)
│   ├── Targeting (audience, source)
│   └── Status toggle
└── Archive opportunity

/flows
├── List view (all flows)
├── Create new flow
├── Edit flow
│   ├── Basic info (name, description)
│   └── Step builder (visual or table)
│       ├── Add step
│       ├── Reorder steps (drag or number)
│       ├── Configure step (type-specific form)
│       └── Delete step
└── Archive flow

/templates
├── List view (all templates, filter by type)
├── Create new template
├── Edit template
│   ├── Type (email/sms)
│   ├── Name
│   ├── Subject (email only)
│   ├── Body (with variable hints)
│   └── Preview with sample data
└── Archive template

/resources
├── List view (team members)
├── Add resource
├── Edit resource
│   ├── Name, role, email, phone
│   ├── Calendar URL
│   └── Availability
└── Deactivate resource

/clients
├── List view (searchable, filterable)
├── Client detail view
│   ├── Profile info
│   ├── Order history
│   ├── Intake responses
│   ├── Task history
│   └── Workflow logs (timeline view)
└── Manual actions (send email, create task)

/orders
├── List view (recent orders, filterable by status)
├── Order detail view
│   ├── Payment details
│   ├── Fulfillment status
│   ├── Workflow execution timeline
│   └── Manual actions (retry, refund)
└── Export (CSV)

/tasks
├── Queue view (grouped by resource)
├── Task detail view
├── Complete task
├── Reassign task
└── Filter by status, resource, type

/logs
├── Workflow execution history
├── Filter by order, client, flow, status
├── Execution detail view
│   ├── Step-by-step timeline
│   ├── Input/output data
│   └── Error details (if failed)
└── Retry failed executions
```

### Tech Stack for Admin

```
ADMIN TECH STACK
─────────────────────────────────────────────────────────────

Frontend: Vanilla HTML/CSS/JS
├── No framework (per architectural decision)
├── Tailwind CSS (via CDN) for styling
├── htmx (optional) for dynamic updates without JS frameworks
└── Chart.js for dashboard stats

Backend: Supabase
├── Direct client connection (supabase-js)
├── Service role key for admin operations
├── RLS policies allow service role full access
└── Real-time subscriptions for live updates (optional)

Hosting: S3 + CloudFront (existing setup)
├── admin.manvshealth.com
└── Protected via Supabase Auth (admin users only)
```

---

## Integration Points

### Square → n8n

```
SQUARE WEBHOOK SETUP
─────────────────────────────────────────────────────────────

1. In Square Developer Dashboard:
   - Create webhook subscription
   - Event: payment.completed
   - URL: https://n8n.manvshealth.com/webhook/square-payment

2. n8n receives:
   {
     "type": "payment.completed",
     "data": {
       "object": {
         "payment": {
           "id": "...",
           "order_id": "...",
           "amount_money": {"amount": 9700, "currency": "USD"},
           "customer_id": "...",
           ...
         }
       }
     }
   }

3. n8n processes and triggers fulfillment
```

### Supabase → n8n (Database Triggers)

```
OPTIONAL: SUPABASE WEBHOOKS
─────────────────────────────────────────────────────────────

If you want Supabase inserts to trigger n8n directly:

1. Create Edge Function as webhook proxy:

   // supabase/functions/webhook-proxy/index.ts
   Deno.serve(async (req) => {
     const { table, record, type } = await req.json();
     
     // Forward to n8n
     await fetch('https://n8n.manvshealth.com/webhook/supabase-trigger', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ table, record, type })
     });
     
     return new Response('OK');
   });

2. Create Supabase trigger:
   
   CREATE OR REPLACE FUNCTION notify_n8n()
   RETURNS TRIGGER AS $$
   BEGIN
     PERFORM net.http_post(
       url := 'https://n8n.manvshealth.com/webhook/supabase-trigger',
       body := json_build_object(
         'table', TG_TABLE_NAME,
         'type', TG_OP,
         'record', row_to_json(NEW)
       )::text
     );
     RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER intake_notify
   AFTER INSERT ON intake_responses
   FOR EACH ROW EXECUTE FUNCTION notify_n8n();

ALTERNATIVE: n8n polls Supabase on schedule (simpler, less real-time)
```

### Admin → n8n (Manual Triggers)

```
MANUAL TRIGGER FROM ADMIN UI
─────────────────────────────────────────────────────────────

// In Admin app (vanilla JS)
async function retryFlow(orderId) {
  const response = await fetch('https://n8n.manvshealth.com/webhook/admin-trigger', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Secret': 'your-secret-key'  // Simple auth
    },
    body: JSON.stringify({
      action: 'retry_flow',
      order_id: orderId
    })
  });
  
  if (response.ok) {
    alert('Flow restarted successfully');
  }
}
```

---

## Variable Replacement in Templates

### Available Variables

```
TEMPLATE VARIABLES
─────────────────────────────────────────────────────────────

Client variables:
{{client_name}}          - Client's full name
{{client_email}}         - Client's email
{{client_phone}}         - Client's phone

Order variables:
{{order_id}}             - Order UUID
{{order_amount}}         - Formatted amount ($97.00)
{{order_date}}           - Formatted date
{{opportunity_name}}     - Name of the offer purchased

URLs:
{{intake_url}}           - Full URL to intake form
{{calendar_url}}         - Scheduling link
{{dashboard_url}}        - Client dashboard link

Custom (from intake):
{{intake.field_name}}    - Any field from intake_responses.responses
```

### Replacement Logic (in n8n)

```javascript
// n8n Code node for variable replacement
const template = $input.first().json.template_body;
const client = $input.first().json.client;
const order = $input.first().json.order;
const intake = $input.first().json.intake || {};

let output = template
  .replace(/\{\{client_name\}\}/g, client.name || 'there')
  .replace(/\{\{client_email\}\}/g, client.email)
  .replace(/\{\{order_amount\}\}/g, formatCurrency(order.amount_cents))
  .replace(/\{\{intake_url\}\}/g, order.intake_form_url)
  // ... etc

// Handle intake.* variables
output = output.replace(/\{\{intake\.(\w+)\}\}/g, (match, field) => {
  return intake.responses?.[field] || '';
});

return { body: output };
```

---

## JumpStart Migration Checklist

### Phase 1: Database Setup
- [ ] Create all tables in Supabase
- [ ] Apply RLS policies
- [ ] Insert JumpStart opportunity record
- [ ] Create JumpStart flow record
- [ ] Create flow_steps for JumpStart
- [ ] Create email templates (confirmation, intake reminder, calendar)

### Phase 2: n8n Setup
- [ ] Provision AWS Lightsail instance
- [ ] Install Docker + Docker Compose
- [ ] Deploy n8n with SSL (Caddy)
- [ ] Configure DNS (n8n.manvshealth.com)
- [ ] Set up credentials (Supabase, SES, Square)

### Phase 3: n8n Workflows
- [ ] Create Payment Webhook Receiver workflow
- [ ] Create Fulfillment Executor workflow
- [ ] Create Scheduled Jobs workflow
- [ ] Test with sample data

### Phase 4: Square Integration
- [ ] Create webhook subscription in Square
- [ ] Point to n8n webhook URL
- [ ] Test payment flow end-to-end

### Phase 5: Admin UI (Minimal)
- [ ] Create /logs page to view workflow_logs
- [ ] Create manual retry button
- [ ] (Full Opportunity Manager can come later)

### Phase 6: Cutover
- [ ] Remove old Edge Functions handling payments
- [ ] Update any hardcoded references
- [ ] Monitor first real transactions

---

## Security Considerations

### n8n Access
- Basic auth enabled (N8N_BASIC_AUTH_ACTIVE=true)
- Strong password required
- Consider IP whitelist if needed

### Webhook Security
- Square webhooks: Verify signature (Square provides HMAC)
- Admin webhooks: X-Admin-Secret header check
- Supabase webhooks: Shared secret validation

### Supabase
- Service role key only in n8n (server-side)
- Anon key for client-side (with RLS)
- Admin users have separate auth

### Secrets Management
- n8n: Store in .env file on server
- Supabase: Use Vault for sensitive config
- Never commit secrets to git

---

## Monitoring & Debugging

### n8n Built-in
- Execution history (success/fail)
- Step-by-step data inspection
- Manual retry from any step

### Supabase workflow_logs
- Query for failed executions
- View input/output data
- Timeline of client journey

### Alerts (Future)
- n8n can send Slack/email on failure
- Set up error workflow that catches failures
- Daily summary of execution stats

---

## Future Enhancements

### Phase 2 Features
- Visual flow builder in Admin (drag-drop)
- Template editor with WYSIWYG
- A/B testing for flows
- Analytics dashboard

### Phase 3 Features
- AI-powered flow optimization
- Predictive lead scoring
- Automated flow suggestions
- Client health dashboard

---

## Questions for Implementation

1. **Lightsail instance size?** 
   - Recommended: 1GB RAM ($5/mo) to start, upgrade if needed

2. **Square sandbox vs production?**
   - Start with sandbox for testing, switch to production when ready

3. **Email sending limits?**
   - SES has sending limits; verify domain and request increase if needed

4. **Backup strategy?**
   - n8n data: Docker volume backup
   - Supabase: Built-in backups (Pro plan)

5. **Existing JumpStart data?**
   - Any existing orders/clients to migrate?
