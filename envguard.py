#!/usr/bin/env python3
"""
EnvGuard - .env Configuration Validator & Conflict Detector

Catches when .env files override code configurations, validates environment
variables against schemas, detects stale values, and tests URL reachability.

Born from a 2+ hour debugging session where a .env file was silently overriding
config.ts changes, causing mobile app builds to use the wrong server URL.

Author: Forge (Team Brain)
For: Logan Smith / Metaphy LLC
Version: 1.0
Date: January 27, 2026
License: MIT

Features:
- Scan projects for all .env files (.env, .env.local, .env.production, etc.)
- Audit environment variables with sensitive value masking
- Detect conflicts between .env and hardcoded config files
- Validate URL/IP reachability for connection strings
- Check .env against schema files (.env.example)
- Flag stale/suspicious values (localhost in production, old IPs)
- Cross-platform support (Windows, Linux, macOS)

Zero external dependencies - uses only Python standard library.
Optional: urllib for URL validation (included in stdlib).
"""

import argparse
import json
import os
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

__version__ = "1.0.0"
__author__ = "Forge (Team Brain)"


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS AND PATTERNS
# ═══════════════════════════════════════════════════════════════════

# .env file patterns to scan for
ENV_FILE_PATTERNS = [
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.staging",
    ".env.test",
    ".env.example",
    ".env.sample",
    ".env.defaults",
]

# Config file patterns that might conflict with .env
CONFIG_FILE_PATTERNS = [
    "config.ts",
    "config.js",
    "config.json",
    "settings.py",
    "settings.json",
    "app.config.ts",
    "app.config.js",
    "constants.ts",
    "constants.js",
    "environment.ts",
    "environment.js",
]

# Keys that typically contain sensitive values (should be masked)
SENSITIVE_KEY_PATTERNS = [
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*KEY.*",
    r".*TOKEN.*",
    r".*API.*KEY.*",
    r".*PRIVATE.*",
    r".*CREDENTIAL.*",
    r".*AUTH.*",
]

# Keys that typically contain URLs (should be validated)
URL_KEY_PATTERNS = [
    r".*URL.*",
    r".*URI.*",
    r".*ENDPOINT.*",
    r".*HOST.*",
    r".*SERVER.*",
    r".*API.*",
    r".*BASE.*URL.*",
]

# Patterns for detecting stale/suspicious values
STALE_PATTERNS = {
    "localhost_in_prod": {
        "pattern": r"localhost|127\.0\.0\.1",
        "contexts": ["production", "staging", "prod"],
        "message": "Localhost detected - likely stale for non-development environments"
    },
    "old_ip_format": {
        "pattern": r"192\.168\.\d+\.\d+",
        "contexts": ["production", "staging", "prod"],
        "message": "Private IP detected - may not work outside local network"
    },
    "example_domain": {
        "pattern": r"example\.com|test\.com|foo\.bar",
        "contexts": ["production", "staging", "prod"],
        "message": "Example/test domain detected - likely placeholder"
    },
    "empty_value": {
        "pattern": r"^$",
        "contexts": ["all"],
        "message": "Empty value detected - may cause runtime errors"
    },
    "placeholder": {
        "pattern": r"YOUR_|CHANGE_ME|TODO|FIXME|XXX|<.*>|\$\{.*\}",
        "contexts": ["all"],
        "message": "Placeholder value detected - needs to be replaced"
    },
}


# ═══════════════════════════════════════════════════════════════════
# CORE CLASSES
# ═══════════════════════════════════════════════════════════════════

class EnvFile:
    """Represents a parsed .env file."""
    
    def __init__(self, path: Path):
        """Initialize with path to .env file."""
        self.path = Path(path)
        self.variables: Dict[str, str] = {}
        self.comments: List[str] = []
        self.parse_errors: List[str] = []
        self._parse()
    
    def _parse(self) -> None:
        """Parse the .env file."""
        if not self.path.exists():
            self.parse_errors.append(f"File not found: {self.path}")
            return
        
        try:
            content = self.path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            try:
                content = self.path.read_text(encoding='latin-1')
            except Exception as e:
                self.parse_errors.append(f"Failed to read file: {e}")
                return
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Collect comments
            if line.startswith('#'):
                self.comments.append(line)
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                # Remove quotes from value
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                if key:
                    self.variables[key] = value
                else:
                    self.parse_errors.append(f"Line {line_num}: Invalid format (empty key)")
            else:
                self.parse_errors.append(f"Line {line_num}: No '=' found in '{line[:30]}...'")
    
    def get(self, key: str, default: str = "") -> str:
        """Get a variable value."""
        return self.variables.get(key, default)
    
    def keys(self) -> List[str]:
        """Get all variable keys."""
        return list(self.variables.keys())
    
    def items(self) -> List[Tuple[str, str]]:
        """Get all key-value pairs."""
        return list(self.variables.items())
    
    def __len__(self) -> int:
        """Return number of variables."""
        return len(self.variables)
    
    def __bool__(self) -> bool:
        """Return True if file was parsed successfully."""
        return len(self.parse_errors) == 0 or len(self.variables) > 0


class EnvGuard:
    """
    Main EnvGuard class for .env validation and conflict detection.
    
    Example:
        >>> guard = EnvGuard()
        >>> files = guard.scan("./my-project")
        >>> guard.audit(files[0])
        >>> conflicts = guard.detect_conflicts("./my-project")
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize EnvGuard.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
    
    def scan(self, path: str, recursive: bool = True) -> List[Path]:
        """
        Scan a directory for all .env files.
        
        Args:
            path: Directory path to scan
            recursive: Search subdirectories
            
        Returns:
            List of Path objects for found .env files
        """
        root = Path(path).resolve()
        found_files: List[Path] = []
        
        if not root.exists():
            raise FileNotFoundError(f"Path not found: {root}")
        
        if root.is_file():
            # Single file provided
            if root.name in ENV_FILE_PATTERNS or root.name.startswith('.env'):
                found_files.append(root)
            return found_files
        
        # Directory scan
        if recursive:
            for env_pattern in ENV_FILE_PATTERNS:
                found_files.extend(root.rglob(env_pattern))
            # Also find any .env.* files
            found_files.extend(root.rglob(".env.*"))
        else:
            for env_pattern in ENV_FILE_PATTERNS:
                env_path = root / env_pattern
                if env_path.exists():
                    found_files.append(env_path)
            # Also check for .env.* patterns
            for f in root.iterdir():
                if f.is_file() and f.name.startswith('.env.'):
                    found_files.append(f)
        
        # Remove duplicates and sort
        found_files = sorted(set(found_files))
        
        # Filter out node_modules, .git, etc.
        exclude_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build'}
        found_files = [
            f for f in found_files 
            if not any(excluded in f.parts for excluded in exclude_dirs)
        ]
        
        return found_files
    
    def audit(self, env_path: str, mask_sensitive: bool = True) -> Dict[str, Any]:
        """
        Audit an .env file and return structured results.
        
        Args:
            env_path: Path to .env file
            mask_sensitive: Mask sensitive values
            
        Returns:
            Dict with audit results
        """
        env = EnvFile(env_path)
        
        result = {
            "path": str(env.path),
            "exists": env.path.exists(),
            "variable_count": len(env),
            "variables": {},
            "parse_errors": env.parse_errors,
            "warnings": [],
        }
        
        for key, value in env.items():
            is_sensitive = self._is_sensitive_key(key)
            display_value = self._mask_value(value) if (mask_sensitive and is_sensitive) else value
            
            result["variables"][key] = {
                "value": display_value,
                "sensitive": is_sensitive,
                "is_url": self._is_url_key(key),
                "length": len(value),
            }
        
        return result
    
    def detect_conflicts(self, project_path: str) -> List[Dict[str, Any]]:
        """
        Detect conflicts between .env files and config files.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            List of conflict descriptions
        """
        root = Path(project_path).resolve()
        conflicts: List[Dict[str, Any]] = []
        
        # Find all .env files
        env_files = self.scan(str(root))
        
        # Parse .env files
        env_vars: Dict[str, Dict[str, str]] = {}
        for env_path in env_files:
            env = EnvFile(env_path)
            env_vars[str(env_path)] = dict(env.items())
        
        # Find and scan config files
        config_files: List[Path] = []
        for pattern in CONFIG_FILE_PATTERNS:
            config_files.extend(root.rglob(pattern))
        
        # Filter out node_modules, etc.
        exclude_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.venv'}
        config_files = [
            f for f in config_files 
            if not any(excluded in f.parts for excluded in exclude_dirs)
        ]
        
        # Check each config file for potential conflicts
        for config_path in config_files:
            try:
                content = config_path.read_text(encoding='utf-8')
            except Exception:
                continue
            
            # Look for hardcoded values that match env var patterns
            for env_path, vars_dict in env_vars.items():
                for key, env_value in vars_dict.items():
                    # Check if the config file references this env var OR has a hardcoded value
                    
                    # Pattern 1: Hardcoded value that differs from .env
                    # Look for patterns like: url: "http://192.168.x.x"
                    # or: const API_URL = "http://..."
                    
                    # Pattern for common assignment patterns
                    assignment_patterns = [
                        rf'{key}\s*[=:]\s*["\']([^"\']+)["\']',  # KEY = "value" or KEY: "value"
                        rf'(?:const|let|var)\s+{key}\s*=\s*["\']([^"\']+)["\']',  # const KEY = "value"
                    ]
                    
                    for pattern in assignment_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if match != env_value and env_value:
                                conflicts.append({
                                    "type": "value_conflict",
                                    "env_file": env_path,
                                    "config_file": str(config_path),
                                    "key": key,
                                    "env_value": env_value,
                                    "config_value": match,
                                    "message": f".env will OVERRIDE config file value",
                                    "severity": "HIGH",
                                })
                    
                    # Pattern 2: Check for process.env references without fallback
                    env_ref_pattern = rf'process\.env\.{key}(?!\s*\|\|)'
                    if re.search(env_ref_pattern, content):
                        # env var is referenced - check if .env has it
                        if not env_value:
                            conflicts.append({
                                "type": "missing_value",
                                "env_file": env_path,
                                "config_file": str(config_path),
                                "key": key,
                                "message": f"Config references process.env.{key} but .env value is empty",
                                "severity": "MEDIUM",
                            })
        
        return conflicts
    
    def validate_urls(self, env_path: str, timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Validate URL/IP values in an .env file for reachability.
        
        Args:
            env_path: Path to .env file
            timeout: Connection timeout in seconds
            
        Returns:
            List of validation results
        """
        env = EnvFile(env_path)
        results: List[Dict[str, Any]] = []
        
        for key, value in env.items():
            if not self._is_url_key(key):
                continue
            
            # Extract URL-like values
            url = value.strip()
            if not url:
                results.append({
                    "key": key,
                    "value": url,
                    "reachable": False,
                    "error": "Empty value",
                    "response_time": None,
                })
                continue
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            # Test reachability
            result = self._test_url(url, timeout)
            result["key"] = key
            result["value"] = value
            results.append(result)
        
        return results
    
    def check_schema(self, env_path: str, schema_path: str) -> Dict[str, Any]:
        """
        Validate .env file against a schema file (typically .env.example).
        
        Args:
            env_path: Path to .env file to validate
            schema_path: Path to schema/example file
            
        Returns:
            Dict with validation results
        """
        env = EnvFile(env_path)
        schema = EnvFile(schema_path)
        
        env_keys = set(env.keys())
        schema_keys = set(schema.keys())
        
        missing_keys = schema_keys - env_keys
        extra_keys = env_keys - schema_keys
        common_keys = env_keys & schema_keys
        
        result = {
            "env_file": str(env_path),
            "schema_file": str(schema_path),
            "valid": len(missing_keys) == 0,
            "missing_keys": sorted(missing_keys),
            "extra_keys": sorted(extra_keys),
            "matched_keys": sorted(common_keys),
            "coverage": len(common_keys) / len(schema_keys) * 100 if schema_keys else 100,
            "warnings": [],
        }
        
        # Check for empty required values
        for key in common_keys:
            if schema.get(key) and not env.get(key):
                result["warnings"].append(f"{key}: Schema has value but .env is empty")
        
        return result
    
    def detect_stale(self, env_path: str, context: str = "auto") -> List[Dict[str, Any]]:
        """
        Detect stale or suspicious values in an .env file.
        
        Args:
            env_path: Path to .env file
            context: Environment context (development, production, staging, or auto)
            
        Returns:
            List of warnings for stale/suspicious values
        """
        env = EnvFile(env_path)
        warnings: List[Dict[str, Any]] = []
        
        # Auto-detect context from filename
        if context == "auto":
            filename = env.path.name.lower()
            if "prod" in filename:
                context = "production"
            elif "staging" in filename:
                context = "staging"
            elif "test" in filename:
                context = "test"
            else:
                context = "development"
        
        for key, value in env.items():
            for pattern_name, pattern_info in STALE_PATTERNS.items():
                contexts = pattern_info["contexts"]
                
                # Check if this pattern applies to current context
                if "all" not in contexts and context not in contexts:
                    continue
                
                # Check if value matches the stale pattern
                if re.search(pattern_info["pattern"], value, re.IGNORECASE):
                    warnings.append({
                        "key": key,
                        "value": value,
                        "pattern": pattern_name,
                        "context": context,
                        "message": pattern_info["message"],
                        "severity": "WARNING" if context == "development" else "HIGH",
                    })
        
        return warnings
    
    def update_value(self, env_path: str, key: str, value: str, create: bool = False) -> bool:
        """
        Update or add a value in an .env file.
        
        Args:
            env_path: Path to .env file
            key: Variable key to update
            value: New value
            create: Create key if it doesn't exist
            
        Returns:
            True if successful, False otherwise
        """
        path = Path(env_path)
        
        if not path.exists():
            if create:
                # Create new .env file
                path.write_text(f"{key}={value}\n", encoding='utf-8')
                return True
            return False
        
        # Read existing content
        lines = path.read_text(encoding='utf-8').splitlines()
        
        # Find and update the key
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}=") or line.strip().startswith(f"{key} ="):
                new_lines.append(f"{key}={value}")
                updated = True
            else:
                new_lines.append(line)
        
        # Add new key if not found and create=True
        if not updated:
            if create:
                new_lines.append(f"{key}={value}")
                updated = True
            else:
                return False
        
        # Write back
        path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
        return True
    
    def diff(self, env_path1: str, env_path2: str) -> Dict[str, Any]:
        """
        Compare two .env files and show differences.
        
        Args:
            env_path1: Path to first .env file
            env_path2: Path to second .env file
            
        Returns:
            Dict with comparison results
        """
        env1 = EnvFile(env_path1)
        env2 = EnvFile(env_path2)
        
        keys1 = set(env1.keys())
        keys2 = set(env2.keys())
        
        only_in_first = keys1 - keys2
        only_in_second = keys2 - keys1
        common_keys = keys1 & keys2
        
        # Find keys with different values
        different_values = {}
        same_values = []
        for key in common_keys:
            v1 = env1.get(key)
            v2 = env2.get(key)
            if v1 != v2:
                different_values[key] = {"file1": v1, "file2": v2}
            else:
                same_values.append(key)
        
        return {
            "file1": str(env_path1),
            "file2": str(env_path2),
            "only_in_file1": sorted(only_in_first),
            "only_in_file2": sorted(only_in_second),
            "different_values": different_values,
            "same_values": sorted(same_values),
            "total_keys_file1": len(keys1),
            "total_keys_file2": len(keys2),
            "similarity": len(same_values) / max(len(common_keys), 1) * 100,
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key typically contains sensitive data."""
        key_upper = key.upper()
        for pattern in SENSITIVE_KEY_PATTERNS:
            if re.match(pattern, key_upper):
                return True
        return False
    
    def _is_url_key(self, key: str) -> bool:
        """Check if a key typically contains a URL."""
        key_upper = key.upper()
        for pattern in URL_KEY_PATTERNS:
            if re.match(pattern, key_upper):
                return True
        return False
    
    def _mask_value(self, value: str) -> str:
        """Mask a sensitive value, showing only first/last characters."""
        if len(value) <= 4:
            return "****"
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
    
    def _test_url(self, url: str, timeout: int = 5) -> Dict[str, Any]:
        """Test if a URL is reachable."""
        import time
        
        result = {
            "url": url,
            "reachable": False,
            "status_code": None,
            "response_time": None,
            "error": None,
        }
        
        try:
            start = time.time()
            req = Request(url, headers={'User-Agent': 'EnvGuard/1.0'})
            response = urlopen(req, timeout=timeout)
            result["response_time"] = round((time.time() - start) * 1000)
            result["status_code"] = response.status
            result["reachable"] = True
        except HTTPError as e:
            result["status_code"] = e.code
            result["error"] = f"HTTP {e.code}: {e.reason}"
            # 4xx/5xx errors still mean reachable
            if e.code < 500:
                result["reachable"] = True
        except URLError as e:
            result["error"] = str(e.reason)
        except socket.timeout:
            result["error"] = "Connection timed out"
        except Exception as e:
            result["error"] = str(e)
        
        return result


# ═══════════════════════════════════════════════════════════════════
# CLI FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def format_table(headers: List[str], rows: List[List[str]], max_width: int = 50) -> str:
    """Format data as a simple ASCII table."""
    if not rows:
        return "No data to display."
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if len(cell_str) > max_width:
                cell_str = cell_str[:max_width-3] + "..."
            widths[i] = max(widths[i], len(cell_str))
    
    # Build table
    lines = []
    
    # Header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-+-".join("-" * w for w in widths))
    
    # Rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if len(cell_str) > max_width:
                cell_str = cell_str[:max_width-3] + "..."
            cells.append(cell_str.ljust(widths[i]))
        lines.append(" | ".join(cells))
    
    return "\n".join(lines)


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute scan command."""
    guard = EnvGuard(verbose=args.verbose)
    path = args.path or "."
    
    try:
        files = guard.scan(path, recursive=not args.no_recursive)
    except FileNotFoundError as e:
        print(f"[X] Error: {e}")
        return 1
    
    if not files:
        print(f"[!] No .env files found in {path}")
        return 0
    
    print(f"\n[OK] Found {len(files)} .env file(s) in {path}:\n")
    
    for f in files:
        env = EnvFile(f)
        status = "[OK]" if env else "[!]"
        print(f"  {status} {f}")
        print(f"      Variables: {len(env)}")
        if env.parse_errors and args.verbose:
            for err in env.parse_errors:
                print(f"      [!] {err}")
    
    print()
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Execute audit command."""
    guard = EnvGuard(verbose=args.verbose)
    env_path = args.env_file
    
    if not Path(env_path).exists():
        print(f"[X] Error: File not found: {env_path}")
        return 1
    
    result = guard.audit(env_path, mask_sensitive=not args.show_secrets)
    
    print(f"\n[OK] Audit: {result['path']}")
    print(f"    Variables: {result['variable_count']}")
    
    if result['parse_errors']:
        print(f"    [!] Parse errors: {len(result['parse_errors'])}")
        for err in result['parse_errors']:
            print(f"        - {err}")
    
    print("\n" + "=" * 70)
    
    # Format as table
    rows = []
    for key, info in sorted(result['variables'].items()):
        flags = []
        if info['sensitive']:
            flags.append("SENSITIVE")
        if info['is_url']:
            flags.append("URL")
        flag_str = f"[{', '.join(flags)}]" if flags else ""
        rows.append([key, info['value'], flag_str])
    
    if rows:
        print(format_table(["KEY", "VALUE", "FLAGS"], rows))
    else:
        print("No variables found.")
    
    print("=" * 70 + "\n")
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(result, indent=2))
    
    return 0


def cmd_conflicts(args: argparse.Namespace) -> int:
    """Execute conflicts detection command."""
    guard = EnvGuard(verbose=args.verbose)
    path = args.path or "."
    
    print(f"\n[...] Scanning for conflicts in {path}...")
    
    try:
        conflicts = guard.detect_conflicts(path)
    except Exception as e:
        print(f"[X] Error: {e}")
        return 1
    
    if not conflicts:
        print("\n[OK] No conflicts detected!")
        return 0
    
    print(f"\n[!] Found {len(conflicts)} conflict(s):\n")
    
    for i, conflict in enumerate(conflicts, 1):
        severity_icon = "[!]" if conflict.get('severity') == 'HIGH' else "[?]"
        print(f"{severity_icon} Conflict #{i}: {conflict['type']}")
        print(f"    Key: {conflict['key']}")
        print(f"    .env file: {conflict['env_file']}")
        print(f"    Config file: {conflict['config_file']}")
        if 'env_value' in conflict:
            print(f"    .env value: {conflict['env_value']}")
        if 'config_value' in conflict:
            print(f"    Config value: {conflict['config_value']}")
        print(f"    Message: {conflict['message']}")
        print()
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(conflicts, indent=2))
    
    return 1 if any(c.get('severity') == 'HIGH' for c in conflicts) else 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute URL validation command."""
    guard = EnvGuard(verbose=args.verbose)
    env_path = args.env_file
    
    if not Path(env_path).exists():
        print(f"[X] Error: File not found: {env_path}")
        return 1
    
    print(f"\n[...] Validating URLs in {env_path}...\n")
    
    results = guard.validate_urls(env_path, timeout=args.timeout)
    
    if not results:
        print("[!] No URL-like variables found.")
        return 0
    
    all_reachable = True
    for result in results:
        if result['reachable']:
            time_str = f"{result['response_time']}ms" if result['response_time'] else "N/A"
            print(f"[OK] {result['key']}: {result['value']}")
            print(f"     Status: {result.get('status_code', 'OK')} | Response time: {time_str}")
        else:
            all_reachable = False
            print(f"[X] {result['key']}: {result['value']}")
            print(f"     Error: {result['error']}")
        print()
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(results, indent=2))
    
    return 0 if all_reachable else 1


def cmd_check(args: argparse.Namespace) -> int:
    """Execute schema check command."""
    guard = EnvGuard(verbose=args.verbose)
    env_path = args.env_file
    schema_path = args.schema
    
    for path in [env_path, schema_path]:
        if not Path(path).exists():
            print(f"[X] Error: File not found: {path}")
            return 1
    
    print(f"\n[...] Checking {env_path} against {schema_path}...\n")
    
    result = guard.check_schema(env_path, schema_path)
    
    if result['valid']:
        print(f"[OK] Schema validation PASSED")
    else:
        print(f"[X] Schema validation FAILED")
    
    print(f"\n    Coverage: {result['coverage']:.1f}%")
    print(f"    Matched keys: {len(result['matched_keys'])}")
    
    if result['missing_keys']:
        print(f"\n    [!] Missing keys ({len(result['missing_keys'])}):")
        for key in result['missing_keys']:
            print(f"        - {key}")
    
    if result['extra_keys']:
        print(f"\n    [?] Extra keys ({len(result['extra_keys'])}):")
        for key in result['extra_keys']:
            print(f"        + {key}")
    
    if result['warnings']:
        print(f"\n    [!] Warnings:")
        for warning in result['warnings']:
            print(f"        - {warning}")
    
    print()
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(result, indent=2))
    
    return 0 if result['valid'] else 1


def cmd_stale(args: argparse.Namespace) -> int:
    """Execute stale value detection command."""
    guard = EnvGuard(verbose=args.verbose)
    env_path = args.env_file
    
    if not Path(env_path).exists():
        print(f"[X] Error: File not found: {env_path}")
        return 1
    
    context = args.context or "auto"
    
    print(f"\n[...] Checking for stale values in {env_path} (context: {context})...\n")
    
    warnings = guard.detect_stale(env_path, context=context)
    
    if not warnings:
        print("[OK] No stale or suspicious values detected!")
        return 0
    
    high_severity = [w for w in warnings if w['severity'] == 'HIGH']
    low_severity = [w for w in warnings if w['severity'] != 'HIGH']
    
    if high_severity:
        print(f"[!] HIGH severity warnings ({len(high_severity)}):\n")
        for w in high_severity:
            print(f"    [!] {w['key']} = {w['value']}")
            print(f"        {w['message']}")
            print()
    
    if low_severity:
        print(f"[?] Warnings ({len(low_severity)}):\n")
        for w in low_severity:
            print(f"    [?] {w['key']} = {w['value']}")
            print(f"        {w['message']}")
            print()
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(warnings, indent=2))
    
    return 1 if high_severity else 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Execute fix command to update a value."""
    guard = EnvGuard(verbose=args.verbose)
    env_path = args.env_file
    key = args.key
    value = args.value
    
    if not Path(env_path).exists() and not args.create:
        print(f"[X] Error: File not found: {env_path}")
        print("    Use --create to create a new .env file")
        return 1
    
    success = guard.update_value(env_path, key, value, create=args.create)
    
    if success:
        print(f"[OK] Updated {key} in {env_path}")
        return 0
    else:
        print(f"[X] Failed to update {key} in {env_path}")
        return 1


def cmd_diff(args: argparse.Namespace) -> int:
    """Execute diff command to compare two .env files."""
    guard = EnvGuard(verbose=args.verbose)
    file1 = args.file1
    file2 = args.file2
    
    for path in [file1, file2]:
        if not Path(path).exists():
            print(f"[X] Error: File not found: {path}")
            return 1
    
    print(f"\n[...] Comparing {file1} vs {file2}...\n")
    
    result = guard.diff(file1, file2)
    
    print(f"[OK] Comparison complete\n")
    print(f"    File 1: {result['file1']} ({result['total_keys_file1']} keys)")
    print(f"    File 2: {result['file2']} ({result['total_keys_file2']} keys)")
    print(f"    Similarity: {result['similarity']:.1f}%")
    
    if result['only_in_file1']:
        print(f"\n    Only in File 1 ({len(result['only_in_file1'])}):")
        for key in result['only_in_file1']:
            print(f"        - {key}")
    
    if result['only_in_file2']:
        print(f"\n    Only in File 2 ({len(result['only_in_file2'])}):")
        for key in result['only_in_file2']:
            print(f"        + {key}")
    
    if result['different_values']:
        print(f"\n    Different values ({len(result['different_values'])}):")
        for key, values in result['different_values'].items():
            print(f"        {key}:")
            print(f"            File 1: {values['file1']}")
            print(f"            File 2: {values['file2']}")
    
    print()
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(result, indent=2))
    
    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='envguard',
        description='EnvGuard - .env Configuration Validator & Conflict Detector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  envguard scan .                        # Find all .env files in current directory
  envguard audit .env                    # Show all variables (sensitive masked)
  envguard audit .env --show-secrets     # Show all values including secrets
  envguard conflicts ./my-project        # Check for config conflicts
  envguard validate .env                 # Test URL reachability
  envguard check .env --schema .env.example  # Validate against schema
  envguard stale .env --context production   # Check for stale values
  envguard fix .env --key API_URL --value "http://new.url"  # Update a value
  envguard diff .env .env.production     # Compare two .env files

For more information: https://github.com/DonkRonk17/EnvGuard
        """
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Find all .env files in a directory')
    scan_parser.add_argument('path', nargs='?', default='.', help='Directory to scan (default: current)')
    scan_parser.add_argument('--no-recursive', action='store_true', help='Do not search subdirectories')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Show all variables in an .env file')
    audit_parser.add_argument('env_file', help='Path to .env file')
    audit_parser.add_argument('--show-secrets', action='store_true', help='Show sensitive values unmasked')
    
    # Conflicts command
    conflicts_parser = subparsers.add_parser('conflicts', help='Detect .env vs config file conflicts')
    conflicts_parser.add_argument('path', nargs='?', default='.', help='Project directory to scan')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Test URL/IP reachability')
    validate_parser.add_argument('env_file', help='Path to .env file')
    validate_parser.add_argument('--timeout', type=int, default=5, help='Connection timeout in seconds')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Validate .env against schema')
    check_parser.add_argument('env_file', help='Path to .env file')
    check_parser.add_argument('--schema', required=True, help='Path to schema file (.env.example)')
    
    # Stale command
    stale_parser = subparsers.add_parser('stale', help='Detect stale/suspicious values')
    stale_parser.add_argument('env_file', help='Path to .env file')
    stale_parser.add_argument('--context', choices=['development', 'production', 'staging', 'test', 'auto'],
                             default='auto', help='Environment context (default: auto-detect from filename)')
    
    # Fix command
    fix_parser = subparsers.add_parser('fix', help='Update a value in .env file')
    fix_parser.add_argument('env_file', help='Path to .env file')
    fix_parser.add_argument('--key', required=True, help='Variable key to update')
    fix_parser.add_argument('--value', required=True, help='New value')
    fix_parser.add_argument('--create', action='store_true', help='Create key if not exists')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Compare two .env files')
    diff_parser.add_argument('file1', help='First .env file')
    diff_parser.add_argument('file2', help='Second .env file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Route to command handler
    commands = {
        'scan': cmd_scan,
        'audit': cmd_audit,
        'conflicts': cmd_conflicts,
        'validate': cmd_validate,
        'check': cmd_check,
        'stale': cmd_stale,
        'fix': cmd_fix,
        'diff': cmd_diff,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
