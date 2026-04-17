"""
Bug condition exploration / fix verification tests for BSL Language Server 0.29.0 compatibility.

These tests encode the EXPECTED CORRECT behavior for BSL LS 0.29.0 CLI syntax.
On unfixed code they FAIL (confirming the bug exists).
On fixed code they PASS (confirming the bug is resolved).

Bug summary (all fixed):
- _build_analyze_command now uses positional 'analyze' subcommand (was '--analyze')
- _build_analyze_command now uses '-s' (was '--srcDir') and '-r' (was '--reporter')
- _build_analyze_command now includes '-o <output_dir>' flag
- _build_format_command now uses positional 'format' subcommand (was '--format')
- _build_format_command now uses '-s' (was '--src')
- analyze() method now uses _is_noise_line() for stderr filtering (filters 'WARNING:')
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.mcp_bsl.bsl_runner import BSLRunner, _is_noise_line
from src.mcp_bsl.config import BSLConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JAR_PATH = r'D:\NewMCP\bsl_mcp\bsl-language-server-0.29.0-exec.jar'
CONFIG_FILE = Path(r'D:\NewMCP\bsl_mcp\.bsl-language-server.json')
SOURCE_PATH = Path(r'D:\NewMCP\bsl_mcp\ЗаказКлиента')


@pytest.fixture(scope="module")
def runner():
    """Create a BSLRunner instance with the real JAR path."""
    config = BSLConfig(jar_path=JAR_PATH)
    return BSLRunner(config)


# ---------------------------------------------------------------------------
# Bug condition / fix verification tests
# (FAIL on unfixed code, PASS on fixed code)
# ---------------------------------------------------------------------------

def test_bug_condition_analyze_uses_positional_analyze_subcommand(runner):
    """
    Fix verification: _build_analyze_command uses positional 'analyze' subcommand
    without '--' prefix, as required by BSL LS 0.29.0.

    Expected correct behavior: 'analyze' in cmd AND '--analyze' not in cmd.
    Validates: Requirements 1.1, 2.1
    """
    cmd, output_dir = runner._build_analyze_command(SOURCE_PATH, CONFIG_FILE, 512)

    assert 'analyze' in cmd, (
        "Expected positional 'analyze' subcommand in command"
    )
    assert '--analyze' not in cmd, (
        "Old '--analyze' flag must not be present in fixed command"
    )


def test_bug_condition_analyze_uses_short_flags(runner):
    """
    Fix verification: _build_analyze_command uses '-s' and '-r' short flags
    as required by BSL LS 0.29.0.

    Expected correct behavior: '-s' in cmd AND '--srcDir' not in cmd.
    Validates: Requirements 1.2, 2.2
    """
    cmd, output_dir = runner._build_analyze_command(SOURCE_PATH, CONFIG_FILE, 512)

    assert '-s' in cmd, (
        "Expected '-s' short flag for source directory"
    )
    assert '--srcDir' not in cmd, (
        "Old '--srcDir' flag must not be present in fixed command"
    )
    assert '-r' in cmd, (
        "Expected '-r' short flag for reporter"
    )
    assert '--reporter' not in cmd, (
        "Old '--reporter' flag must not be present in fixed command"
    )


def test_bug_condition_analyze_includes_output_dir_flag(runner):
    """
    Fix verification: _build_analyze_command includes '-o <output_dir>' flag
    so BSL LS 0.29.0 knows where to write bsl-json.json.

    Expected correct behavior: '-o' in cmd AND output_dir is a valid path.
    Validates: Requirements 1.3, 2.3
    """
    cmd, output_dir = runner._build_analyze_command(SOURCE_PATH, CONFIG_FILE, 512)

    assert '-o' in cmd, (
        "Expected '-o' output directory flag in fixed analyze command"
    )
    # The value after '-o' should be the output_dir
    o_index = cmd.index('-o')
    assert cmd[o_index + 1] == output_dir, (
        "The value after '-o' must be the output_dir returned by the method"
    )
    # Config flag must appear BEFORE the 'analyze' subcommand
    assert '-c' in cmd, "Expected '-c' config flag in command"
    c_index = cmd.index('-c')
    analyze_index = cmd.index('analyze')
    assert c_index < analyze_index, (
        "Global '-c' flag must appear BEFORE the 'analyze' subcommand"
    )


def test_bug_condition_format_uses_positional_format_subcommand(runner):
    """
    Fix verification: _build_format_command uses positional 'format' subcommand
    without '--' prefix, as required by BSL LS 0.29.0.

    Expected correct behavior: 'format' in cmd AND '--format' not in cmd.
    Validates: Requirements 1.4, 2.4
    """
    cmd = runner._build_format_command(SOURCE_PATH)

    assert 'format' in cmd, (
        "Expected positional 'format' subcommand in command"
    )
    assert '--format' not in cmd, (
        "Old '--format' flag must not be present in fixed command"
    )
    assert '-s' in cmd, (
        "Expected '-s' short flag for source path"
    )
    assert '--src' not in cmd, (
        "Old '--src' flag must not be present in fixed command"
    )


def test_bug_condition_warning_filtered_by_is_noise_line():
    """
    Fix verification: WARNING: lines from JVM 0.29.0 are now filtered by
    _is_noise_line(), which is used in the fixed analyze() method.

    Expected correct behavior: _is_noise_line('WARNING: ...') returns True.
    Validates: Requirements 1.5, 2.5
    """
    warning_line = 'WARNING: A terminally deprecated method in java.lang.System has been called'

    assert _is_noise_line(warning_line) is True, (
        "Expected _is_noise_line to return True for WARNING: lines "
        "(they are JVM noise, not real errors)"
    )


# --- Preservation tests ---

import json

from hypothesis import given, settings
from hypothesis import strategies as st

from src.mcp_bsl.bsl_runner import (
    BSLDiagnostic,
    _IGNORE_PREFIXES,
)


# ---------------------------------------------------------------------------
# Helpers / strategies
# ---------------------------------------------------------------------------

# Strategy for severity values accepted by _parse_analyze_output
_SEVERITY_VALUES = st.sampled_from(['Error', 'Warning', 'Information', 'Hint'])

# Expected mapping from BSL severity strings to internal severity strings
_SEVERITY_MAP = {
    'Error': 'error',
    'Warning': 'warning',
    'Information': 'info',
    'Hint': 'info',
}

# Strategy for a single diagnostic dict in BSL JSON reporter format
_diagnostic_strategy = st.fixed_dictionaries({
    'range': st.fixed_dictionaries({
        'start': st.fixed_dictionaries({
            'line': st.integers(min_value=0, max_value=10_000),
            'character': st.integers(min_value=0, max_value=10_000),
        })
    }),
    'severity': _SEVERITY_VALUES,
    'message': st.text(min_size=0, max_size=200),
    'code': st.text(min_size=0, max_size=50),
})

# Strategy for a single file-info entry in the BSL JSON report
_file_info_strategy = st.fixed_dictionaries({
    'path': st.from_regex(r'[A-Za-z0-9_/\\\.]+', fullmatch=True),
    'diagnostics': st.lists(_diagnostic_strategy, min_size=0, max_size=10),
})

# Strategy for the full JSON report (list of file-info entries)
_json_report_strategy = st.lists(_file_info_strategy, min_size=0, max_size=5)


# ---------------------------------------------------------------------------
# Observation 1 — _parse_analyze_output with valid JSON
# ---------------------------------------------------------------------------

@given(report=_json_report_strategy)
@settings(max_examples=100)
def test_preservation_parse_analyze_output_returns_bsl_diagnostics(runner, report):
    """
    Preservation: _parse_analyze_output with valid JSON always returns a list of
    BSLDiagnostic objects with correctly mapped fields.

    Validates: Requirements 3.1
    """
    json_payload = json.dumps(report)
    result = runner._parse_analyze_output(json_payload, "")

    # Result must be a list
    assert isinstance(result, list), "Result must be a list"

    # Collect expected diagnostics from the report for comparison
    expected = []
    for file_info in report:
        file_path = file_info['path']
        for diag in file_info['diagnostics']:
            start = diag['range']['start']
            expected.append({
                'file': file_path,
                'line': start['line'] + 1,
                'column': start['character'] + 1,
                'severity': _SEVERITY_MAP[diag['severity']],
                'message': diag['message'],
                'code': diag['code'],
            })

    assert len(result) == len(expected), (
        f"Expected {len(expected)} diagnostics, got {len(result)}"
    )

    for i, (actual, exp) in enumerate(zip(result, expected)):
        assert isinstance(actual, BSLDiagnostic), (
            f"Item {i} must be a BSLDiagnostic, got {type(actual)}"
        )
        assert actual.file == exp['file'], (
            f"Diagnostic {i}: file mismatch: {actual.file!r} != {exp['file']!r}"
        )
        assert actual.line == exp['line'], (
            f"Diagnostic {i}: line must be range.start.line + 1 "
            f"(got {actual.line}, expected {exp['line']})"
        )
        assert actual.column == exp['column'], (
            f"Diagnostic {i}: column must be range.start.character + 1 "
            f"(got {actual.column}, expected {exp['column']})"
        )
        assert actual.severity == exp['severity'], (
            f"Diagnostic {i}: severity mismatch: {actual.severity!r} != {exp['severity']!r}"
        )
        assert actual.message == exp['message'], (
            f"Diagnostic {i}: message mismatch"
        )
        assert actual.code == exp['code'], (
            f"Diagnostic {i}: code mismatch"
        )


# ---------------------------------------------------------------------------
# Observation 2 — _is_noise_line filters noise prefixes
# ---------------------------------------------------------------------------

@given(suffix=st.text(min_size=0, max_size=100))
@settings(max_examples=200)
def test_preservation_is_noise_line_filters_all_ignore_prefixes(suffix):
    """
    Preservation: _is_noise_line returns True for any string that starts with
    a prefix from _IGNORE_PREFIXES, regardless of what follows.

    Validates: Requirements 3.4, 2.5
    """
    for prefix in _IGNORE_PREFIXES:
        line = prefix + suffix
        assert _is_noise_line(line) is True, (
            f"_is_noise_line({line!r}) should return True "
            f"(starts with prefix {prefix!r})"
        )


def test_preservation_is_noise_line_empty_string_returns_true():
    """
    Preservation: _is_noise_line returns True for empty strings and
    whitespace-only strings.

    Validates: Requirements 3.4
    """
    assert _is_noise_line('') is True
    assert _is_noise_line('   ') is True
    assert _is_noise_line('\t\n') is True


@pytest.mark.parametrize("noise_line", [
    'Analyzing files 10/100',
    'Analyzing files...',
    'Analyzing files 0/0',
    'OpenJDK 64-Bit Server VM warning: Using deprecated option',
    'Java HotSpot(TM) 64-Bit Server VM warning',
    'WARNING: A terminally deprecated method in java.lang.System has been called',
    'WARNING: Use --enable-native-access=ALL-UNNAMED to avoid a warning for module jdk.incubator.vector',
    'WARNING: ',
    '',
])
def test_preservation_is_noise_line_known_noise_lines(noise_line):
    """
    Preservation: _is_noise_line returns True for specific known noise lines
    produced by BSL Language Server and JVM.

    Validates: Requirements 3.4, 2.5
    """
    assert _is_noise_line(noise_line) is True, (
        f"_is_noise_line({noise_line!r}) should return True"
    )


# ---------------------------------------------------------------------------
# Observation 3 — _get_safe_environment redirects Windows paths
# ---------------------------------------------------------------------------

def test_preservation_get_safe_environment_all_six_keys_present(runner):
    """
    Preservation: _get_safe_environment returns a dict containing all six
    Windows path variables, each set to tempfile.gettempdir().

    Validates: Requirements 3.9
    """
    env = runner._get_safe_environment()
    expected_temp = tempfile.gettempdir()

    required_keys = ['APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP', 'USERPROFILE', 'HOME']
    for key in required_keys:
        assert key in env, f"Key {key!r} must be present in safe environment"
        assert env[key] == expected_temp, (
            f"env[{key!r}] must equal tempfile.gettempdir() ({expected_temp!r}), "
            f"got {env[key]!r}"
        )


# ---------------------------------------------------------------------------
# Observation 4 — _count_processed_files counts .bsl and .os files
# ---------------------------------------------------------------------------

def test_preservation_count_processed_files_directory(runner):
    """
    Preservation: _count_processed_files returns > 0 for the ЗаказКлиента
    directory which contains multiple .bsl files.

    Validates: Requirements 3.1, 3.7
    """
    source_dir = Path(r'D:\NewMCP\bsl_mcp\ЗаказКлиента')
    count = runner._count_processed_files(source_dir)
    assert count > 0, (
        f"Expected at least one .bsl/.os file in {source_dir}, got {count}"
    )


def test_preservation_count_processed_files_single_bsl_file(runner):
    """
    Preservation: _count_processed_files returns exactly 1 for a single .bsl file path.

    Validates: Requirements 3.1, 3.7
    """
    single_file = Path(r'D:\NewMCP\bsl_mcp\ЗаказКлиента\Ext\ObjectModule.bsl')
    count = runner._count_processed_files(single_file)
    assert count == 1, (
        f"Expected count == 1 for single file {single_file}, got {count}"
    )


# ---------------------------------------------------------------------------
# Integration tests — real JAR 0.29.0
# ---------------------------------------------------------------------------

REAL_JAR_PATH = r'D:\NewMCP\bsl_mcp\bsl-language-server-0.29.0-exec.jar'
REAL_CONFIG_PATH = r'D:\NewMCP\bsl_mcp\.bsl-language-server.json'
REAL_SOURCE_DIR = r'D:\NewMCP\bsl_mcp\ЗаказКлиента'
REAL_BSL_FILE = r'D:\NewMCP\bsl_mcp\ЗаказКлиента\Ext\ObjectModule.bsl'


@pytest.fixture(scope="module")
def real_runner():
    """Create a BSLRunner instance with the real JAR 0.29.0 path."""
    config = BSLConfig(jar_path=REAL_JAR_PATH)
    return BSLRunner(config)


@pytest.mark.integration
def test_integration_analyze_directory(real_runner):
    """
    Integration: bsl_analyze on ЗаказКлиента directory using real JAR 0.29.0.

    Asserts:
    - result.success == True
    - result.files_processed > 0

    Cleanup is verified implicitly: the temp output directory is removed by
    analyze() after reading bsl-json.json (shutil.rmtree). No bsl_report_*
    directories should remain in tempfile.gettempdir() after this call.

    Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.2, 3.3
    """
    # Snapshot temp dirs before analysis to verify cleanup
    temp_root = tempfile.gettempdir()
    before = set(
        d for d in os.listdir(temp_root)
        if d.startswith('bsl_report_')
    )

    result = real_runner.analyze(REAL_SOURCE_DIR, config_path=REAL_CONFIG_PATH)

    assert result.success is True, (
        f"Expected success=True but got success=False. Error: {result.error!r}"
    )
    assert result.files_processed > 0, (
        f"Expected files_processed > 0, got {result.files_processed}"
    )

    # Verify cleanup: no new bsl_report_* directories left behind
    after = set(
        d for d in os.listdir(temp_root)
        if d.startswith('bsl_report_')
    )
    leftover = after - before
    assert not leftover, (
        f"Temp output directories were not cleaned up after analyze: {leftover}"
    )


@pytest.mark.integration
def test_integration_format_single_file(real_runner):
    """
    Integration: bsl_format on a single BSL file using real JAR 0.29.0.

    Asserts:
    - result.success == True

    Validates: Requirements 2.4, 3.7
    """
    result = real_runner.format(REAL_BSL_FILE)

    assert result.success is True, (
        f"Expected success=True but got success=False. Error: {result.error!r}"
    )


@pytest.mark.integration
def test_integration_analyze_temp_dir_cleaned_up(real_runner):
    """
    Integration: verify the temporary output directory is deleted after analyze.

    Strategy: capture the output_dir by calling _build_analyze_command first
    (which creates the temp dir), then run analyze and check the dir is gone.

    Note: _build_analyze_command creates a NEW temp dir each call, so we
    snapshot all bsl_report_* dirs before and after analyze() to detect leaks.

    Validates: Requirements 2.3, 3.3
    """
    temp_root = tempfile.gettempdir()

    # Record existing bsl_report_* dirs before the call
    before = set(
        os.path.join(temp_root, d)
        for d in os.listdir(temp_root)
        if d.startswith('bsl_report_')
    )

    result = real_runner.analyze(REAL_SOURCE_DIR, config_path=REAL_CONFIG_PATH)

    # Collect bsl_report_* dirs after the call
    after = set(
        os.path.join(temp_root, d)
        for d in os.listdir(temp_root)
        if d.startswith('bsl_report_')
    )

    # Any dirs created during this test run must have been cleaned up
    new_dirs = after - before
    assert not new_dirs, (
        f"Temporary output directories were not deleted after analyze: {new_dirs}"
    )

    # Also confirm the analysis itself succeeded
    assert result.success is True, (
        f"analyze() returned success=False. Error: {result.error!r}"
    )
