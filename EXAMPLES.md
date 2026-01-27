# EnvGuard - Usage Examples

> 10+ real-world examples with expected output

---

## Quick Navigation

- [Example 1: Basic Project Scan](#example-1-basic-project-scan)
- [Example 2: Audit Environment Variables](#example-2-audit-environment-variables)
- [Example 3: Detect Configuration Conflicts](#example-3-detect-configuration-conflicts)
- [Example 4: URL Reachability Validation](#example-4-url-reachability-validation)
- [Example 5: Schema Validation](#example-5-schema-validation)
- [Example 6: Stale Value Detection](#example-6-stale-value-detection)
- [Example 7: Update Environment Values](#example-7-update-environment-values)
- [Example 8: Compare Environment Files](#example-8-compare-environment-files)
- [Example 9: CI/CD Pipeline Integration](#example-9-cicd-pipeline-integration)
- [Example 10: Python API Integration](#example-10-python-api-integration)
- [Example 11: Mobile App Pre-Build Check](#example-11-mobile-app-pre-build-check)
- [Example 12: Multi-Environment Audit](#example-12-multi-environment-audit)

---

## Example 1: Basic Project Scan

**Scenario:** You want to find all .env files in your project.

**Command:**

```bash
python envguard.py scan ./my-project
```

**Expected Output:**

```
[OK] Found 4 .env file(s) in ./my-project:

  [OK] ./my-project/.env
      Variables: 15
  [OK] ./my-project/.env.local
      Variables: 3
  [OK] ./my-project/.env.production
      Variables: 15
  [OK] ./my-project/.env.example
      Variables: 15
```

**What You Learned:**
- EnvGuard recursively searches for all .env variants
- Shows variable count for each file
- Identifies potential configuration files for validation

---

## Example 2: Audit Environment Variables

**Scenario:** You want to see all variables in your .env file with sensitive values masked.

**Setup:** Create a test `.env` file:

```bash
# .env
API_KEY=sk_live_abc123def456ghi789
DATABASE_URL=postgres://user:password@localhost:5432/mydb
API_URL=http://api.example.com
DEBUG=true
PORT=3000
```

**Command:**

```bash
python envguard.py audit .env
```

**Expected Output:**

```
[OK] Audit: .env
    Variables: 5

======================================================================
KEY            | VALUE                              | FLAGS
---------------+------------------------------------+-----------------
API_KEY        | sk**************************89    | [SENSITIVE]
API_URL        | http://api.example.com             | [URL]
DATABASE_URL   | po**************************db    | [SENSITIVE, URL]
DEBUG          | true                               |
PORT           | 3000                               |
======================================================================
```

**Show Secrets (Use Carefully!):**

```bash
python envguard.py audit .env --show-secrets
```

**What You Learned:**
- Sensitive values (API keys, passwords) are automatically masked
- URL-like keys are flagged for validation
- Use `--show-secrets` only when necessary and in secure environments

---

## Example 3: Detect Configuration Conflicts

**Scenario:** Your mobile app uses wrong server URL despite code changes. You suspect .env is overriding.

**Setup:** 

`.env`:
```
API_URL=http://192.168.4.66:3000
```

`config.ts`:
```typescript
export const config = {
  API_URL: "http://production.server.com",
  timeout: 5000
};
```

**Command:**

```bash
python envguard.py conflicts ./my-project
```

**Expected Output:**

```
[...] Scanning for conflicts in ./my-project...

[!] Found 1 conflict(s):

[!] Conflict #1: value_conflict
    Key: API_URL
    .env file: ./my-project/.env
    Config file: ./my-project/config.ts
    .env value: http://192.168.4.66:3000
    Config value: http://production.server.com
    Message: .env will OVERRIDE config file value
```

**What You Learned:**
- EnvGuard detected that .env will override your config.ts value
- This explains why code changes weren't taking effect
- Fix by updating .env or removing the conflicting entry

---

## Example 4: URL Reachability Validation

**Scenario:** Before deployment, you want to verify all URL endpoints are reachable.

**Setup:** `.env`:
```
API_URL=https://api.example.com
DATABASE_HOST=db.internal.company.com
REDIS_URL=redis://localhost:6379
EXTERNAL_API=https://httpstat.us/200
```

**Command:**

```bash
python envguard.py validate .env --timeout 5
```

**Expected Output:**

```
[...] Validating URLs in .env...

[OK] API_URL: https://api.example.com
     Status: 200 | Response time: 145ms

[X] DATABASE_HOST: http://db.internal.company.com
     Error: Name or service not known

[X] REDIS_URL: http://redis://localhost:6379
     Error: Connection refused

[OK] EXTERNAL_API: https://httpstat.us/200
     Status: 200 | Response time: 523ms
```

**What You Learned:**
- Internal hostnames may not resolve outside VPN
- Local services (Redis) need to be running
- External APIs are reachable
- Fix database connection string or connect to VPN

---

## Example 5: Schema Validation

**Scenario:** Validate that your .env has all required variables from .env.example.

**Setup:**

`.env.example` (template):
```
API_KEY=your_api_key_here
API_URL=https://api.example.com
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379
DEBUG=false
```

`.env` (actual):
```
API_KEY=sk_live_abc123
API_URL=https://api.production.com
DEBUG=true
CUSTOM_SETTING=myvalue
```

**Command:**

```bash
python envguard.py check .env --schema .env.example
```

**Expected Output:**

```
[...] Checking .env against .env.example...

[X] Schema validation FAILED

    Coverage: 60.0%
    Matched keys: 3

    [!] Missing keys (2):
        - DATABASE_URL
        - REDIS_URL

    [?] Extra keys (1):
        + CUSTOM_SETTING
```

**What You Learned:**
- Your .env is missing `DATABASE_URL` and `REDIS_URL`
- You have an extra `CUSTOM_SETTING` not in the template
- 60% schema coverage - needs attention before deployment

---

## Example 6: Stale Value Detection

**Scenario:** Check if your production .env has any stale or suspicious values.

**Setup:** `.env.production`:
```
API_URL=http://localhost:3000
DATABASE_HOST=192.168.4.66
REDIS_URL=redis://localhost:6379
API_KEY=YOUR_API_KEY_HERE
SECRET_KEY=
DEBUG=true
```

**Command:**

```bash
python envguard.py stale .env.production --context production
```

**Expected Output:**

```
[...] Checking for stale values in .env.production (context: production)...

[!] HIGH severity warnings (4):

    [!] API_URL = http://localhost:3000
        Localhost detected - likely stale for non-development environments

    [!] DATABASE_HOST = 192.168.4.66
        Private IP detected - may not work outside local network

    [!] REDIS_URL = redis://localhost:6379
        Localhost detected - likely stale for non-development environments

    [!] API_KEY = YOUR_API_KEY_HERE
        Placeholder value detected - needs to be replaced

[?] Warnings (1):

    [?] SECRET_KEY =
        Empty value detected - may cause runtime errors
```

**What You Learned:**
- 4 HIGH severity issues that could break production
- Localhost URLs won't work in production
- Private IPs may not be accessible
- Placeholder values need real credentials
- Empty values will cause runtime errors

---

## Example 7: Update Environment Values

**Scenario:** Fix a value directly from the command line.

**Before:** `.env`:
```
API_URL=http://localhost:3000
DEBUG=true
```

**Command:**

```bash
# Update existing value
python envguard.py fix .env --key API_URL --value "https://api.production.com"

# Add new key
python envguard.py fix .env --key NEW_FEATURE_FLAG --value "enabled" --create
```

**Expected Output:**

```
[OK] Updated API_URL in .env
[OK] Updated NEW_FEATURE_FLAG in .env
```

**After:** `.env`:
```
API_URL=https://api.production.com
DEBUG=true
NEW_FEATURE_FLAG=enabled
```

**What You Learned:**
- Quickly update values without opening the file
- Use `--create` to add new keys
- Great for CI/CD automation

---

## Example 8: Compare Environment Files

**Scenario:** See differences between development and production configs.

**Setup:**

`.env`:
```
API_URL=http://localhost:3000
DEBUG=true
LOG_LEVEL=debug
DATABASE_URL=postgres://localhost/dev
```

`.env.production`:
```
API_URL=https://api.production.com
DEBUG=false
LOG_LEVEL=error
DATABASE_URL=postgres://prod-server/prod
SENTRY_DSN=https://key@sentry.io/123
```

**Command:**

```bash
python envguard.py diff .env .env.production
```

**Expected Output:**

```
[...] Comparing .env vs .env.production...

[OK] Comparison complete

    File 1: .env (4 keys)
    File 2: .env.production (5 keys)
    Similarity: 0.0%

    Only in File 2 (1):
        + SENTRY_DSN

    Different values (4):
        API_URL:
            File 1: http://localhost:3000
            File 2: https://api.production.com
        DATABASE_URL:
            File 1: postgres://localhost/dev
            File 2: postgres://prod-server/prod
        DEBUG:
            File 1: true
            File 2: false
        LOG_LEVEL:
            File 1: debug
            File 2: error
```

**What You Learned:**
- All 4 common keys have different values (expected for dev vs prod)
- Production has `SENTRY_DSN` that dev doesn't have
- This is a healthy environment separation

---

## Example 9: CI/CD Pipeline Integration

**Scenario:** Add EnvGuard checks to your CI/CD pipeline.

**GitHub Actions Workflow:**

```yaml
# .github/workflows/validate-env.yml
name: Validate Environment

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install EnvGuard
        run: |
          git clone https://github.com/DonkRonk17/EnvGuard.git
          cd EnvGuard
      
      - name: Validate Schema
        run: |
          python EnvGuard/envguard.py check .env.production --schema .env.example
      
      - name: Check for Stale Values
        run: |
          python EnvGuard/envguard.py stale .env.production --context production
      
      - name: Detect Conflicts
        run: |
          python EnvGuard/envguard.py conflicts .
```

**Expected Output (in CI logs):**

```
=== Validate Schema ===
[OK] Schema validation PASSED
    Coverage: 100.0%
    Matched keys: 12

=== Check for Stale Values ===
[OK] No stale or suspicious values detected!

=== Detect Conflicts ===
[OK] No conflicts detected!
```

**What You Learned:**
- EnvGuard returns non-zero exit code on failures
- CI/CD can fail builds on env issues
- Catch problems before deployment

---

## Example 10: Python API Integration

**Scenario:** Use EnvGuard programmatically in your Python application.

**Code:**

```python
#!/usr/bin/env python3
"""Pre-deploy environment validation script."""

from envguard import EnvGuard, EnvFile
import sys

def validate_environment():
    """Comprehensive environment validation."""
    guard = EnvGuard()
    errors = []
    
    print("=" * 60)
    print("ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    # 1. Find all .env files
    print("\n[1/5] Scanning for .env files...")
    files = guard.scan(".")
    print(f"      Found {len(files)} files")
    
    # 2. Check for conflicts
    print("\n[2/5] Checking for conflicts...")
    conflicts = guard.detect_conflicts(".")
    if conflicts:
        errors.extend([f"Conflict: {c['key']}" for c in conflicts])
        print(f"      [X] Found {len(conflicts)} conflicts")
    else:
        print("      [OK] No conflicts")
    
    # 3. Validate schema
    print("\n[3/5] Validating against schema...")
    if ".env" in [f.name for f in files]:
        schema_result = guard.check_schema(".env", ".env.example")
        if not schema_result['valid']:
            errors.extend([f"Missing: {k}" for k in schema_result['missing_keys']])
            print(f"      [X] Missing {len(schema_result['missing_keys'])} keys")
        else:
            print("      [OK] Schema valid")
    
    # 4. Check for stale values
    print("\n[4/5] Checking for stale values...")
    if ".env.production" in [f.name for f in files]:
        stale = guard.detect_stale(".env.production", context="production")
        high_severity = [w for w in stale if w['severity'] == 'HIGH']
        if high_severity:
            errors.extend([f"Stale: {w['key']}" for w in high_severity])
            print(f"      [X] Found {len(high_severity)} stale values")
        else:
            print("      [OK] No stale values")
    
    # 5. Validate URLs
    print("\n[5/5] Validating URLs...")
    if ".env.production" in [f.name for f in files]:
        url_results = guard.validate_urls(".env.production", timeout=5)
        unreachable = [r for r in url_results if not r['reachable']]
        if unreachable:
            errors.extend([f"Unreachable: {r['key']}" for r in unreachable])
            print(f"      [!] {len(unreachable)} URLs unreachable (may be internal)")
        else:
            print("      [OK] All URLs reachable")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"VALIDATION FAILED: {len(errors)} issues found")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("VALIDATION PASSED!")
        return 0

if __name__ == "__main__":
    sys.exit(validate_environment())
```

**Expected Output:**

```
============================================================
ENVIRONMENT VALIDATION
============================================================

[1/5] Scanning for .env files...
      Found 3 files

[2/5] Checking for conflicts...
      [OK] No conflicts

[3/5] Validating against schema...
      [OK] Schema valid

[4/5] Checking for stale values...
      [OK] No stale values

[5/5] Validating URLs...
      [OK] All URLs reachable

============================================================
VALIDATION PASSED!
```

**What You Learned:**
- EnvGuard provides a clean Python API
- Can be integrated into any Python workflow
- Return codes work with sys.exit for scripts

---

## Example 11: Mobile App Pre-Build Check

**Scenario:** Before building your React Native/Expo app, validate the environment.

**Script:** `pre-build-check.py`:

```python
#!/usr/bin/env python3
"""Pre-build validation for mobile app."""

import sys
from pathlib import Path
from envguard import EnvGuard

def main():
    guard = EnvGuard()
    mobile_project = Path("./bch-mobile")
    
    print("Mobile App Pre-Build Check")
    print("=" * 40)
    
    # Critical: Check for API_URL conflicts
    print("\n[!] Checking API_URL configuration...")
    conflicts = guard.detect_conflicts(str(mobile_project))
    api_conflicts = [c for c in conflicts if 'URL' in c.get('key', '')]
    
    if api_conflicts:
        print("\n[X] CRITICAL: API URL conflicts detected!")
        for c in api_conflicts:
            print(f"    .env value: {c['env_value']}")
            print(f"    config value: {c['config_value']}")
            print(f"    The .env value will be used in build!")
        return 1
    
    print("[OK] No API URL conflicts")
    
    # Check for localhost in production builds
    env_file = mobile_project / ".env"
    if env_file.exists():
        stale = guard.detect_stale(str(env_file), context="production")
        localhost = [w for w in stale if 'localhost' in w['pattern']]
        
        if localhost:
            print("\n[!] WARNING: Localhost URLs detected")
            print("    These may work in dev but fail in production builds")
            for w in localhost:
                print(f"    {w['key']} = {w['value']}")
    
    print("\n[OK] Pre-build check passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Usage:**

```bash
python pre-build-check.py && npx expo build
```

**What You Learned:**
- Run EnvGuard before every build
- Catch URL conflicts that cause wrong server connections
- Prevent localhost URLs from reaching production builds

---

## Example 12: Multi-Environment Audit

**Scenario:** Audit all environments at once for a comprehensive view.

**Command:**

```bash
# Scan and list all environments
python envguard.py scan . --verbose

# Compare each environment
python envguard.py diff .env .env.staging
python envguard.py diff .env.staging .env.production

# Check each for stale values
for env in .env .env.staging .env.production; do
    echo "=== Checking $env ==="
    python envguard.py stale "$env" --context auto
done
```

**Expected Output:**

```
=== Checking .env ===
[OK] No stale or suspicious values detected!

=== Checking .env.staging ===
[?] Warnings (1):
    [?] DEBUG = true
        Note: Debug mode enabled

=== Checking .env.production ===
[OK] No stale or suspicious values detected!
```

**What You Learned:**
- Comprehensive environment auditing
- Catch issues across all environments
- Ensure production is clean

---

## Summary

| Example | Use Case | Key Command |
|---------|----------|-------------|
| 1 | Find .env files | `scan .` |
| 2 | View variables | `audit .env` |
| 3 | Find conflicts | `conflicts .` |
| 4 | Test URLs | `validate .env` |
| 5 | Check schema | `check .env --schema .env.example` |
| 6 | Find stale values | `stale .env --context production` |
| 7 | Update values | `fix .env --key KEY --value VALUE` |
| 8 | Compare files | `diff .env .env.production` |
| 9 | CI/CD | GitHub Actions integration |
| 10 | Python API | Programmatic usage |
| 11 | Mobile builds | Pre-build validation |
| 12 | Multi-env | Audit all environments |

---

**Need more examples?** Check [CHEAT_SHEET.txt](CHEAT_SHEET.txt) for quick reference.
