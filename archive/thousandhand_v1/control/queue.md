# TASK QUEUE
## Ready for Execution

---

Tasks here are unblocked and ready to run. Orchestrator picks from top.

---

## PRIORITY 1 (Execute Now)

## PRIORITY 2 (After Priority 1 Complete)

## QUEUED (Not Yet Prioritized)

- Blog articles #6-10 (Priority 2 topics from goal)
- Validation tasks (created after generation)

---

*Queue managed by orchestrator. Paul can reorder by editing this file.*
### BLOCK-001: Site Configuration
**Priority:** HIGH
**Blocking:** All publishing tasks

**What's needed:**
Copy `config.example.json` to `config.json` and fill in:
- S3 bucket name (where your site is hosted)
- CloudFront distribution ID (if using CloudFront)
- Confirm base URL

**Quick action:**
```bash
cp config.example.json config.json
# Edit config.json with your values
```

---

### BLOCK-002: AWS Credentials
**Priority:** HIGH  
**Blocking:** S3 deployment

**What's needed:**
Set AWS credentials in your environment:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

Or configure AWS CLI: `aws configure`

---

### BLOCK-003: Image Strategy Decision
**Priority:** MEDIUM
**Blocking:** Blog publishing (can use placeholder for now)

**Options:**
1. **placeholder** - Use branded placeholder images (fastest, free)
2. **ai_generate** - Generate images via DALL-E (costs ~$0.02/image)
3. **stock_library** - Use curated stock photos (requires library setup)

**Quick action:** Set `image_strategy` in config.json. Default is "placeholder".