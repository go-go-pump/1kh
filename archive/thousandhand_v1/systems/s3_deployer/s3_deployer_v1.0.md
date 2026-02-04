# SYSTEM: S3Deployer
## Version 1.0

---

## PURPOSE

Deploy static files to S3 bucket with proper caching, invalidation, and verification.

---

## INTERFACE

### Input Schema

```json
{
  "source_dir": "string - Local directory to deploy",
  "bucket": "string - S3 bucket name",
  "region": "string - AWS region",
  "cloudfront_distribution_id": "string (optional) - For cache invalidation",
  "deploy_mode": "sync | full",
  "dry_run": "boolean - Preview without deploying"
}
```

### Output Schema

```json
{
  "success": "boolean",
  "files_uploaded": "number",
  "files_deleted": "number",
  "files_unchanged": "number",
  "total_size": "string - e.g., 2.4 MB",
  "cloudfront_invalidation_id": "string (if applicable)",
  "deploy_url": "string - Live URL",
  "errors": ["string"]
}
```

---

## PROCESS

### Step 1: Validate Configuration
- Verify AWS credentials available
- Verify bucket exists and is accessible
- Check source directory exists

### Step 2: Calculate Diff (sync mode)
- List current S3 objects
- Compare with local files (by hash, not just name)
- Identify: new, modified, deleted, unchanged

### Step 3: Set Content Types and Caching
```
.html     → text/html, max-age=3600 (1 hour)
.css      → text/css, max-age=31536000 (1 year, hashed filenames)
.js       → application/javascript, max-age=31536000
.jpg/.png → image/*, max-age=31536000
.json     → application/json, max-age=3600
.xml      → application/xml, max-age=3600
```

### Step 4: Upload Files
- Upload new and modified files
- Set appropriate Content-Type
- Set Cache-Control headers
- Delete removed files (if sync mode)

### Step 5: Invalidate CloudFront (if configured)
- Create invalidation for changed paths
- Or invalidate /* for full refresh
- Wait for invalidation to complete (optional)

### Step 6: Verify Deployment
- Spot check key URLs return 200
- Verify content matches local

### Step 7: Log Results
- Record all actions taken
- Report success/failure
- Include rollback info if needed

---

## AWS CLI EQUIVALENT

For reference, the core operation is:
```bash
aws s3 sync ./public s3://bucket-name \
  --delete \
  --cache-control "max-age=3600" \
  --exclude "*.map"
```

With CloudFront invalidation:
```bash
aws cloudfront create-invalidation \
  --distribution-id XXXXX \
  --paths "/*"
```

---

## CONSTRAINTS

- Never delete files in dry_run mode
- Always verify credentials before starting
- Log all actions for audit
- Support rollback (keep manifest of previous state)

---

## DEPENDENCIES

- AWS credentials (via environment or IAM role)
- boto3 Python library
- Source files already built

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-17 | Initial specification |
