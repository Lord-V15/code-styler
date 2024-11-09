import pytest
from style_analyzer import PEP8Analyzer, StyleIssue, generate_report
import tempfile
import os

@pytest.fixture
def temp_python_file():
    """Fixture to create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        yield f.name
    os.unlink(f.name)

def write_content(filename, content):
    """Helper function to write content to a file."""
    with open(filename, 'w') as f:
        f.write(content)

def test_line_length_check(temp_python_file):
    """Test detection of lines exceeding 100 characters."""
    content = 'x = ' + 'a' * 98 + '\n'  # 101 characters
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    assert len(issues) == 1
    assert issues[0].code == 'E501'
    assert 'Line too long' in issues[0].description

def test_indentation_check(temp_python_file):
    """Test detection of incorrect indentation."""
    content = '''
def foo():
   x = 1  # 3 spaces instead of 4
    y = 2  # correct indentation
'''
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    assert len(issues) == 1
    assert issues[0].code == 'E111'
    assert 'Indentation' in issues[0].description

def test_whitespace_check(temp_python_file):
    """Test detection of incorrect whitespace around operators."""
    content = '''
x= 1 + 2 # incorrect around equals
y = 3 + 4 # correct
z = 5+6 # incorrect around plus
'''
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    # Should find whitespace issues in lines 1 and 3
    whitespace_issues = [issue for issue in issues if issue.code == 'E225']
    assert len(whitespace_issues) == 2

def test_trailing_whitespace(temp_python_file):
    """Test detection of trailing whitespace."""
    content = 'x = 1    \ny = 2\n'  # trailing whitespace on first line
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    trailing_space_issues = [issue for issue in issues if issue.code == 'W291']
    assert len(trailing_space_issues) == 1

def test_import_ordering(temp_python_file):
    """Test detection of incorrectly ordered imports."""
    content = '''
import sys # wrong alphabetic order
import ast # correct
from typing import List # wrong call order (should be top)
'''
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    import_issues = [issue for issue in issues if issue.code == 'I100']
    assert len(import_issues) == 2

def test_naming_conventions(temp_python_file):
    """Test detection of incorrect naming conventions."""
    content = '''
class testClass:  # should be TestClass
    pass

def TestFunction():  # should be test_function
    pass
'''
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    naming_issues = [issue for issue in issues if issue.code.startswith('N8')]
    assert len(naming_issues) == 2

def test_auto_correct_mode(temp_python_file):
    """Test auto-correction functionality."""
    content = '''
x=1+2
   y = 3  # incorrect indentation
'''
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file, auto_correct=True)
    analyzer.analyze()
    analyzer._apply_corrections()
    
    with open(temp_python_file, 'r') as f:
        corrected_content = f.read()
    
    assert '=' in corrected_content and '+' in corrected_content
    assert 'x = 1 + 2' in corrected_content.splitlines()

def test_clean_code(temp_python_file):
    """Test analysis of code with no style issues."""
    content = '''
def test_function():
    x = 1 + 2
    return x
'''
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    assert len(issues) == 0

def test_multiple_issues_same_line(temp_python_file):
    """Test detection of multiple issues in the same line."""
    content = 'def BAD_name():    \n'  # Has naming issue and trailing whitespace
    write_content(temp_python_file, content)
    
    analyzer = PEP8Analyzer(temp_python_file)
    issues = analyzer.analyze()
    
    assert len(issues) == 2
    issue_codes = {issue.code for issue in issues}
    assert 'N802' in issue_codes  # naming convention
    assert 'W291' in issue_codes  # trailing whitespace

def test_generate_report():
    """Test report generation functionality."""
    issues = [
        StyleIssue(
            filename="test.py",
            line_number=1,
            code="E225",
            description="Missing whitespace around operator"
        )
    ]
    
    report = generate_report(issues)
    assert "test.py" in report
    assert "Line 1" in report
    assert "E225" in report