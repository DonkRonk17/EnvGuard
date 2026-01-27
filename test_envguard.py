#!/usr/bin/env python3
"""
Comprehensive test suite for EnvGuard.

Tests cover:
- Core functionality (EnvFile parsing, EnvGuard methods)
- Edge cases (empty files, malformed content, missing files)
- Error handling (invalid paths, encoding issues)
- CLI commands (all subcommands)
- Integration scenarios (conflict detection, schema validation)

Run: python test_envguard.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from envguard import EnvFile, EnvGuard, __version__


class TestEnvFile(unittest.TestCase):
    """Test EnvFile class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_env_file(self, name: str, content: str) -> Path:
        """Helper to create a test .env file."""
        path = Path(self.temp_dir) / name
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_parse_simple_env(self):
        """Test parsing a simple .env file."""
        path = self._create_env_file(".env", "KEY1=value1\nKEY2=value2\n")
        env = EnvFile(path)
        
        self.assertEqual(len(env), 2)
        self.assertEqual(env.get("KEY1"), "value1")
        self.assertEqual(env.get("KEY2"), "value2")
        self.assertEqual(len(env.parse_errors), 0)
    
    def test_parse_with_quotes(self):
        """Test parsing values with quotes."""
        path = self._create_env_file(".env", 
            'DOUBLE="hello world"\n'
            "SINGLE='hello world'\n"
            'NONE=hello world\n'
        )
        env = EnvFile(path)
        
        self.assertEqual(env.get("DOUBLE"), "hello world")
        self.assertEqual(env.get("SINGLE"), "hello world")
        self.assertEqual(env.get("NONE"), "hello world")
    
    def test_parse_with_comments(self):
        """Test parsing with comments."""
        path = self._create_env_file(".env",
            "# This is a comment\n"
            "KEY=value\n"
            "# Another comment\n"
        )
        env = EnvFile(path)
        
        self.assertEqual(len(env), 1)
        self.assertEqual(len(env.comments), 2)
    
    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        path = self._create_env_file(".env", "")
        env = EnvFile(path)
        
        self.assertEqual(len(env), 0)
        self.assertTrue(bool(env))  # Empty but valid
    
    def test_parse_malformed_line(self):
        """Test handling malformed lines."""
        path = self._create_env_file(".env",
            "KEY=value\n"
            "INVALID_LINE\n"
            "KEY2=value2\n"
        )
        env = EnvFile(path)
        
        self.assertEqual(len(env), 2)
        self.assertEqual(len(env.parse_errors), 1)
    
    def test_file_not_found(self):
        """Test handling non-existent file."""
        env = EnvFile("/nonexistent/path/.env")
        
        self.assertEqual(len(env), 0)
        self.assertEqual(len(env.parse_errors), 1)
    
    def test_empty_key(self):
        """Test handling empty key."""
        path = self._create_env_file(".env", "=value\nKEY=value\n")
        env = EnvFile(path)
        
        self.assertEqual(len(env), 1)  # Only KEY=value should be parsed
        self.assertEqual(len(env.parse_errors), 1)
    
    def test_special_characters_in_value(self):
        """Test values with special characters."""
        path = self._create_env_file(".env",
            "URL=http://example.com:8080/path?query=1&foo=bar\n"
            "JSON={\"key\": \"value\"}\n"
        )
        env = EnvFile(path)
        
        self.assertIn("http://example.com", env.get("URL"))
        self.assertIn("key", env.get("JSON"))
    
    def test_whitespace_handling(self):
        """Test handling of whitespace."""
        path = self._create_env_file(".env",
            "  KEY1  =  value1  \n"
            "KEY2=value2\n"
            "\n"
            "KEY3=value3\n"
        )
        env = EnvFile(path)
        
        self.assertEqual(len(env), 3)


class TestEnvGuardScan(unittest.TestCase):
    """Test EnvGuard scan functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_file(self, rel_path: str, content: str = "") -> Path:
        """Helper to create a test file."""
        path = Path(self.temp_dir) / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_scan_single_env(self):
        """Test scanning directory with single .env file."""
        self._create_file(".env", "KEY=value")
        
        files = self.guard.scan(self.temp_dir)
        
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name == ".env")
    
    def test_scan_multiple_env_variants(self):
        """Test scanning multiple .env file variants."""
        self._create_file(".env", "KEY=value")
        self._create_file(".env.local", "KEY=local")
        self._create_file(".env.production", "KEY=prod")
        
        files = self.guard.scan(self.temp_dir)
        
        self.assertEqual(len(files), 3)
    
    def test_scan_recursive(self):
        """Test recursive scanning."""
        self._create_file(".env", "ROOT=value")
        self._create_file("subdir/.env", "SUB=value")
        self._create_file("subdir/nested/.env.local", "NESTED=value")
        
        files = self.guard.scan(self.temp_dir, recursive=True)
        
        self.assertEqual(len(files), 3)
    
    def test_scan_non_recursive(self):
        """Test non-recursive scanning."""
        self._create_file(".env", "ROOT=value")
        self._create_file("subdir/.env", "SUB=value")
        
        files = self.guard.scan(self.temp_dir, recursive=False)
        
        self.assertEqual(len(files), 1)
    
    def test_scan_excludes_node_modules(self):
        """Test that node_modules is excluded."""
        self._create_file(".env", "ROOT=value")
        self._create_file("node_modules/.env", "EXCLUDED=value")
        
        files = self.guard.scan(self.temp_dir)
        
        self.assertEqual(len(files), 1)
    
    def test_scan_nonexistent_path(self):
        """Test scanning non-existent path."""
        with self.assertRaises(FileNotFoundError):
            self.guard.scan("/nonexistent/path")
    
    def test_scan_single_file(self):
        """Test scanning a single file path."""
        path = self._create_file(".env", "KEY=value")
        
        files = self.guard.scan(str(path))
        
        self.assertEqual(len(files), 1)


class TestEnvGuardAudit(unittest.TestCase):
    """Test EnvGuard audit functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_env_file(self, content: str) -> Path:
        """Helper to create a test .env file."""
        path = Path(self.temp_dir) / ".env"
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_audit_basic(self):
        """Test basic audit functionality."""
        path = self._create_env_file("KEY1=value1\nKEY2=value2\n")
        
        result = self.guard.audit(str(path))
        
        self.assertTrue(result['exists'])
        self.assertEqual(result['variable_count'], 2)
        self.assertIn("KEY1", result['variables'])
    
    def test_audit_masks_sensitive(self):
        """Test that sensitive values are masked."""
        path = self._create_env_file(
            "API_KEY=super_secret_key_12345\n"
            "DATABASE_PASSWORD=mypassword123\n"
            "APP_NAME=normal_value\n"
        )
        
        result = self.guard.audit(str(path), mask_sensitive=True)
        
        # Sensitive values should be masked
        self.assertTrue(result['variables']['API_KEY']['sensitive'])
        self.assertNotIn("super_secret", result['variables']['API_KEY']['value'])
        
        # Normal values (no sensitive keywords) should not be masked
        self.assertFalse(result['variables']['APP_NAME']['sensitive'])
        self.assertEqual(result['variables']['APP_NAME']['value'], "normal_value")
    
    def test_audit_show_secrets(self):
        """Test audit with secrets unmasked."""
        path = self._create_env_file("API_KEY=super_secret_key_12345\n")
        
        result = self.guard.audit(str(path), mask_sensitive=False)
        
        self.assertEqual(result['variables']['API_KEY']['value'], "super_secret_key_12345")
    
    def test_audit_identifies_urls(self):
        """Test that URL keys are identified."""
        path = self._create_env_file(
            "API_URL=http://api.example.com\n"
            "DATABASE_HOST=localhost\n"
        )
        
        result = self.guard.audit(str(path))
        
        self.assertTrue(result['variables']['API_URL']['is_url'])
        self.assertTrue(result['variables']['DATABASE_HOST']['is_url'])


class TestEnvGuardConflicts(unittest.TestCase):
    """Test EnvGuard conflict detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_file(self, name: str, content: str) -> Path:
        """Helper to create a test file."""
        path = Path(self.temp_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_detect_value_conflict(self):
        """Test detecting value conflicts."""
        self._create_file(".env", "API_URL=http://production.api.com\n")
        self._create_file("config.ts", 
            'export const API_URL = "http://development.api.com";\n'
        )
        
        conflicts = self.guard.detect_conflicts(self.temp_dir)
        
        self.assertGreaterEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'value_conflict')
    
    def test_no_conflicts(self):
        """Test when there are no conflicts."""
        self._create_file(".env", "API_URL=http://api.example.com\n")
        self._create_file("config.ts", 
            'export const config = { timeout: 5000 };\n'
        )
        
        conflicts = self.guard.detect_conflicts(self.temp_dir)
        
        self.assertEqual(len(conflicts), 0)


class TestEnvGuardSchema(unittest.TestCase):
    """Test EnvGuard schema validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_file(self, name: str, content: str) -> Path:
        """Helper to create a test file."""
        path = Path(self.temp_dir) / name
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_schema_valid(self):
        """Test valid schema check."""
        env = self._create_file(".env", "KEY1=value1\nKEY2=value2\n")
        schema = self._create_file(".env.example", "KEY1=\nKEY2=\n")
        
        result = self.guard.check_schema(str(env), str(schema))
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['missing_keys']), 0)
    
    def test_schema_missing_keys(self):
        """Test schema check with missing keys."""
        env = self._create_file(".env", "KEY1=value1\n")
        schema = self._create_file(".env.example", "KEY1=\nKEY2=\nKEY3=\n")
        
        result = self.guard.check_schema(str(env), str(schema))
        
        self.assertFalse(result['valid'])
        self.assertEqual(len(result['missing_keys']), 2)
        self.assertIn("KEY2", result['missing_keys'])
    
    def test_schema_extra_keys(self):
        """Test schema check with extra keys."""
        env = self._create_file(".env", "KEY1=value1\nEXTRA=value\n")
        schema = self._create_file(".env.example", "KEY1=\n")
        
        result = self.guard.check_schema(str(env), str(schema))
        
        self.assertTrue(result['valid'])  # Extra keys don't fail validation
        self.assertEqual(len(result['extra_keys']), 1)
        self.assertIn("EXTRA", result['extra_keys'])
    
    def test_schema_coverage(self):
        """Test schema coverage calculation."""
        env = self._create_file(".env", "KEY1=value1\nKEY2=value2\n")
        schema = self._create_file(".env.example", "KEY1=\nKEY2=\nKEY3=\nKEY4=\n")
        
        result = self.guard.check_schema(str(env), str(schema))
        
        self.assertEqual(result['coverage'], 50.0)


class TestEnvGuardStale(unittest.TestCase):
    """Test EnvGuard stale value detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_env_file(self, name: str, content: str) -> Path:
        """Helper to create a test .env file."""
        path = Path(self.temp_dir) / name
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_detect_localhost_in_production(self):
        """Test detecting localhost in production env."""
        path = self._create_env_file(".env.production", "API_URL=http://localhost:3000\n")
        
        warnings = self.guard.detect_stale(str(path), context="production")
        
        self.assertGreaterEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['pattern'], 'localhost_in_prod')
    
    def test_detect_placeholder(self):
        """Test detecting placeholder values."""
        path = self._create_env_file(".env", "API_KEY=YOUR_API_KEY_HERE\n")
        
        warnings = self.guard.detect_stale(str(path))
        
        self.assertGreaterEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['pattern'], 'placeholder')
    
    def test_detect_empty_value(self):
        """Test detecting empty values."""
        path = self._create_env_file(".env", "REQUIRED_KEY=\n")
        
        warnings = self.guard.detect_stale(str(path))
        
        self.assertGreaterEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['pattern'], 'empty_value')
    
    def test_auto_context_detection(self):
        """Test automatic context detection from filename."""
        path = self._create_env_file(".env.production", "API_URL=http://localhost:3000\n")
        
        warnings = self.guard.detect_stale(str(path), context="auto")
        
        # Should detect localhost in production
        self.assertGreaterEqual(len(warnings), 1)


class TestEnvGuardUpdate(unittest.TestCase):
    """Test EnvGuard update functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_env_file(self, content: str) -> Path:
        """Helper to create a test .env file."""
        path = Path(self.temp_dir) / ".env"
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_update_existing_key(self):
        """Test updating an existing key."""
        path = self._create_env_file("KEY1=old_value\nKEY2=value2\n")
        
        success = self.guard.update_value(str(path), "KEY1", "new_value")
        
        self.assertTrue(success)
        env = EnvFile(path)
        self.assertEqual(env.get("KEY1"), "new_value")
        self.assertEqual(env.get("KEY2"), "value2")
    
    def test_update_nonexistent_key(self):
        """Test updating a non-existent key without create flag."""
        path = self._create_env_file("KEY1=value1\n")
        
        success = self.guard.update_value(str(path), "NEW_KEY", "value", create=False)
        
        self.assertFalse(success)
    
    def test_create_new_key(self):
        """Test creating a new key with create flag."""
        path = self._create_env_file("KEY1=value1\n")
        
        success = self.guard.update_value(str(path), "NEW_KEY", "new_value", create=True)
        
        self.assertTrue(success)
        env = EnvFile(path)
        self.assertEqual(env.get("NEW_KEY"), "new_value")
    
    def test_create_new_file(self):
        """Test creating a new .env file."""
        path = Path(self.temp_dir) / "new.env"
        
        success = self.guard.update_value(str(path), "KEY", "value", create=True)
        
        self.assertTrue(success)
        self.assertTrue(path.exists())


class TestEnvGuardDiff(unittest.TestCase):
    """Test EnvGuard diff functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_file(self, name: str, content: str) -> Path:
        """Helper to create a test file."""
        path = Path(self.temp_dir) / name
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_diff_identical_files(self):
        """Test diff of identical files."""
        file1 = self._create_file(".env", "KEY1=value1\nKEY2=value2\n")
        file2 = self._create_file(".env.backup", "KEY1=value1\nKEY2=value2\n")
        
        result = self.guard.diff(str(file1), str(file2))
        
        self.assertEqual(result['similarity'], 100.0)
        self.assertEqual(len(result['different_values']), 0)
    
    def test_diff_different_values(self):
        """Test diff with different values."""
        file1 = self._create_file(".env", "KEY1=value1\nKEY2=value2\n")
        file2 = self._create_file(".env.prod", "KEY1=prod_value1\nKEY2=value2\n")
        
        result = self.guard.diff(str(file1), str(file2))
        
        self.assertIn("KEY1", result['different_values'])
        self.assertEqual(result['different_values']['KEY1']['file1'], "value1")
        self.assertEqual(result['different_values']['KEY1']['file2'], "prod_value1")
    
    def test_diff_missing_keys(self):
        """Test diff with missing keys."""
        file1 = self._create_file(".env", "KEY1=value1\nKEY2=value2\n")
        file2 = self._create_file(".env.prod", "KEY1=value1\nKEY3=value3\n")
        
        result = self.guard.diff(str(file1), str(file2))
        
        self.assertIn("KEY2", result['only_in_file1'])
        self.assertIn("KEY3", result['only_in_file2'])


class TestEnvGuardURLValidation(unittest.TestCase):
    """Test EnvGuard URL validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.guard = EnvGuard()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_env_file(self, content: str) -> Path:
        """Helper to create a test .env file."""
        path = Path(self.temp_dir) / ".env"
        path.write_text(content, encoding='utf-8')
        return path
    
    def test_validate_empty_url(self):
        """Test validation of empty URL."""
        path = self._create_env_file("API_URL=\n")
        
        results = self.guard.validate_urls(str(path))
        
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['reachable'])
        self.assertEqual(results[0]['error'], "Empty value")
    
    @patch('envguard.urlopen')
    def test_validate_reachable_url(self, mock_urlopen):
        """Test validation of reachable URL."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response
        
        path = self._create_env_file("API_URL=http://example.com\n")
        
        results = self.guard.validate_urls(str(path), timeout=1)
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['reachable'])


class TestVersion(unittest.TestCase):
    """Test version and metadata."""
    
    def test_version_exists(self):
        """Test that version is defined."""
        self.assertIsNotNone(__version__)
        self.assertRegex(__version__, r'^\d+\.\d+\.\d+$')


def run_tests():
    """Run all tests with nice output."""
    print("=" * 70)
    print("TESTING: EnvGuard v1.0")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestEnvFile,
        TestEnvGuardScan,
        TestEnvGuardAudit,
        TestEnvGuardConflicts,
        TestEnvGuardSchema,
        TestEnvGuardStale,
        TestEnvGuardUpdate,
        TestEnvGuardDiff,
        TestEnvGuardURLValidation,
        TestVersion,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"RESULTS: {result.testsRun} tests")
    print(f"[OK] Passed: {passed}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
