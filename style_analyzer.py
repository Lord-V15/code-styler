'''
Code for a style analyzer based on PEP 8 style guideline. Inspired from how black works.
main(): Runs the script for a given file passed in system args
analyze(): Runs the '_check' fucnctions for finding PEP 8 style guideline violations
generate_report(issues): Generates all the stdout for style issues detected
_apply_corrections(): Applies all corrections to the file (for --auto flag)
Note: This file has been formatted using black.
'''
import ast
import re
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
import sys


@dataclass
class StyleIssue:
    """Represents a detected style violation (for managing issues list)."""

    filename: str
    line_number: int
    column: int
    code: str  # Issue code (e.g., E201 for whitespace)
    description: str
    fix: Optional[str] = None  # The corrected line if available


class PEP8Analyzer:
    """Analyzes Python code for PEP 8 style violations."""

    def __init__(self, filename: str, auto_correct: bool = False):
        self.filename = filename
        self.auto_correct = auto_correct
        self.issues: List[StyleIssue] = []
        self.corrected_lines: Dict[int, str] = {}

    # The following list is taken from ideas online. It can be extended with new rules as needed.
    def analyze(self, filename: Optional[str] = None) -> List[StyleIssue]: # with optional filename path
        """Analyze the file for style violations."""
        with open(self.filename, "r") as f:
            content = f.read()

        # Store original lines for comparison and correction
        self.original_lines = content.splitlines()

        self._check_line_length()
        self._check_indentation()
        self._check_whitespace()
        self._check_imports()
        self._check_naming_conventions()

        return self.issues

    def _check_line_length(self):
        """Check for lines exceeding 100 characters."""
        for i, line in enumerate(self.original_lines, 1):
            if len(line.rstrip()) > 100:
                # Don't try to auto-correct long lines
                self.issues.append(
                    StyleIssue(
                        self.filename,
                        i,
                        100,
                        "E501",
                        "Line too long (exceeds 100 characters)",
                    )
                )

    def _check_indentation(self):
        """Check for consistent indentation (4 spaces)."""
        for i, line in enumerate(self.original_lines, 1):
            if line.strip():  # Skip empty lines
                spaces = len(line) - len(line.lstrip())
                if spaces % 4 != 0:
                    correct_spaces = (spaces // 4) * 4
                    corrected = " " * correct_spaces + line.lstrip()
                    self.issues.append(
                        StyleIssue(
                            self.filename,
                            i,
                            0,
                            "E111",
                            "Indentation is not a multiple of 4",
                            corrected,
                        )
                    )
                    if self.auto_correct:
                        self.corrected_lines[i] = corrected

    def _check_whitespace(self):
        """
        Check for whitespace issues.
        -> test = '(a,b+1) *(2+ 3)'
        -> re.sub(f"({operator_pattern})", r" \1 ", test)
        -> '(a,b + 1)  * (2 + 3)'
        """
        for i, line in enumerate(self.original_lines, 1):
            # Check spaces around operators
            operator_pattern = r"([+\-*/=<>!]=?|[+\-*/])"
            matches = re.finditer(operator_pattern, line)
            for match in matches:
                if not (
                    match.start() > 0
                    and match.end() < len(line)
                    and line[match.start() - 1].isspace()
                    and line[match.end()].isspace()
                ):
                    corrected = re.sub(f"({operator_pattern})", r" \1 ", line)
                    self.issues.append(
                        StyleIssue(
                            self.filename,
                            i,
                            match.start(),
                            "E225",
                            "Missing whitespace around operator",
                            corrected,
                        )
                    )
                    if self.auto_correct:
                        self.corrected_lines[i] = corrected

            # Check trailing whitespace
            if line.rstrip() != line:
                corrected = line.rstrip()
                self.issues.append(
                    StyleIssue(
                        self.filename,
                        i,
                        len(line.rstrip()),
                        "W291",
                        "Trailing whitespace",
                        corrected,
                    )
                )
                if self.auto_correct:
                    self.corrected_lines[i] = corrected

    def _check_imports(self):
        """Check import statement formatting and ordering."""
        import_lines = []
        for i, line in enumerate(self.original_lines, 1):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                import_lines.append((i, line.strip()))

        # Check import ordering using first word after 'import'
        sorted_imports = sorted(import_lines, key=lambda x: x[1])

        for (orig_idx, orig_imp), (sort_idx, sort_imp) in zip(
            import_lines, sorted_imports
        ):
            if orig_imp != sort_imp:
                self.issues.append(
                    StyleIssue(
                        self.filename,
                        orig_idx,
                        0,
                        "I100",
                        "Import statements are not in alphabetical order",
                        sort_imp,
                    )
                )
                if self.auto_correct:
                    self.corrected_lines[orig_idx] = sort_imp

    def _check_naming_conventions(self):
        """Check naming conventions for variables, functions, and classes."""
        tree = ast.parse("".join(self.original_lines))

        class NamingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.issues = []

            def visit_ClassDef(self, node):
                if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                    self.issues.append(
                        StyleIssue(
                            self.filename,
                            node.lineno,
                            node.col_offset,
                            "N801",
                            f'Class name "{node.name}" should use CapWords convention',
                        )
                    )
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                    self.issues.append(
                        StyleIssue(
                            self.filename,
                            node.lineno,
                            node.col_offset,
                            "N802",
                            f'Function name "{node.name}" should be lowercase',
                        )
                    )
                self.generic_visit(node)

        visitor = NamingVisitor()
        visitor.visit(tree)
        self.issues.extend(visitor.issues)

    def _apply_corrections(self):
        """Apply all accumulated corrections to the file."""
        if not self.corrected_lines:
            print("\033[96m🤌 Nothing to auto-correct. Code is clean.")
            return

        corrected_content = []
        for i, line in enumerate(self.original_lines, 1):
            corrected_content.append(self.corrected_lines.get(i, line))

        with open(self.filename, "w") as f:
            f.write("\n".join(corrected_content)) 
        # auto fixes in green
        print("\033[92m🧼Auto-corrections applied to the file successfully🧼")


def generate_report(issues: List[StyleIssue]) -> str:
    """Generate a formatted report of style issues."""
    if not issues:
        return "\033[92m✨No style issues detected✨"

    report = ["\033[1m \033[95m\nPEP 8 Style Analysis Report", "=" * 40]  # line-by-line print

    for issue in issues:
        report.extend(
            [
                "\033[93m" + f"\nFile: {issue.filename}",
                "\033[93m" + f"Line {issue.line_number}, Column {issue.column}",
                "\033[93m" + f"Code: {issue.code}",
                "\033[93m" + f"Issue: {issue.description}",
                "-" * 40,
            ]
        )  # issues are warnings in yellow

    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print("Usage: python style_analyzer.py <filename> [--auto-correct]")
        sys.exit(1)

    filename = sys.argv[1]
    auto_correct = True if "--auto" in sys.argv else False

    try:
        analyzer = PEP8Analyzer(filename, auto_correct)
        issues = analyzer.analyze()
        print(generate_report(issues))

        if auto_correct:
            analyzer._apply_corrections()

    except Exception as e:
        print("\033[91m" + f"Error analyzing file: {e}")  # error in red
        sys.exit(1)


if __name__ == "__main__":
    main()
