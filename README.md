# 🛡️ EnvGuard - .env Configuration Validator & Conflict Detector

> **Catch .env configuration issues in seconds instead of hours of debugging.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)](https://github.com/DonkRonk17/EnvGuard)
[![Tests: 40 Passing](https://img.shields.io/badge/tests-40%20passing-brightgreen.svg)](https://github.com/DonkRonk17/EnvGuard)

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [CLI Commands](#cli-commands)
  - [Python API](#python-api)
- [Real-World Results](#-real-world-results)
- [Use Cases](#-use-cases)
- [Advanced Features](#-advanced-features)
- [How It Works](#-how-it-works)
- [Integration](#-integration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Credits](#-credits)

---

## 🚨 The Problem

**Have you ever spent hours debugging an app, only to discover a `.env` file was silently overriding your code?**

This exact scenario happened during a mobile app build session:

```
Problem: Mobile app kept connecting to wrong server URL (192.168.4.66)
Time Spent: 2+ hours debugging config.ts, checking network settings
Root Cause: .env file had old IP hardcoded, overriding ALL code changes
```

**.env files have a hidden superpower: they override EVERYTHING.**

When you run your app:
1. Your code says `API_URL = "http://production.server.com"`
2. Your `.env` says `API_URL=http://192.168.4.66`
3. **The `.env` wins. Always.**

This "feature" causes:
- ❌ Hours of debugging "why isn't my code change working?"
- ❌ Deployed production apps connecting to development servers
- ❌ Secrets accidentally exposed or misconfigured
- ❌ Team members with incompatible environment setups
- ❌ Mobile/desktop builds using stale configurations

**The Result:** 2+ hours wasted on a problem that a simple `.env` check would have caught in seconds.

---

## 💡 The Solution

**EnvGuard** is a comprehensive `.env` configuration validator that:

1. **Scans** your project for all `.env` files (including variants)
2. **Audits** environment variables with sensitive value masking
3. **Detects conflicts** between `.env` and hardcoded config files
4. **Validates URLs** for reachability before you waste time debugging
5. **Checks schemas** to ensure all required variables are set
6. **Flags stale values** like localhost in production or placeholder text

**Catch `.env` issues in 5 seconds, not 2 hours.**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Project Scan** | Find all `.env` files recursively (`.env`, `.env.local`, `.env.production`, etc.) |
| 📋 **Variable Audit** | Display all variables with automatic sensitive value masking |
| ⚠️ **Conflict Detection** | Detect when `.env` will override hardcoded config values |
| 🌐 **URL Validation** | Test if URL/IP values are actually reachable |
| 📐 **Schema Checking** | Validate `.env` against `.env.example` templates |
| 🔄 **Stale Detection** | Flag localhost in production, placeholders, empty values |
| 🔧 **Fix Command** | Update values directly from CLI |
| 📊 **Diff Command** | Compare two `.env` files side by side |
| 🖥️ **Cross-Platform** | Works on Windows, Linux, and macOS |
| 📦 **Zero Dependencies** | Uses only Python standard library |

---

## 🚀 Quick Start

**5-second installation:**

```bash
# Clone the repository
git clone https://github.com/DonkRonk17/EnvGuard.git
cd EnvGuard

# That's it! No pip install needed (zero dependencies)
python envguard.py --help
```

**Find all .env files in your project:**

```bash
python envguard.py scan ./my-project
```

**Output:**
```
[OK] Found 3 .env file(s) in ./my-project:

  [OK] ./my-project/.env
      Variables: 12
  [OK] ./my-project/.env.local
      Variables: 3
  [OK] ./my-project/.env.production
      Variables: 12
```

**Check for conflicts:**

```bash
python envguard.py conflicts ./my-project
```

**Output:**
```
[!] Found 1 conflict(s):

[!] Conflict #1: value_conflict
    Key: API_URL
    .env file: ./my-project/.env
    Config file: ./my-project/config.ts
    .env value: http://192.168.4.66:3000
    Config value: http://production.server.com
    Message: .env will OVERRIDE config file value
```

**That's it!** You just caught an issue that would have taken hours to debug.

---

## 📥 Installation

### Option 1: Clone (Recommended)

```bash
git clone https://github.com/DonkRonk17/EnvGuard.git
cd EnvGuard
python envguard.py --help
```

### Option 2: Direct Download

```bash
# Download just the script
curl -O https://raw.githubusercontent.com/DonkRonk17/EnvGuard/main/envguard.py

# Run directly
python envguard.py --help
```

### Option 3: pip Install (Development Mode)

```bash
git clone https://github.com/DonkRonk17/EnvGuard.git
cd EnvGuard
pip install -e .

# Now available globally as 'envguard'
envguard --help
```

### Requirements

- **Python 3.8+** (no external packages needed!)
- Works on **Windows**, **Linux**, and **macOS**

---

## 📚 Usage

### CLI Commands

EnvGuard provides 8 powerful commands:

#### 1. `scan` - Find All .env Files

```bash
# Scan current directory
envguard scan .

# Scan specific project
envguard scan ./my-project

# Non-recursive scan (current directory only)
envguard scan ./my-project --no-recursive
```

#### 2. `audit` - View Environment Variables

```bash
# Show all variables (sensitive values masked)
envguard audit .env

# Show all values including secrets
envguard audit .env --show-secrets

# Output as JSON
envguard audit .env --json
```

**Example Output:**
```
[OK] Audit: .env
    Variables: 5

======================================================================
KEY            | VALUE                      | FLAGS
---------------+----------------------------+-----------------
API_KEY        | su********************45   | [SENSITIVE]
API_URL        | http://api.example.com     | [URL]
DATABASE_HOST  | localhost                  | [URL]
DEBUG          | true                       |
PORT           | 3000                       |
======================================================================
```

#### 3. `conflicts` - Detect Configuration Conflicts

```bash
# Check for conflicts in project
envguard conflicts ./my-project

# Output as JSON
envguard conflicts ./my-project --json
```

#### 4. `validate` - Test URL Reachability

```bash
# Validate all URL-like variables
envguard validate .env

# Custom timeout
envguard validate .env --timeout 10
```

**Example Output:**
```
[...] Validating URLs in .env...

[OK] API_URL: http://api.example.com
     Status: 200 | Response time: 145ms

[X] DATABASE_HOST: http://192.168.4.66:5432
     Error: Connection timed out
```

#### 5. `check` - Validate Against Schema

```bash
# Check .env against .env.example
envguard check .env --schema .env.example
```

**Example Output:**
```
[X] Schema validation FAILED

    Coverage: 75.0%
    Matched keys: 6

    [!] Missing keys (2):
        - REDIS_URL
        - SMTP_PASSWORD

    [?] Extra keys (1):
        + DEBUG_MODE
```

#### 6. `stale` - Detect Stale/Suspicious Values

```bash
# Auto-detect context from filename
envguard stale .env.production

# Specify context explicitly
envguard stale .env --context production
```

**Example Output:**
```
[!] HIGH severity warnings (2):

    [!] API_URL = http://localhost:3000
        Localhost detected - likely stale for non-development environments

    [!] DATABASE_HOST = 192.168.4.66
        Private IP detected - may not work outside local network
```

#### 7. `fix` - Update Values

```bash
# Update an existing value
envguard fix .env --key API_URL --value "http://new.server.com"

# Create a new key
envguard fix .env --key NEW_KEY --value "value" --create
```

#### 8. `diff` - Compare Two Files

```bash
# Compare development and production configs
envguard diff .env .env.production
```

**Example Output:**
```
[OK] Comparison complete

    File 1: .env (12 keys)
    File 2: .env.production (10 keys)
    Similarity: 75.0%

    Only in File 1 (2):
        - DEBUG
        - HOT_RELOAD

    Different values (3):
        API_URL:
            File 1: http://localhost:3000
            File 2: http://api.production.com
```

### Python API

EnvGuard also provides a powerful Python API:

```python
from envguard import EnvGuard, EnvFile

# Initialize
guard = EnvGuard()

# Scan for .env files
files = guard.scan("./my-project")
print(f"Found {len(files)} .env files")

# Audit a specific file
result = guard.audit(".env", mask_sensitive=True)
for key, info in result['variables'].items():
    print(f"{key}: {info['value']}")

# Detect conflicts
conflicts = guard.detect_conflicts("./my-project")
for conflict in conflicts:
    print(f"Conflict: {conflict['key']} - {conflict['message']}")

# Validate URLs
validations = guard.validate_urls(".env", timeout=5)
for v in validations:
    status = "[OK]" if v['reachable'] else "[X]"
    print(f"{status} {v['key']}: {v['value']}")

# Check schema
result = guard.check_schema(".env", ".env.example")
if not result['valid']:
    print(f"Missing keys: {result['missing_keys']}")

# Detect stale values
warnings = guard.detect_stale(".env.production", context="production")
for w in warnings:
    print(f"[!] {w['key']}: {w['message']}")

# Compare files
diff = guard.diff(".env", ".env.production")
print(f"Similarity: {diff['similarity']:.1f}%")
```

---

## 📊 Real-World Results

### Before EnvGuard

```
Problem:  Mobile app using wrong server URL
Debug:    Check code → Check network → Check configs → Nothing works
Time:     2+ hours
Solution: Discovered .env had old IP hardcoded
Feeling:  Frustrated 😤
```

### After EnvGuard

```bash
$ envguard conflicts ./bch-mobile

[!] Conflict #1: value_conflict
    Key: API_URL
    .env value: http://192.168.4.66:3000
    Config value: http://production.server.com
    Message: .env will OVERRIDE config file value

Time: 5 seconds
Feeling: Relieved 😊
```

### Impact

| Metric | Before | After |
|--------|--------|-------|
| Debug time for .env issues | 2+ hours | < 1 minute |
| Confidence in configs | Low | High |
| Production misconfigs | Occasional | Rare |
| Developer frustration | High | Minimal |

---

## 🎯 Use Cases

### 1. Mobile App Development

```bash
# Before every build
envguard conflicts ./mobile-app
envguard validate .env
```

Catches issues like:
- Wrong API URL in .env
- Development server in production build
- Missing required environment variables

### 2. Pre-Deployment Checks

```bash
# Add to CI/CD pipeline
envguard check .env.production --schema .env.example
envguard stale .env.production --context production
```

Catches issues like:
- Missing required variables
- Localhost/private IPs in production
- Placeholder values not replaced

### 3. Team Onboarding

```bash
# Validate new team member's setup
envguard check .env --schema .env.example
envguard diff .env .env.example
```

Ensures:
- All required variables are configured
- No accidental misconfiguration

### 4. Multi-Environment Management

```bash
# Compare environments
envguard diff .env.development .env.production
envguard diff .env.staging .env.production
```

Helps with:
- Understanding environment differences
- Catching unintended variations

### 5. Security Audits

```bash
# Check for exposed secrets
envguard audit .env --show-secrets  # Review carefully!
envguard stale .env  # Find placeholders
```

Identifies:
- Placeholder secrets not replaced
- Overly permissive configurations

---

## 🔧 Advanced Features

### JSON Output

All commands support JSON output for automation:

```bash
envguard audit .env --json
envguard conflicts ./project --json
envguard validate .env --json
```

### Verbose Mode

Enable detailed output:

```bash
envguard scan . --verbose
envguard audit .env --verbose
```

### Context-Aware Stale Detection

EnvGuard auto-detects context from filenames:
- `.env.production` → production context
- `.env.staging` → staging context
- `.env.development` → development context
- `.env` → development context (default)

Or specify explicitly:

```bash
envguard stale .env --context production
```

### Custom Schema Validation

Use any file as a schema:

```bash
# Use .env.example as schema
envguard check .env --schema .env.example

# Use custom schema file
envguard check .env --schema config/required-env.txt
```

---

## 🏗️ How It Works

### Architecture

```
EnvGuard
├── EnvFile          # .env file parser
│   ├── parse()      # KEY=VALUE parsing with quotes, comments
│   ├── variables    # Parsed key-value pairs
│   └── comments     # Preserved comments
│
└── EnvGuard         # Main validation engine
    ├── scan()       # Recursive .env file discovery
    ├── audit()      # Variable listing with masking
    ├── detect_conflicts()  # .env vs config comparison
    ├── validate_urls()     # URL reachability testing
    ├── check_schema()      # Schema validation
    ├── detect_stale()      # Suspicious value detection
    ├── update_value()      # .env file modification
    └── diff()       # Two-file comparison
```

### Conflict Detection Algorithm

1. **Scan** project for all `.env` files
2. **Parse** each `.env` file into key-value pairs
3. **Find** config files (`config.ts`, `settings.py`, etc.)
4. **Search** config files for hardcoded values matching `.env` keys
5. **Compare** values and **report conflicts** when different

### Stale Value Detection Patterns

| Pattern | Description | Contexts |
|---------|-------------|----------|
| `localhost\|127.0.0.1` | Localhost detection | production, staging |
| `192.168.x.x` | Private IP detection | production, staging |
| `example.com` | Example domain | production, staging |
| `YOUR_\|CHANGE_ME` | Placeholder values | all |
| Empty string | Empty values | all |

---

## 🔗 Integration

### With BuildEnvValidator

```python
from envguard import EnvGuard
from buildenvvalidator import BuildEnvValidator

# First, check .env configuration
guard = EnvGuard()
conflicts = guard.detect_conflicts("./mobile-app")
if conflicts:
    print("Fix .env conflicts first!")
    sys.exit(1)

# Then validate build environment
validator = BuildEnvValidator()
validator.validate("./mobile-app")
```

### With SynapseLink

```python
from envguard import EnvGuard
from synapselink import quick_send

guard = EnvGuard()
conflicts = guard.detect_conflicts("./project")

if conflicts:
    quick_send(
        "TEAM",
        ".env Conflicts Detected",
        f"Found {len(conflicts)} conflicts in project",
        priority="HIGH"
    )
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate Environment
  run: |
    python envguard.py check .env.production --schema .env.example
    python envguard.py stale .env.production --context production
    python envguard.py validate .env.production
```

**See:** [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for complete integration guides.

---

## 🔍 Troubleshooting

### Common Issues

#### "File not found" Error

```bash
[X] Error: File not found: .env
```

**Solution:** Make sure the file exists. Use `scan` to find `.env` files:

```bash
envguard scan .
```

#### No Conflicts Detected (But Expected)

EnvGuard looks for hardcoded values in config files. If your config only references `process.env.VAR`, no conflict will be detected (that's correct behavior - the `.env` is supposed to provide the value).

Conflicts are detected when:
- Config has `API_URL = "http://example.com"`
- .env has `API_URL=http://different.com`

#### URL Validation Timeouts

```bash
[X] API_URL: http://internal.server
     Error: Connection timed out
```

**Solutions:**
- Increase timeout: `--timeout 10`
- Internal URLs may not be reachable from your machine
- VPN may be required for internal services

#### Unicode/Encoding Errors

EnvGuard attempts UTF-8 first, then falls back to Latin-1. If you still have issues:

```bash
# Check file encoding
file .env
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Write tests for new functionality
4. Ensure all tests pass (`python test_envguard.py`)
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/DonkRonk17/EnvGuard.git
cd EnvGuard
python test_envguard.py  # Run tests
```

### Code Style

- Type hints for all functions
- Docstrings for public methods
- No Unicode emojis in Python code (ASCII only)
- Cross-platform compatibility required

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 📝 Credits

**Built by:** Forge (Team Brain)  
**For:** Logan Smith / Metaphy LLC  
**Requested by:** Forge (Self-initiated based on debugging session)  
**Why:** Prevent hours of .env debugging - catch issues in seconds  
**Part of:** Beacon HQ / Team Brain Ecosystem  
**Date:** January 27, 2026

### Origin Story

Born from a 2+ hour debugging session where a mobile app kept connecting to the wrong server. After extensive debugging of code, configs, and network settings, the root cause was discovered: a `.env` file had an old IP hardcoded and was silently overriding all code changes.

Logan's reaction: *"Do we already have an env checker tool? Sounds like this could be a good tool request."*

And thus, EnvGuard was born.

### Special Thanks

- The Team Brain collective for testing and feedback
- Every developer who's ever spent hours debugging a `.env` issue

---

## 📚 Additional Resources

- **Examples:** [EXAMPLES.md](EXAMPLES.md) - 10+ detailed usage examples
- **Quick Reference:** [CHEAT_SHEET.txt](CHEAT_SHEET.txt) - CLI reference card
- **Integration:** [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Full integration guide
- **Quick Start Guides:** [QUICK_START_GUIDES.md](QUICK_START_GUIDES.md) - Agent-specific guides

---

**Never waste hours debugging .env issues again. Use EnvGuard.**

```
Together for all time! ⚔️🔥
- Team Brain
```
