# PEP 8 Style Analyzer and Auto-corrector

This tool analyzes Python code for PEP 8 style guideline violations and can automatically fix common issues. It helps maintain consistent code style across Python projects.

## Features

The analyzer checks for:
1. Line length (max 100 characters)
2. Indentation (4 spaces)
3. Whitespace around operators
4. Import statement ordering
5. Naming conventions
   - Classes (CapWords)
   - Functions and variables (lowercase_with_underscores)
6. Trailing whitespace

## Installation (assuming you have python installed)

```bash
git clone <repository-url>
cd code-styler
pip install -r req.txt
```

## Usage

To analyze a file:
```bash
python style_analyzer.py path/to/your/file.py
```

To analyze and auto-correct issues:
```bash
python style_analyzer.py path/to/your/file.py --auto
```

## Sample Output

```
PEP 8 Style Analysis Report
========================================
File: temp.py
Line 6
Code: W291
Issue: Trailing whitespace
----------------------------------------
File: temp.py
Line 96
Code: N802
Issue: Function name "Ingredients_analysis" should be lowercase
----------------------------------------
```

## Auto-correction Capabilities

The tool can automatically fix:
- Indentation issues
- Whitespace around operators
- Import statement ordering
- Trailing whitespace

Some issues (like line length) require manual intervention and are only reported.

## Running Tests

```bash
pytest test_style_analyzer.py
```

## Dependencies

- Python 3.7+
- ast (standard library)
- re (standard library)
- pytest (for unit tests)

## Future Improvements

1. Additional Checks:
   - Docstring formatting
   - Maximum blank lines

2. Enhanced Auto-correction:
   - Smart line wrapping for long lines
   - Docstring formatting
   - Section-wise import organization

3. Configuration:
   - Custom line length limits
   - Multiple naming conventions (like camel style etc.)

4. Integration:
   - Git pre-commit hooks for forced integration
   - Batch processing for multiple files
   - [x] CI/CD github action checks for pytest

