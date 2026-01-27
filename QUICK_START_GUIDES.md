# EnvGuard - Quick Start Guides

> 5-minute guides tailored for each Team Brain agent

---

## 📖 ABOUT THESE GUIDES

Each Team Brain agent has a **5-minute quick-start guide** tailored to their role and workflows.

**Choose your guide:**
- [Forge (Orchestrator)](#-forge-quick-start)
- [Atlas (Executor)](#-atlas-quick-start)
- [Clio (Linux Agent)](#-clio-quick-start)
- [Nexus (Multi-Platform)](#-nexus-quick-start)
- [Bolt (Free Executor)](#-bolt-quick-start)
- [Iris (Desktop Agent)](#-iris-quick-start)
- [Porter (Mobile Agent)](#-porter-quick-start)

---

## 🔥 FORGE QUICK START

**Role:** Orchestrator / Reviewer  
**Time:** 5 minutes  
**Goal:** Use EnvGuard to validate environments before assigning tasks

### Step 1: Verify Installation

```bash
cd C:\Users\logan\OneDrive\Documents\AutoProjects\EnvGuard
python envguard.py --version

# Expected: envguard 1.0.0
```

### Step 2: First Use - Pre-Review Validation

Before creating specs for Bolt:

```python
from envguard import EnvGuard

def pre_review_check(project_path: str) -> bool:
    """Run before assigning task to Bolt."""
    guard = EnvGuard()
    
    # Check for conflicts
    conflicts = guard.detect_conflicts(project_path)
    if conflicts:
        print(f"[X] BLOCKED: {len(conflicts)} .env conflicts")
        for c in conflicts:
            print(f"    - {c['key']}: {c['message']}")
        return False
    
    print("[OK] Environment validated - ready for Bolt")
    return True

# Use before task assignment
pre_review_check("./bch-mobile")
```

### Step 3: Integration with Task Specs

Add to your spec templates:

```markdown
## Pre-Build Requirements

- [ ] EnvGuard validation passed: `envguard conflicts ./project`
- [ ] No stale values: `envguard stale .env --context production`
```

### Step 4: Common Forge Commands

```bash
# Quick conflict check
envguard conflicts ./project

# Full validation before review
envguard scan ./project && envguard conflicts ./project

# Check schema compliance
envguard check .env --schema .env.example
```

### Next Steps for Forge

1. Add EnvGuard checks to spec templates
2. Include in PR review checklist
3. Use in task queue validation

---

## ⚡ ATLAS QUICK START

**Role:** Executor / Builder  
**Time:** 5 minutes  
**Goal:** Validate environment before every tool build

### Step 1: Installation Check

```bash
cd C:\Users\logan\OneDrive\Documents\AutoProjects\EnvGuard
python -c "from envguard import EnvGuard; print('[OK] EnvGuard ready')"
```

### Step 2: First Use - Pre-Build Validation

Add to your tool build workflow:

```python
from envguard import EnvGuard
from pathlib import Path

def atlas_pre_build(tool_directory: str) -> bool:
    """Atlas standard pre-build check."""
    guard = EnvGuard()
    
    print(f"\n[EnvGuard] Validating {tool_directory}...")
    
    # 1. Scan for env files
    env_files = guard.scan(tool_directory)
    if not env_files:
        print("[OK] No .env files - stdlib project")
        return True
    
    print(f"[INFO] Found {len(env_files)} env file(s)")
    
    # 2. Check for conflicts
    conflicts = guard.detect_conflicts(tool_directory)
    if conflicts:
        print(f"[X] {len(conflicts)} conflicts detected!")
        return False
    
    # 3. Audit for issues
    for env_path in env_files:
        result = guard.audit(str(env_path))
        if result['parse_errors']:
            print(f"[X] Parse errors in {env_path}")
            return False
    
    print("[OK] Environment validation passed\n")
    return True

# Use in build workflow
atlas_pre_build("./NewTool")
```

### Step 3: Integration with Holy Grail

Add to Phase 2 (Development):

```bash
# Before writing any code
envguard scan ./NewTool
envguard conflicts ./NewTool
```

### Step 4: Common Atlas Commands

```bash
# Standard pre-build
envguard conflicts ./ToolName

# Full project scan
envguard scan ./ToolName --verbose

# Validate against example
envguard check .env --schema .env.example
```

### Next Steps for Atlas

1. Add to tool build checklist (Phase 2)
2. Run before every `git init`
3. Include in test suite

---

## 🐧 CLIO QUICK START

**Role:** Linux / Ubuntu Agent  
**Time:** 5 minutes  
**Goal:** Validate server deployments and Linux environments

### Step 1: Linux Installation

```bash
# Clone from GitHub
git clone https://github.com/DonkRonk17/EnvGuard.git
cd EnvGuard

# Verify
python3 envguard.py --version

# Optional: Add to PATH
echo 'alias envguard="python3 ~/EnvGuard/envguard.py"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: First Use - Deployment Validation

```bash
#!/bin/bash
# clio_deploy_check.sh

echo "=== Clio Deployment Validation ==="

PROJECT_DIR="${1:-.}"

# Schema check
python3 envguard.py check "$PROJECT_DIR/.env.production" --schema "$PROJECT_DIR/.env.example"
if [ $? -ne 0 ]; then
    echo "[X] Schema validation failed!"
    exit 1
fi

# Stale check
python3 envguard.py stale "$PROJECT_DIR/.env.production" --context production
if [ $? -ne 0 ]; then
    echo "[X] Stale values detected!"
    exit 1
fi

echo "[OK] Deployment validation passed"
```

### Step 3: Integration with Deployment Scripts

```bash
# Add to deployment script
validate_before_deploy() {
    envguard conflicts . || exit 1
    envguard stale .env.production --context production || exit 1
}

# Use in deploy
validate_before_deploy && ./deploy.sh
```

### Step 4: Common Clio Commands

```bash
# Server deployment check
envguard check .env.production --schema .env.example
envguard stale .env.production --context production
envguard validate .env.production --timeout 10

# Compare environments
envguard diff .env.staging .env.production
```

### Next Steps for Clio

1. Add to deployment scripts
2. Create systemd timer for periodic checks
3. Integrate with monitoring

---

## 🌐 NEXUS QUICK START

**Role:** Multi-Platform Agent  
**Time:** 5 minutes  
**Goal:** Cross-platform environment validation

### Step 1: Platform Detection

```python
import platform
from envguard import EnvGuard

print(f"Platform: {platform.system()}")
guard = EnvGuard()
print("[OK] EnvGuard ready")
```

### Step 2: First Use - Cross-Platform Check

```python
from envguard import EnvGuard
import platform

def nexus_cross_platform_check(project_path: str) -> dict:
    """Validate environment across platforms."""
    guard = EnvGuard()
    
    results = {
        "platform": platform.system(),
        "issues": []
    }
    
    # Scan all envs
    env_files = guard.scan(project_path)
    
    for env_path in env_files:
        audit = guard.audit(str(env_path))
        
        for key, info in audit["variables"].items():
            value = info["value"]
            
            # Check path separators
            if platform.system() == "Windows":
                if "/" in value and "://" not in value:
                    results["issues"].append(
                        f"{key}: Unix path on Windows"
                    )
            else:
                if "\\\\" in value:
                    results["issues"].append(
                        f"{key}: Windows path on {platform.system()}"
                    )
    
    return results

# Test
result = nexus_cross_platform_check("./project")
print(f"Issues: {len(result['issues'])}")
```

### Step 3: Platform-Specific Commands

**Windows:**
```powershell
python envguard.py conflicts .
python envguard.py scan . --verbose
```

**Linux/macOS:**
```bash
python3 envguard.py conflicts .
python3 envguard.py scan . --verbose
```

### Step 4: Common Nexus Commands

```bash
# Cross-platform validation
envguard scan . --verbose
envguard conflicts .
envguard diff .env .env.production
```

### Next Steps for Nexus

1. Test on all platforms
2. Document platform-specific issues
3. Add to multi-platform workflows

---

## 🆓 BOLT QUICK START

**Role:** Free Executor (Cline + Grok)  
**Time:** 5 minutes  
**Goal:** Automated validation in task execution

### Step 1: Verify Access

```bash
# No API key needed!
python envguard.py --version
```

### Step 2: First Use - Task Validation

```bash
# Run before every task
validate_env() {
    python envguard.py conflicts "$1"
    return $?
}

# Usage
validate_env "./project" && echo "Ready to execute"
```

### Step 3: Integration with Cline

Add to task execution:

```bash
# Bolt task wrapper
bolt_execute() {
    local project="$1"
    local task="$2"
    
    echo "=== Pre-Task Validation ==="
    python envguard.py conflicts "$project"
    if [ $? -ne 0 ]; then
        echo "[X] Fix .env issues first"
        return 1
    fi
    
    echo "=== Executing Task ==="
    # ... task execution ...
}
```

### Step 4: Common Bolt Commands

```bash
# Quick validation
envguard conflicts .

# Full check (batch)
envguard scan . && envguard conflicts . && envguard stale .env
```

### Next Steps for Bolt

1. Add to task templates
2. Create validation wrapper
3. Report issues via Synapse

---

## 🖥️ IRIS QUICK START

**Role:** Desktop Development Specialist  
**Time:** 5 minutes  
**Goal:** Desktop app build validation (Tauri, Electron)

### Step 1: Installation Check

```bash
cd C:\Users\logan\OneDrive\Documents\AutoProjects\EnvGuard
python envguard.py --version
```

### Step 2: First Use - Desktop Build Check

```python
from envguard import EnvGuard

def iris_desktop_prebuild(project_path: str) -> bool:
    """Pre-build check for desktop apps."""
    guard = EnvGuard()
    
    print("=== Iris Desktop Pre-Build ===")
    
    # Desktop apps need production env for release
    import os
    prod_env = os.path.join(project_path, ".env.production")
    
    if os.path.exists(prod_env):
        stale = guard.detect_stale(prod_env, context="production")
        if stale:
            print(f"[X] {len(stale)} issues in production env")
            return False
    
    # Check conflicts
    conflicts = guard.detect_conflicts(project_path)
    if conflicts:
        print(f"[X] {len(conflicts)} config conflicts")
        return False
    
    print("[OK] Ready for build")
    return True

# Before Tauri/Electron build
iris_desktop_prebuild("./bch-desktop")
```

### Step 3: Integration with Desktop Builds

```bash
# Before Tauri build
envguard conflicts ./bch-desktop
envguard stale .env.production --context production
cargo tauri build

# Before Electron build
envguard conflicts ./electron-app
npm run build
```

### Step 4: Common Iris Commands

```bash
# Desktop validation
envguard conflicts ./desktop-app
envguard stale .env.production --context production
envguard validate .env --timeout 5
```

### Next Steps for Iris

1. Add to build scripts
2. Create pre-build hook
3. Document desktop-specific checks

---

## 📱 PORTER QUICK START

**Role:** Mobile Development Specialist  
**Time:** 5 minutes  
**Goal:** Mobile app build validation (React Native, Expo)

### Step 1: Installation Check

```bash
cd C:\Users\logan\OneDrive\Documents\AutoProjects\EnvGuard
python envguard.py --version
```

### Step 2: First Use - Mobile Build Check

**This is CRITICAL for mobile apps!** .env issues caused 2+ hours of debugging.

```python
from envguard import EnvGuard

def porter_mobile_prebuild(project_path: str) -> bool:
    """Pre-build check for mobile apps."""
    guard = EnvGuard()
    
    print("=== Porter Mobile Pre-Build ===")
    
    # CRITICAL: API URL conflicts
    conflicts = guard.detect_conflicts(project_path)
    api_conflicts = [c for c in conflicts if 'URL' in c.get('key', '')]
    
    if api_conflicts:
        print("[X] CRITICAL: API URL conflicts!")
        for c in api_conflicts:
            print(f"    .env: {c['env_value']}")
            print(f"    config: {c['config_value']}")
        print("    Mobile app will use .env value!")
        return False
    
    # Check for localhost (won't work on device)
    import os
    env_file = os.path.join(project_path, ".env")
    if os.path.exists(env_file):
        stale = guard.detect_stale(env_file)
        localhost = [w for w in stale if 'localhost' in str(w.get('value', ''))]
        if localhost:
            print("[!] WARNING: localhost URLs detected")
            print("    These will NOT work on physical devices")
    
    print("[OK] Ready for mobile build")
    return True

# Before Expo/RN build
porter_mobile_prebuild("./bch-mobile")
```

### Step 3: Integration with Mobile Builds

```bash
# Before Expo build
envguard conflicts ./mobile-app
envguard stale .env
npx expo build

# Before React Native build
envguard conflicts ./rn-app
npx react-native run-android
```

### Step 4: Common Porter Commands

```bash
# Mobile validation (RUN EVERY TIME!)
envguard conflicts ./mobile-app
envguard stale .env

# Check all env variants
envguard scan ./mobile-app --verbose
envguard diff .env .env.production
```

### Next Steps for Porter

1. **ALWAYS** run before builds
2. Add to Expo scripts
3. Create pre-build hook

---

## 📚 ADDITIONAL RESOURCES

**For All Agents:**
- Full Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Integration Plan: [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
- Cheat Sheet: [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

**Support:**
- GitHub Issues: https://github.com/DonkRonk17/EnvGuard/issues
- Synapse: Post in THE_SYNAPSE/active/
- Direct: Message Forge

---

**Last Updated:** January 27, 2026  
**Maintained By:** Forge (Team Brain)
