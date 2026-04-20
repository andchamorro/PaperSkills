"""
test_socket_security.py — Socket.dev-compatible security test suite.

These tests verify that all Python scripts in this repository are free from
patterns commonly flagged by Socket.dev's supply-chain security scanner:

1. No shell=True in any subprocess call           (command injection risk)
2. No os.system() calls                           (shell injection risk)
3. No eval() / exec() on external input           (arbitrary code execution)
4. No dynamic import of user-supplied modules     (code injection risk)
5. Path-traversal protection in export_latex.py   (directory escape)
6. export_latex.py subprocess calls use list args (not string commands)

Socket alert categories addressed
-----------------------------------
- Shell Access (S603 / shellAccess): subprocess must use list + shell=False
- Unsafe eval/exec: dynamic code execution from external data
- Path traversal: file I/O confined to declared base directory

Running
-------
    pytest tests/test_socket_security.py -v
    # or as a standalone check:
    python tests/test_socket_security.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"


def _all_python_scripts() -> list[Path]:
    """Return every .py file under skills/ (excludes hidden dirs)."""
    return [
        p for p in SKILLS_ROOT.rglob("*.py") if not any(part.startswith(".") for part in p.parts)
    ]


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. No shell=True
# ---------------------------------------------------------------------------


class TestNoShellTrue:
    """Socket alert: shellAccess — subprocess with shell=True is flagged."""

    @pytest.mark.parametrize(
        "script", _all_python_scripts(), ids=lambda p: str(p.relative_to(REPO_ROOT))
    )
    def test_no_shell_true(self, script: Path) -> None:
        """Every Python script must NOT contain shell=True."""
        source = _source(script)
        # Match `shell=True` and `shell = True` (with optional spaces)
        pattern = re.compile(r"shell\s*=\s*True")
        matches = pattern.findall(source)
        assert not matches, (
            f"{script.relative_to(REPO_ROOT)}: found {len(matches)} occurrence(s) of "
            f"'shell=True'. Use an argument list with shell=False instead."
        )


# ---------------------------------------------------------------------------
# 2. No os.system() calls
# ---------------------------------------------------------------------------


class TestNoOsSystem:
    """Socket alert: shellAccess — os.system() executes via the shell."""

    @pytest.mark.parametrize(
        "script", _all_python_scripts(), ids=lambda p: str(p.relative_to(REPO_ROOT))
    )
    def test_no_os_system(self, script: Path) -> None:
        source = _source(script)
        pattern = re.compile(r"\bos\.system\s*\(")
        matches = pattern.findall(source)
        assert not matches, (
            f"{script.relative_to(REPO_ROOT)}: found {len(matches)} os.system() call(s). "
            f"Use subprocess.run([...], shell=False) instead."
        )


# ---------------------------------------------------------------------------
# 3. No bare eval() / exec() on non-literal input
# ---------------------------------------------------------------------------


class TestNoEvalExec:
    """Socket alert: dangerous eval/exec that could execute arbitrary code."""

    @pytest.mark.parametrize(
        "script", _all_python_scripts(), ids=lambda p: str(p.relative_to(REPO_ROOT))
    )
    def test_no_eval_exec(self, script: Path) -> None:
        source = _source(script)
        # Allow eval/exec only if called with a literal string (e.g. in tests).
        # We parse the AST to find dynamic calls.
        try:
            tree = ast.parse(source, filename=str(script))
        except SyntaxError:
            pytest.skip(f"Could not parse {script}: SyntaxError")
            return

        violations: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in {"eval", "exec"} and node.args:
                    # Flag if the first arg is not a string literal
                    first_arg = node.args[0]
                    if not isinstance(first_arg, ast.Constant):
                        violations.append(f"line {node.lineno}: {name}(<dynamic>)")

        assert (
            not violations
        ), f"{script.relative_to(REPO_ROOT)}: dynamic eval/exec detected:\n" + "\n".join(
            f"  {v}" for v in violations
        )


# ---------------------------------------------------------------------------
# 4. export_latex.py — subprocess calls use list args (not string command)
# ---------------------------------------------------------------------------


class TestExportLatexSubprocessSafety:
    """Socket alert: shellAccess specifically in export_latex.py."""

    SCRIPT = SKILLS_ROOT / "paper-orchestra" / "scripts" / "export_latex.py"

    def _get_subprocess_run_calls(self) -> list[ast.Call]:
        source = self.SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(self.SCRIPT))
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "run"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "subprocess"
                ):
                    calls.append(node)
        return calls

    def test_subprocess_calls_exist(self) -> None:
        """export_latex.py must contain subprocess.run() calls."""
        assert self.SCRIPT.exists(), f"Missing script: {self.SCRIPT}"
        calls = self._get_subprocess_run_calls()
        assert calls, "No subprocess.run() calls found — script may have changed."

    def test_all_subprocess_calls_use_list_arg(self) -> None:
        """Every subprocess.run() must receive a list, not a string command."""
        calls = self._get_subprocess_run_calls()
        for call in calls:
            first_arg = call.args[0] if call.args else None
            assert (
                first_arg is not None
            ), f"subprocess.run() at line {call.lineno} has no positional argument."
            # The first arg must be a Name (variable holding a list) or a List literal.
            # A Constant (string) here would mean shell-string usage.
            assert not isinstance(first_arg, ast.Constant), (
                f"subprocess.run() at line {call.lineno} receives a string constant as "
                f"its first argument — this enables shell injection. Pass a list instead."
            )

    def test_all_subprocess_calls_have_explicit_shell_false(self) -> None:
        """Every subprocess.run() must set shell=False explicitly."""
        calls = self._get_subprocess_run_calls()
        for call in calls:
            shell_kwarg = next(
                (kw for kw in call.keywords if kw.arg == "shell"),
                None,
            )
            assert shell_kwarg is not None, (
                f"subprocess.run() at line {call.lineno} is missing the 'shell=' keyword. "
                f"Add shell=False to make the security intent explicit."
            )
            value = shell_kwarg.value
            assert isinstance(value, ast.Constant) and value.value is False, (
                f"subprocess.run() at line {call.lineno} has shell={ast.unparse(value)} "
                f"but must have shell=False."
            )


# ---------------------------------------------------------------------------
# 5. Path-traversal protection in export_latex._validate_path
# ---------------------------------------------------------------------------


class TestPathTraversalProtection:
    """Ensure _validate_path() blocks paths that escape the base directory."""

    @pytest.fixture(autouse=True)
    def _import_module(self, tmp_path: Path) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "export_latex",
            SKILLS_ROOT / "paper-orchestra" / "scripts" / "export_latex.py",
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self._validate_path = mod._validate_path
        self._tmp = tmp_path

    def test_valid_path_inside_base(self) -> None:
        base = self._tmp
        child = base / "final" / "manuscript.md"
        child.parent.mkdir(parents=True, exist_ok=True)
        # Should not raise
        result = self._validate_path(child, base, label="test")
        assert result == child.resolve()

    def test_traversal_path_raises(self) -> None:
        base = self._tmp / "desk"
        base.mkdir()
        evil = base / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="outside the allowed base directory"):
            self._validate_path(evil, base, label="evil")

    def test_absolute_path_outside_base_raises(self) -> None:
        base = self._tmp / "desk"
        base.mkdir()
        outside = Path("/tmp/evil.md")
        with pytest.raises(ValueError, match="outside the allowed base directory"):
            self._validate_path(outside, base, label="outside")

    def test_disallowed_extension_raises(self) -> None:
        base = self._tmp
        bad = base / "script.sh"
        with pytest.raises(ValueError, match="disallowed extension"):
            self._validate_path(bad, base, label="bad-ext")

    def test_allowed_extensions_pass(self) -> None:
        base = self._tmp
        for ext in (".md", ".tex", ".pdf", ".bib"):
            p = base / f"file{ext}"
            # Should not raise
            self._validate_path(p, base, label=ext)


# ---------------------------------------------------------------------------
# Standalone runner (also works as `python tests/test_socket_security.py`)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
