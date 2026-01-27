# EnvGuard - Integration Plan

> Comprehensive guide for integrating EnvGuard into Team Brain workflows

---

## 🎯 INTEGRATION GOALS

This document outlines how EnvGuard integrates with:
1. Team Brain agents (Forge, Atlas, Clio, Nexus, Bolt)
2. Existing Team Brain tools
3. BCH (Beacon Command Hub) - future integration
4. Logan's workflows
5. CI/CD pipelines

---

## 📦 BCH INTEGRATION

### Overview

EnvGuard is primarily a CLI/Python tool. BCH integration would involve:
- Adding EnvGuard commands to BCH command palette
- Real-time .env monitoring for active projects
- Alert system for detected conflicts

### Current Status: Not Yet Integrated

**Reason:** EnvGuard is a pre-build validation tool, typically run before deployment rather than through BCH's real-time interface.

### Future BCH Commands (Proposed)

```
@envguard scan [project]     - Find all .env files
@envguard check [project]    - Full validation suite
@envguard conflicts [project] - Detect config conflicts
```

### Implementation Steps (Future)

1. Create BCH EnvGuard module
2. Add command handlers
3. Implement project context detection
4. Create alert notifications for conflicts
5. Add to BCH documentation

---

## 🤖 AI AGENT INTEGRATION

### Integration Matrix

| Agent | Primary Use Case | Method | Priority |
|-------|------------------|--------|----------|
| **Forge** | Pre-review validation, spec writing | Python API | HIGH |
| **Atlas** | Build validation, tool testing | CLI + API | HIGH |
| **Clio** | Linux server deployments | CLI | HIGH |
| **Nexus** | Cross-platform validation | CLI + API | MEDIUM |
| **Bolt** | Automated validation scripts | CLI | MEDIUM |
| **Iris** | Desktop app builds | CLI | HIGH |
| **Porter** | Mobile app builds | CLI | HIGH |

### Agent-Specific Workflows

---

#### 🔥 Forge (Orchestrator / Reviewer)

**Primary Use Case:** Pre-review validation before Bolt executes tasks

**Workflow:**
```python
# Forge reviewing a PR or task before passing to Bolt
from envguard import EnvGuard

def pre_review_validation(project_path: str) -> dict:
    """Run before assigning task to Bolt."""
    guard = EnvGuard()
    
    issues = {
        "conflicts": guard.detect_conflicts(project_path),
        "stale": guard.detect_stale(f"{project_path}/.env", context="auto"),
    }
    
    if issues["conflicts"] or issues["stale"]:
        return {
            "status": "BLOCKED",
            "reason": "Environment configuration issues detected",
            "issues": issues
        }
    
    return {"status": "READY", "issues": None}
```

**Integration Points:**
- Run before creating specs for Bolt
- Include in task queue validation
- Add to PR review checklist

---

#### ⚡ Atlas (Executor / Builder)

**Primary Use Case:** Validate environment before tool builds

**Workflow:**
```python
# Atlas tool build workflow
from envguard import EnvGuard

def pre_build_check(tool_directory: str) -> bool:
    """Run before building any tool."""
    guard = EnvGuard()
    
    # Check for env files
    env_files = guard.scan(tool_directory)
    if not env_files:
        print("[OK] No .env files - standard library only project")
        return True
    
    # Validate each env file
    for env_path in env_files:
        result = guard.audit(str(env_path))
        if result['parse_errors']:
            print(f"[X] Parse errors in {env_path}")
            return False
    
    # Check for conflicts
    conflicts = guard.detect_conflicts(tool_directory)
    if conflicts:
        print(f"[X] {len(conflicts)} conflicts detected")
        return False
    
    print("[OK] Environment validation passed")
    return True
```

**Key Commands:**
```bash
# Before every tool build
envguard scan ./ToolName
envguard conflicts ./ToolName
```

---

#### 🐧 Clio (Linux / Ubuntu Agent)

**Primary Use Case:** Server deployment validation

**Workflow:**
```bash
#!/bin/bash
# clio_deploy_check.sh

echo "=== Clio Deployment Validation ==="

# Check production env
envguard check .env.production --schema .env.example
if [ $? -ne 0 ]; then
    echo "[X] Schema validation failed"
    exit 1
fi

# Check for stale values
envguard stale .env.production --context production
if [ $? -ne 0 ]; then
    echo "[X] Stale values detected"
    exit 1
fi

# Validate URLs
envguard validate .env.production --timeout 10
if [ $? -ne 0 ]; then
    echo "[!] Some URLs unreachable (may be internal)"
fi

echo "[OK] Deployment validation passed"
```

**Platform Notes:**
- Install: `git clone` + add to PATH
- Works natively on Linux
- Use in deployment scripts

---

#### 🌐 Nexus (Multi-Platform Agent)

**Primary Use Case:** Cross-platform environment consistency

**Workflow:**
```python
# Nexus cross-platform validation
import platform
from envguard import EnvGuard

def cross_platform_check(project_path: str) -> dict:
    """Validate environment across platforms."""
    guard = EnvGuard()
    
    results = {
        "platform": platform.system(),
        "env_files": [],
        "issues": []
    }
    
    # Find all env files
    env_files = guard.scan(project_path)
    results["env_files"] = [str(f) for f in env_files]
    
    # Check each for platform-specific issues
    for env_path in env_files:
        audit = guard.audit(str(env_path))
        for key, info in audit["variables"].items():
            value = info["value"]
            
            # Check for Windows-specific paths on Linux
            if platform.system() != "Windows" and "\\\\" in value:
                results["issues"].append({
                    "key": key,
                    "issue": "Windows path detected on non-Windows platform"
                })
            
            # Check for Unix paths on Windows
            if platform.system() == "Windows" and value.startswith("/"):
                results["issues"].append({
                    "key": key,
                    "issue": "Unix path detected on Windows"
                })
    
    return results
```

---

#### 🆓 Bolt (Free Executor)

**Primary Use Case:** Automated validation in task execution

**Workflow:**
```bash
# Bolt automation script
# Run before every task execution

validate_env() {
    local project="$1"
    
    # Quick validation
    python -c "
from envguard import EnvGuard
guard = EnvGuard()
conflicts = guard.detect_conflicts('$project')
if conflicts:
    print(f'[X] {len(conflicts)} conflicts')
    exit(1)
print('[OK] No conflicts')
"
}

# Usage in task
validate_env "./project" && execute_task
```

---

#### 🖥️ Iris (Desktop Agent)

**Primary Use Case:** Desktop app build validation (Tauri, Electron)

**Workflow:**
```python
# Iris desktop build pre-check
from envguard import EnvGuard

def desktop_build_check(project_path: str) -> bool:
    """Pre-build check for desktop apps."""
    guard = EnvGuard()
    
    # Desktop apps often have multiple env files
    # .env (development)
    # .env.production (release builds)
    
    env_files = guard.scan(project_path)
    print(f"Found {len(env_files)} environment files")
    
    # For release builds, check production env
    prod_env = [f for f in env_files if 'production' in f.name]
    if prod_env:
        stale = guard.detect_stale(str(prod_env[0]), context="production")
        if stale:
            print(f"[!] {len(stale)} stale values in production env")
            for w in stale:
                print(f"    - {w['key']}: {w['message']}")
            return False
    
    return True
```

---

#### 📱 Porter (Mobile Agent)

**Primary Use Case:** Mobile app build validation (React Native, Expo)

**Workflow:**
```bash
# Porter mobile pre-build script
echo "=== Porter Mobile Build Validation ==="

# Critical for mobile: API URL must be correct
envguard conflicts ./mobile-app
if [ $? -ne 0 ]; then
    echo "[X] CRITICAL: Config conflicts detected!"
    echo "    Mobile app may connect to wrong server"
    exit 1
fi

# Check for localhost (won't work on device)
envguard stale .env --context production 2>&1 | grep -i localhost
if [ $? -eq 0 ]; then
    echo "[!] WARNING: localhost detected"
    echo "    This will NOT work on physical devices"
fi

echo "[OK] Mobile validation passed"
```

---

## 🔗 INTEGRATION WITH OTHER TEAM BRAIN TOOLS

### With BuildEnvValidator

**Use Case:** Complete build environment validation

```python
from envguard import EnvGuard
from buildenvvalidator import BuildEnvValidator

def full_build_validation(project_path: str) -> bool:
    """Complete pre-build validation."""
    
    # Step 1: Validate .env configuration
    guard = EnvGuard()
    conflicts = guard.detect_conflicts(project_path)
    if conflicts:
        print(f"[X] Fix {len(conflicts)} .env conflicts first")
        return False
    
    # Step 2: Validate build environment (Java, Node, etc.)
    validator = BuildEnvValidator()
    result = validator.validate(project_path)
    if not result['ready']:
        print(f"[X] Fix build environment issues")
        return False
    
    print("[OK] Full validation passed - ready to build")
    return True
```

### With SynapseLink

**Use Case:** Notify team of configuration issues

```python
from envguard import EnvGuard
from synapselink import quick_send

def notify_env_issues(project_path: str, project_name: str):
    """Check for issues and notify team."""
    guard = EnvGuard()
    
    conflicts = guard.detect_conflicts(project_path)
    stale = guard.detect_stale(f"{project_path}/.env.production", context="production")
    
    if conflicts or stale:
        message = f"""Environment Issues Detected in {project_name}

Conflicts: {len(conflicts)}
Stale Values: {len(stale)}

Details:
"""
        for c in conflicts[:3]:
            message += f"- Conflict: {c['key']}\n"
        for s in stale[:3]:
            message += f"- Stale: {s['key']}: {s['message']}\n"
        
        quick_send(
            "FORGE,ATLAS",
            f"[EnvGuard] Issues in {project_name}",
            message,
            priority="HIGH"
        )

# Run on project changes
notify_env_issues("./bch-mobile", "BCH Mobile")
```

### With TaskQueuePro

**Use Case:** Add validation step to task workflow

```python
from taskqueuepro import TaskQueuePro
from envguard import EnvGuard

def create_build_task(project: str, task_title: str):
    """Create task with env validation step."""
    queue = TaskQueuePro()
    guard = EnvGuard()
    
    # Pre-check environment
    conflicts = guard.detect_conflicts(project)
    
    task = queue.create_task(
        title=task_title,
        agent="BOLT",
        priority=2,
        metadata={
            "env_validated": len(conflicts) == 0,
            "env_conflicts": len(conflicts),
            "validation_tool": "EnvGuard"
        }
    )
    
    if conflicts:
        queue.add_blocker(task['id'], "Fix .env conflicts before proceeding")
    
    return task
```

### With VersionGuard

**Use Case:** Validate dependencies AND environment together

```python
from envguard import EnvGuard
from versionguard import VersionGuard

def full_project_validation(project_path: str) -> dict:
    """Complete project validation."""
    
    results = {"env": None, "deps": None, "ready": False}
    
    # Check environment
    guard = EnvGuard()
    env_issues = guard.detect_conflicts(project_path)
    results["env"] = {"conflicts": len(env_issues)}
    
    # Check dependencies
    vguard = VersionGuard()
    dep_issues = vguard.check(project_path)
    results["deps"] = {"incompatible": len(dep_issues.get("incompatible", []))}
    
    # Ready if no issues
    results["ready"] = (
        results["env"]["conflicts"] == 0 and
        results["deps"]["incompatible"] == 0
    )
    
    return results
```

### With ToolRegistry

**Use Case:** Register EnvGuard capabilities

```python
from toolregistry import ToolRegistry

def register_envguard():
    """Register EnvGuard in Team Brain tool registry."""
    registry = ToolRegistry()
    
    registry.register(
        name="EnvGuard",
        category="validation",
        capabilities=[
            "env_scan",
            "env_audit", 
            "conflict_detection",
            "url_validation",
            "schema_validation",
            "stale_detection"
        ],
        commands={
            "scan": "envguard scan [path]",
            "audit": "envguard audit [file]",
            "conflicts": "envguard conflicts [path]",
            "validate": "envguard validate [file]",
            "check": "envguard check [file] --schema [schema]",
            "stale": "envguard stale [file] --context [ctx]"
        },
        tags=["env", "config", "validation", "security", "pre-build"]
    )
```

---

## 🚀 ADOPTION ROADMAP

### Phase 1: Core Adoption (Week 1)

**Goal:** All agents aware and can use basic features

**Steps:**
1. ✅ Tool deployed to GitHub
2. ☐ Quick-start guides sent via Synapse
3. ☐ Each agent tests basic workflow
4. ☐ Feedback collected

**Success Criteria:**
- All 5 primary agents have used EnvGuard
- No blocking issues reported

### Phase 2: Workflow Integration (Week 2-3)

**Goal:** Integrated into daily workflows

**Steps:**
1. ☐ Add to pre-build checklists
2. ☐ Create integration examples with BuildEnvValidator
3. ☐ Update agent startup routines
4. ☐ Add to CI/CD pipelines

**Success Criteria:**
- Used automatically before builds
- Zero .env-related debugging sessions

### Phase 3: Advanced Integration (Week 4+)

**Goal:** Full ecosystem integration

**Steps:**
1. ☐ BCH integration (if applicable)
2. ☐ SynapseLink alerts
3. ☐ ToolRegistry listing
4. ☐ Automated monitoring

**Success Criteria:**
- Proactive issue detection
- Measurable time savings

---

## 📊 SUCCESS METRICS

**Adoption Metrics:**
- Agents using EnvGuard: Track daily
- Commands executed: Log usage
- Integration points: Count implementations

**Efficiency Metrics:**
- Debugging time saved: Target 2+ hours per incident
- Conflicts caught before build: Track count
- Failed builds prevented: Measure reduction

**Quality Metrics:**
- False positives: Should be < 5%
- Coverage: All projects with .env files
- User satisfaction: Collect feedback

---

## 🛠️ TECHNICAL INTEGRATION DETAILS

### Import Paths

```python
# Standard import
from envguard import EnvGuard, EnvFile

# Specific imports
from envguard import (
    EnvGuard,
    EnvFile,
    ENV_FILE_PATTERNS,
    CONFIG_FILE_PATTERNS,
)
```

### Error Handling

```python
from envguard import EnvGuard

guard = EnvGuard()

try:
    conflicts = guard.detect_conflicts("./project")
except FileNotFoundError as e:
    print(f"Project not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success / No issues |
| 1 | Issues detected / Error |

### JSON Output

```bash
# All commands support JSON
envguard audit .env --json | jq '.variables'
envguard conflicts . --json | jq 'length'
```

---

## 🔧 MAINTENANCE & SUPPORT

### Update Strategy
- Minor updates: As needed
- Major updates: With notification
- Security patches: Immediate

### Support Channels
- GitHub Issues: Bug reports
- Synapse: Team discussions
- Direct: Message Forge

### Known Limitations
- Conflict detection requires hardcoded values
- URL validation may timeout for internal services
- Large projects may take longer to scan

---

## 📚 ADDITIONAL RESOURCES

- **Main Documentation:** [README.md](README.md)
- **Examples:** [EXAMPLES.md](EXAMPLES.md)
- **Quick Reference:** [CHEAT_SHEET.txt](CHEAT_SHEET.txt)
- **Quick Start Guides:** [QUICK_START_GUIDES.md](QUICK_START_GUIDES.md)
- **Integration Examples:** [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)
- **GitHub:** https://github.com/DonkRonk17/EnvGuard

---

**Last Updated:** January 27, 2026  
**Maintained By:** Forge (Team Brain)
