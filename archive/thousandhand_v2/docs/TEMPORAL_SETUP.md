# Temporal Cloud Setup Guide

This guide walks through setting up Temporal Cloud for ThousandHand's autonomous operation.

## Prerequisites

- Python 3.9+
- Temporal Cloud account (https://cloud.temporal.io)
- Your namespace and API key from Temporal Cloud

## Step 1: Install Temporal SDK

```bash
# In your 1KH project directory
pip install temporalio
```

## Step 2: Install Temporal CLI (optional, for debugging)

```bash
# macOS
brew install temporal

# Or download from https://github.com/temporalio/cli/releases
```

## Step 3: Configure Temporal Profile

Get your credentials from Temporal Cloud dashboard, then:

```bash
# Set up a "cloud" profile with your credentials
temporal --profile cloud config set --prop address --value "<your-namespace>.tmprl.cloud:7233"
temporal --profile cloud config set --prop namespace --value "<your-namespace>"
temporal --profile cloud config set --prop api_key --value "<your-api-key>"
```

Example with real values:
```bash
temporal --profile cloud config set --prop address --value "us-east-1.aws.api.temporal.io:7233"
temporal --profile cloud config set --prop namespace --value "quickstart-paulmanv-b31d640b.dx2to"
temporal --profile cloud config set --prop api_key --value "eyJhbGc..."
```

## Step 4: Update 1KH Config

Add your Temporal credentials to your project's `.1kh/.env`:

```bash
TEMPORAL_CLOUD_API_KEY=eyJhbGc...
TEMPORAL_NAMESPACE=quickstart-paulmanv-b31d640b.dx2to
TEMPORAL_ADDRESS=us-east-1.aws.api.temporal.io:7233
```

## Step 5: Run the Local Worker

The local worker runs on your machine and executes activities that require:
- Claude Code (building workflows)
- Local file system access
- Claude API calls

```bash
# From your 1KH project directory
TEMPORAL_PROFILE=cloud python -m temporal.workers.local_worker
```

Or using environment variables directly:
```bash
TEMPORAL_ADDRESS="your-namespace.tmprl.cloud:7233" \
TEMPORAL_NAMESPACE="your-namespace" \
TEMPORAL_API_KEY="your-key" \
python -m temporal.workers.local_worker
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Temporal Cloud                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ IMAGINATION  │ │    INTENT    │ │     WORK     │  Workflows │
│  │    Loop      │ │    Loop      │ │     Loop     │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         │                │                │                     │
│         └────────────────┴────────────────┘                     │
│                          │                                      │
│                   Activity Queue                                │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Your Local Machine                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Local Worker                              ││
│  │  ┌─────────────────┐  ┌─────────────────┐                   ││
│  │  │  Claude API     │  │  Claude Code    │  Activities       ││
│  │  │  (reasoning)    │  │  (execution)    │                   ││
│  │  └─────────────────┘  └─────────────────┘                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  .1kh/                                                       ││
│  │  ├── .env (API keys)                                        ││
│  │  ├── state/                                                 ││
│  │  └── logs/                                                  ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## What Each Loop Does

### IMAGINATION Loop
- Generates hypothesis candidates
- Estimates capability confidence
- Calculates viability scores
- Recommends paths or escalates to human

### INTENT Loop
- Observes tree state
- Makes strategic decisions
- Detects fruit (outcomes)
- Decides to prune or grow branches

### WORK Loop
- Decomposes decisions into tasks
- Manages task queue
- Tracks progress
- Handles retries

### EXECUTION (via Activities)
- Builds workflows using Claude Code
- Deploys workflows to Temporal
- Runs exploration tasks
- Collects metrics

## Testing Your Setup

1. **Verify CLI connection:**
   ```bash
   temporal --profile cloud workflow list --namespace your-namespace
   ```

2. **Run a test workflow:**
   ```bash
   # Coming soon: 1kh test-temporal
   ```

## Troubleshooting

### "Connection refused"
- Check your TEMPORAL_ADDRESS includes the port (`:7233`)
- Verify your API key hasn't expired
- Check firewall/VPN settings

### "Namespace not found"
- Verify TEMPORAL_NAMESPACE matches exactly (case-sensitive)
- Check you're connecting to the right region

### Worker not picking up activities
- Ensure worker is running with correct task queue
- Check worker logs for connection errors
- Verify activities are registered correctly

## Cost Considerations

Temporal Cloud pricing is based on:
- Actions (workflow/activity starts, signals, etc.)
- Storage (workflow history retention)

For a small 1KH deployment, expect:
- ~$20-50/month during active development
- Scales with number of active branches/workflows

See: https://temporal.io/pricing
