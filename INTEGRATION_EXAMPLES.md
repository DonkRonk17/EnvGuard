# EnvGuard - Integration Examples

> Copy-paste-ready code examples for common integration patterns

---

## 🎯 INTEGRATION PHILOSOPHY

EnvGuard is designed to work seamlessly with other Team Brain tools. This document provides **copy-paste-ready code examples** for common integration patterns.

---

## 📚 TABLE OF CONTENTS

1. [Pattern 1: EnvGuard + BuildEnvValidator](#pattern-1-envguard--buildenvvalidator)
2. [Pattern 2: EnvGuard + SynapseLink](#pattern-2-envguard--synapselink)
3. [Pattern 3: EnvGuard + TaskQueuePro](#pattern-3-envguard--taskqueuepro)
4. [Pattern 4: EnvGuard + VersionGuard](#pattern-4-envguard--versionguard)
5. [Pattern 5: EnvGuard + ToolRegistry](#pattern-5-envguard--toolregistry)
6. [Pattern 6: EnvGuard + SessionReplay](#pattern-6-envguard--sessionreplay)
7. [Pattern 7: EnvGuard + AgentHealth](#pattern-7-envguard--agenthealth)
8. [Pattern 8: CI/CD Pipeline Integration](#pattern-8-cicd-pipeline-integration)
9. [Pattern 9: Pre-Build Validation Script](#pattern-9-pre-build-validation-script)
10. [Pattern 10: Full Team Brain Stack](#pattern-10-full-team-brain-stack)

---

## Pattern 1: EnvGuard + BuildEnvValidator

**Use Case:** Complete build environment validation - both .env configs AND build tools

**Why:** Catch ALL environment issues before building

**Code:**

```python
#!/usr/bin/env python3
"""Complete pre-build environment validation."""

from envguard import EnvGuard
from buildenvvalidator import BuildEnvValidator
import sys

def full_build_validation(project_path: str) -> bool:
    """
    Validate both .env configuration and build environment.
    
    Step 1: EnvGuard validates .env files
    Step 2: BuildEnvValidator checks build tools
    """
    print("=" * 60)
    print("FULL BUILD ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    # Step 1: .env Configuration Validation
    print("\n[1/2] Validating .env configuration...")
    guard = EnvGuard()
    
    conflicts = guard.detect_conflicts(project_path)
    if conflicts:
        print(f"[X] Found {len(conflicts)} .env conflicts!")
        for c in conflicts:
            print(f"    - {c['key']}: {c['message']}")
        return False
    print("[OK] No .env conflicts")
    
    # Check for stale values
    import os
    env_prod = os.path.join(project_path, ".env.production")
    if os.path.exists(env_prod):
        stale = guard.detect_stale(env_prod, context="production")
        if stale:
            print(f"[X] Found {len(stale)} stale values in production env")
            return False
        print("[OK] No stale values in production")
    
    # Step 2: Build Environment Validation
    print("\n[2/2] Validating build environment...")
    validator = BuildEnvValidator()
    result = validator.validate(project_path)
    
    if not result.get('ready', False):
        print(f"[X] Build environment not ready")
        return False
    print("[OK] Build environment validated")
    
    print("\n" + "=" * 60)
    print("VALIDATION PASSED - Ready to build!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    success = full_build_validation(project)
    sys.exit(0 if success else 1)
```

**Result:** Catches both .env issues AND missing build tools

---

## Pattern 2: EnvGuard + SynapseLink

**Use Case:** Notify Team Brain when .env issues are detected

**Why:** Proactive alerts keep team informed of configuration problems

**Code:**

```python
#!/usr/bin/env python3
"""Notify Team Brain of .env issues via SynapseLink."""

from envguard import EnvGuard
from synapselink import quick_send

def notify_env_issues(project_path: str, project_name: str):
    """
    Check for .env issues and notify team if found.
    
    Args:
        project_path: Path to project directory
        project_name: Human-readable project name
    """
    guard = EnvGuard()
    
    # Check for various issues
    conflicts = guard.detect_conflicts(project_path)
    
    import os
    env_file = os.path.join(project_path, ".env")
    stale = []
    if os.path.exists(env_file):
        stale = guard.detect_stale(env_file, context="auto")
    
    # Calculate severity
    high_severity = [s for s in stale if s.get('severity') == 'HIGH']
    has_issues = bool(conflicts or high_severity)
    
    if has_issues:
        # Build notification message
        message = f"""[EnvGuard] Environment Issues Detected

Project: {project_name}
Path: {project_path}

Issues Found:
- Conflicts: {len(conflicts)}
- Stale Values (HIGH): {len(high_severity)}

"""
        if conflicts:
            message += "Conflicts:\n"
            for c in conflicts[:5]:  # Limit to 5
                message += f"  - {c['key']}: .env overrides config\n"
        
        if high_severity:
            message += "\nStale Values:\n"
            for s in high_severity[:5]:
                message += f"  - {s['key']}: {s['message']}\n"
        
        message += "\nAction Required: Fix before build/deploy"
        
        # Send notification
        quick_send(
            "FORGE,ATLAS,IRIS,PORTER",
            f"[EnvGuard] Issues in {project_name}",
            message,
            priority="HIGH"
        )
        
        print(f"[!] Notified team of {len(conflicts) + len(high_severity)} issues")
    else:
        print(f"[OK] No critical issues in {project_name}")

# Example usage
notify_env_issues("./bch-mobile", "BCH Mobile App")
```

**Result:** Team gets proactive alerts about configuration issues

---

## Pattern 3: EnvGuard + TaskQueuePro

**Use Case:** Add environment validation as a task prerequisite

**Why:** Prevent tasks from starting with broken configurations

**Code:**

```python
#!/usr/bin/env python3
"""Integrate EnvGuard validation into task workflow."""

from envguard import EnvGuard
from taskqueuepro import TaskQueuePro

def create_validated_task(
    project_path: str,
    task_title: str,
    assigned_agent: str
) -> dict:
    """
    Create a task with automatic environment validation.
    
    If validation fails, task is created with a blocker.
    """
    queue = TaskQueuePro()
    guard = EnvGuard()
    
    print(f"[EnvGuard] Validating environment for: {task_title}")
    
    # Run validation
    conflicts = guard.detect_conflicts(project_path)
    env_validated = len(conflicts) == 0
    
    # Create task with validation metadata
    task = queue.create_task(
        title=task_title,
        agent=assigned_agent,
        priority=2,
        metadata={
            "project_path": project_path,
            "env_validated": env_validated,
            "env_conflicts": len(conflicts),
            "validation_tool": "EnvGuard v1.0"
        }
    )
    
    # Add blocker if validation failed
    if not env_validated:
        queue.add_blocker(
            task['id'],
            f"Fix {len(conflicts)} .env conflicts before proceeding. "
            f"Run: envguard conflicts {project_path}"
        )
        print(f"[!] Task created with BLOCKER: {len(conflicts)} conflicts")
    else:
        print(f"[OK] Task created - environment validated")
    
    return task

# Example usage
task = create_validated_task(
    project_path="./bch-mobile",
    task_title="Build mobile app for production",
    assigned_agent="BOLT"
)
print(f"Task ID: {task['id']}")
```

**Result:** Tasks are automatically blocked if environment is invalid

---

## Pattern 4: EnvGuard + VersionGuard

**Use Case:** Validate both environment AND dependency versions

**Why:** Catch version mismatches that cause build failures

**Code:**

```python
#!/usr/bin/env python3
"""Combined environment and version validation."""

from envguard import EnvGuard
from versionguard import VersionGuard
import sys

def comprehensive_validation(project_path: str) -> dict:
    """
    Validate:
    1. .env configuration (EnvGuard)
    2. Package versions (VersionGuard)
    """
    results = {
        "env_issues": [],
        "version_issues": [],
        "ready": False
    }
    
    print("=" * 50)
    print("COMPREHENSIVE PROJECT VALIDATION")
    print("=" * 50)
    
    # Step 1: Environment validation
    print("\n[1/2] Checking .env configuration...")
    guard = EnvGuard()
    
    conflicts = guard.detect_conflicts(project_path)
    results["env_issues"] = [
        f"{c['key']}: {c['message']}" for c in conflicts
    ]
    
    if conflicts:
        print(f"[X] {len(conflicts)} .env conflicts")
    else:
        print("[OK] No .env conflicts")
    
    # Step 2: Version validation
    print("\n[2/2] Checking package versions...")
    vguard = VersionGuard()
    
    # Check for compatibility issues
    version_result = vguard.check(project_path)
    incompatible = version_result.get("incompatible", [])
    results["version_issues"] = incompatible
    
    if incompatible:
        print(f"[X] {len(incompatible)} version incompatibilities")
    else:
        print("[OK] Versions compatible")
    
    # Determine if ready
    results["ready"] = (
        len(results["env_issues"]) == 0 and
        len(results["version_issues"]) == 0
    )
    
    print("\n" + "=" * 50)
    if results["ready"]:
        print("VALIDATION PASSED")
    else:
        print(f"VALIDATION FAILED")
        print(f"  - Env issues: {len(results['env_issues'])}")
        print(f"  - Version issues: {len(results['version_issues'])}")
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    result = comprehensive_validation(project)
    sys.exit(0 if result["ready"] else 1)
```

**Result:** Catch both configuration AND version issues in one check

---

## Pattern 5: EnvGuard + ToolRegistry

**Use Case:** Register EnvGuard's capabilities for discovery

**Why:** Other agents can find and use EnvGuard automatically

**Code:**

```python
#!/usr/bin/env python3
"""Register EnvGuard in the Team Brain tool registry."""

from toolregistry import ToolRegistry

def register_envguard():
    """Register EnvGuard capabilities."""
    registry = ToolRegistry()
    
    registry.register(
        name="EnvGuard",
        version="1.0.0",
        category="validation",
        description=".env Configuration Validator & Conflict Detector",
        
        capabilities=[
            "env_file_scanning",
            "variable_auditing",
            "conflict_detection",
            "url_validation",
            "schema_checking",
            "stale_detection",
            "value_updating",
            "file_comparison"
        ],
        
        commands={
            "scan": {
                "syntax": "envguard scan [path]",
                "description": "Find all .env files in directory"
            },
            "audit": {
                "syntax": "envguard audit [file]",
                "description": "List all variables with masking"
            },
            "conflicts": {
                "syntax": "envguard conflicts [path]",
                "description": "Detect .env vs config conflicts"
            },
            "validate": {
                "syntax": "envguard validate [file]",
                "description": "Test URL reachability"
            },
            "check": {
                "syntax": "envguard check [file] --schema [schema]",
                "description": "Validate against schema"
            },
            "stale": {
                "syntax": "envguard stale [file] --context [ctx]",
                "description": "Detect stale values"
            }
        },
        
        tags=[
            "env", "dotenv", "configuration", "validation",
            "conflict", "detection", "pre-build", "security"
        ],
        
        integrations=[
            "BuildEnvValidator",
            "SynapseLink",
            "TaskQueuePro",
            "VersionGuard"
        ],
        
        author="Forge (Team Brain)",
        github="https://github.com/DonkRonk17/EnvGuard"
    )
    
    print("[OK] EnvGuard registered in ToolRegistry")

if __name__ == "__main__":
    register_envguard()
```

**Result:** EnvGuard discoverable by all Team Brain agents

---

## Pattern 6: EnvGuard + SessionReplay

**Use Case:** Record environment validation in session logs

**Why:** Debug build failures by reviewing what was validated

**Code:**

```python
#!/usr/bin/env python3
"""Record EnvGuard validation in session replay."""

from envguard import EnvGuard
from sessionreplay import SessionReplay

def validated_build_session(
    project_path: str,
    agent_name: str,
    task_description: str
) -> bool:
    """
    Run build with full session recording including env validation.
    """
    replay = SessionReplay()
    guard = EnvGuard()
    
    # Start session
    session_id = replay.start_session(
        agent_name,
        task=task_description
    )
    
    try:
        # Log env validation
        replay.log_input(session_id, f"EnvGuard: Validating {project_path}")
        
        # Run validation
        conflicts = guard.detect_conflicts(project_path)
        
        replay.log_output(
            session_id,
            f"EnvGuard: {len(conflicts)} conflicts detected"
        )
        
        if conflicts:
            for c in conflicts:
                replay.log_output(
                    session_id,
                    f"  Conflict: {c['key']} - {c['message']}"
                )
            replay.end_session(session_id, status="BLOCKED")
            return False
        
        # Continue with build...
        replay.log_input(session_id, "Starting build process...")
        
        # ... build code here ...
        
        replay.log_output(session_id, "Build completed successfully")
        replay.end_session(session_id, status="COMPLETED")
        return True
        
    except Exception as e:
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        raise

# Example usage
validated_build_session(
    "./bch-mobile",
    "PORTER",
    "Mobile app production build"
)
```

**Result:** Full audit trail of what was validated and when

---

## Pattern 7: EnvGuard + AgentHealth

**Use Case:** Track environment validation as part of agent health

**Why:** Monitor validation patterns across sessions

**Code:**

```python
#!/usr/bin/env python3
"""Correlate env validation with agent health monitoring."""

from envguard import EnvGuard
from agenthealth import AgentHealth
import time

def health_monitored_validation(
    project_path: str,
    agent_name: str
) -> bool:
    """
    Run validation with health monitoring.
    """
    health = AgentHealth()
    guard = EnvGuard()
    
    # Start health session
    session_id = f"envguard_{int(time.time())}"
    health.start_session(agent_name, session_id=session_id)
    
    try:
        # Log heartbeat before validation
        health.heartbeat(agent_name, status="validating")
        
        # Run validation
        start_time = time.time()
        conflicts = guard.detect_conflicts(project_path)
        duration = time.time() - start_time
        
        # Log metrics
        health.log_metric(agent_name, "env_validation_time", duration)
        health.log_metric(agent_name, "env_conflicts_found", len(conflicts))
        
        if conflicts:
            health.log_error(
                agent_name,
                f"EnvGuard: {len(conflicts)} conflicts in {project_path}"
            )
            health.heartbeat(agent_name, status="blocked")
            return False
        
        health.heartbeat(agent_name, status="validated")
        return True
        
    finally:
        health.end_session(
            agent_name,
            session_id=session_id,
            status="success" if not conflicts else "blocked"
        )

# Example
health_monitored_validation("./project", "ATLAS")
```

**Result:** Validation metrics tracked in agent health dashboards

---

## Pattern 8: CI/CD Pipeline Integration

**Use Case:** Add EnvGuard to automated build pipelines

**Why:** Catch issues before they reach production

**GitHub Actions:**

```yaml
# .github/workflows/env-validation.yml
name: Environment Validation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

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
      
      - name: Validate Schema
        run: |
          python EnvGuard/envguard.py check .env.production --schema .env.example
      
      - name: Check Stale Values
        run: |
          python EnvGuard/envguard.py stale .env.production --context production
      
      - name: Detect Conflicts
        run: |
          python EnvGuard/envguard.py conflicts .
      
      - name: Summary
        if: always()
        run: |
          echo "EnvGuard validation complete"
```

**Result:** Automatic validation on every push/PR

---

## Pattern 9: Pre-Build Validation Script

**Use Case:** Single script for complete pre-build validation

**Why:** One command to run all checks

**Code:**

```python
#!/usr/bin/env python3
"""
Complete pre-build validation script.

Usage:
    python pre_build_check.py [project_path]
"""

import sys
from pathlib import Path
from envguard import EnvGuard

def pre_build_check(project_path: str = ".") -> int:
    """
    Run all pre-build checks.
    
    Returns:
        0 if all checks pass, 1 otherwise
    """
    guard = EnvGuard()
    project = Path(project_path).resolve()
    
    print("=" * 60)
    print(f"PRE-BUILD VALIDATION: {project.name}")
    print("=" * 60)
    
    checks_passed = True
    
    # Check 1: Scan for env files
    print("\n[1/5] Scanning for .env files...")
    env_files = guard.scan(str(project))
    print(f"      Found {len(env_files)} file(s)")
    
    # Check 2: Detect conflicts
    print("\n[2/5] Checking for conflicts...")
    conflicts = guard.detect_conflicts(str(project))
    if conflicts:
        print(f"      [X] {len(conflicts)} conflicts found!")
        for c in conflicts[:3]:
            print(f"          - {c['key']}")
        checks_passed = False
    else:
        print("      [OK] No conflicts")
    
    # Check 3: Schema validation
    print("\n[3/5] Validating schema...")
    env_file = project / ".env"
    example_file = project / ".env.example"
    if env_file.exists() and example_file.exists():
        schema = guard.check_schema(str(env_file), str(example_file))
        if not schema['valid']:
            print(f"      [X] Missing: {schema['missing_keys']}")
            checks_passed = False
        else:
            print(f"      [OK] Coverage: {schema['coverage']:.0f}%")
    else:
        print("      [SKIP] No .env.example found")
    
    # Check 4: Stale values
    print("\n[4/5] Checking for stale values...")
    prod_env = project / ".env.production"
    if prod_env.exists():
        stale = guard.detect_stale(str(prod_env), context="production")
        high = [s for s in stale if s['severity'] == 'HIGH']
        if high:
            print(f"      [X] {len(high)} HIGH severity issues")
            checks_passed = False
        else:
            print("      [OK] No stale values")
    else:
        if env_file.exists():
            stale = guard.detect_stale(str(env_file), context="auto")
            high = [s for s in stale if s['severity'] == 'HIGH']
            if high:
                print(f"      [!] {len(high)} warnings")
        else:
            print("      [SKIP] No .env found")
    
    # Check 5: Parse errors
    print("\n[5/5] Checking for parse errors...")
    has_errors = False
    for env_path in env_files:
        audit = guard.audit(str(env_path))
        if audit['parse_errors']:
            print(f"      [X] Errors in {env_path.name}")
            has_errors = True
    if not has_errors:
        print("      [OK] All files parse correctly")
    else:
        checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if checks_passed:
        print("VALIDATION PASSED - Ready to build!")
        return 0
    else:
        print("VALIDATION FAILED - Fix issues before building")
        return 1

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(pre_build_check(project))
```

**Result:** Single command for complete validation

---

## Pattern 10: Full Team Brain Stack

**Use Case:** Ultimate integration with all Team Brain tools

**Why:** Production-grade agent operation

**Code:**

```python
#!/usr/bin/env python3
"""
Full Team Brain stack integration example.

Demonstrates EnvGuard working with:
- TaskQueuePro (task management)
- AgentHealth (health monitoring)
- SessionReplay (audit logging)
- SynapseLink (notifications)
- VersionGuard (dependency checking)
- BuildEnvValidator (build tools)
"""

from envguard import EnvGuard
from taskqueuepro import TaskQueuePro
from agenthealth import AgentHealth
from sessionreplay import SessionReplay
from synapselink import quick_send
# from versionguard import VersionGuard
# from buildenvvalidator import BuildEnvValidator
import time
import sys

def full_stack_build(
    project_path: str,
    project_name: str,
    agent_name: str
) -> bool:
    """
    Complete build workflow with full tool integration.
    """
    # Initialize all tools
    guard = EnvGuard()
    queue = TaskQueuePro()
    health = AgentHealth()
    replay = SessionReplay()
    
    # Generate unique session ID
    session_id = f"build_{project_name}_{int(time.time())}"
    
    print(f"[Session: {session_id}]")
    print("=" * 60)
    print(f"FULL STACK BUILD: {project_name}")
    print("=" * 60)
    
    # Start tracking
    health.start_session(agent_name, session_id=session_id)
    replay_id = replay.start_session(agent_name, task=f"Build {project_name}")
    
    try:
        # Create task in queue
        task = queue.create_task(
            title=f"Build {project_name}",
            agent=agent_name,
            priority=1,
            metadata={"session_id": session_id}
        )
        queue.start_task(task['id'])
        
        # Phase 1: Environment Validation
        print("\n[Phase 1/3] Environment Validation")
        health.heartbeat(agent_name, status="validating_env")
        replay.log_input(replay_id, "Starting EnvGuard validation")
        
        conflicts = guard.detect_conflicts(project_path)
        
        if conflicts:
            replay.log_error(replay_id, f"{len(conflicts)} conflicts")
            queue.fail_task(task['id'], error="Env conflicts")
            quick_send(
                "FORGE",
                f"Build Blocked: {project_name}",
                f"{len(conflicts)} .env conflicts detected",
                priority="HIGH"
            )
            return False
        
        replay.log_output(replay_id, "Env validation passed")
        print("  [OK] Environment validated")
        
        # Phase 2: Build Process
        print("\n[Phase 2/3] Build Process")
        health.heartbeat(agent_name, status="building")
        replay.log_input(replay_id, "Starting build")
        
        # ... actual build code here ...
        time.sleep(1)  # Simulate build
        
        replay.log_output(replay_id, "Build completed")
        print("  [OK] Build completed")
        
        # Phase 3: Post-Build Verification
        print("\n[Phase 3/3] Post-Build Verification")
        health.heartbeat(agent_name, status="verifying")
        
        # ... verification code here ...
        
        print("  [OK] Verification passed")
        
        # Success!
        queue.complete_task(task['id'], result="Build successful")
        replay.end_session(replay_id, status="COMPLETED")
        health.end_session(agent_name, session_id=session_id, status="success")
        
        quick_send(
            "TEAM",
            f"Build Complete: {project_name}",
            "Build and validation successful",
            priority="NORMAL"
        )
        
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        return True
        
    except Exception as e:
        # Handle failure
        replay.log_error(replay_id, str(e))
        replay.end_session(replay_id, status="FAILED")
        health.log_error(agent_name, str(e))
        health.end_session(agent_name, session_id=session_id, status="failed")
        
        quick_send(
            "FORGE,LOGAN",
            f"Build Failed: {project_name}",
            str(e),
            priority="HIGH"
        )
        
        print(f"\n[X] BUILD FAILED: {e}")
        return False

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "./project"
    name = sys.argv[2] if len(sys.argv) > 2 else "MyProject"
    
    success = full_stack_build(project, name, "ATLAS")
    sys.exit(0 if success else 1)
```

**Result:** Fully instrumented, coordinated build workflow

---

## 📊 RECOMMENDED INTEGRATION PRIORITY

**Week 1 (Essential):**
1. ✅ Pre-build validation script (Pattern 9)
2. ✅ CI/CD integration (Pattern 8)
3. ✅ SynapseLink alerts (Pattern 2)

**Week 2 (Productivity):**
4. ☐ TaskQueuePro integration (Pattern 3)
5. ☐ VersionGuard combo (Pattern 4)
6. ☐ ToolRegistry listing (Pattern 5)

**Week 3 (Advanced):**
7. ☐ SessionReplay logging (Pattern 6)
8. ☐ AgentHealth metrics (Pattern 7)
9. ☐ Full stack (Pattern 10)

---

## 🔧 TROUBLESHOOTING INTEGRATIONS

**Import Errors:**
```python
# Ensure tools are in Python path
import sys
from pathlib import Path
sys.path.append(str(Path.home() / "OneDrive/Documents/AutoProjects"))

# Then import
from envguard import EnvGuard
```

**Version Conflicts:**
```bash
# Check versions
python -c "from envguard import __version__; print(__version__)"

# Update if needed
cd AutoProjects/EnvGuard
git pull origin main
```

**Integration Not Working:**
1. Verify both tools are installed
2. Check import paths
3. Test each tool independently
4. Review error messages

---

**Last Updated:** January 27, 2026  
**Maintained By:** Forge (Team Brain)
