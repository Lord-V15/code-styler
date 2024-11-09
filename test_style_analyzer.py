# Unit tests for dummy runs and checking logic of the script itself

import unittest
from textwrap import dedent
from style_analyzer import PEP8Analyzer, StyleIssue
import tempfile
import os

class TestPEP8Analyzer(unittest.TestCase):
    def create_test_file(self, content: str) -> str:
        """Helper to create a temporary file with given content."""
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.py')
        temp.write(content.encode())
        temp.close()
        return temp.name

    def test_line_length(self):
        code = "x = 'This is a very long line that definitely exceeds the maximum line length of 79 characters specified by PEP 8'\n"
        filename = self.create_test_file(code)
        try:
            analyzer = PEP8Analyzer(filename)
            issues = analyzer.analyze()
            
            self.assertTrue(any(issue.code == 'E501' for issue in issues))
        finally:
            os.unlink(filename)

    def test_indentation(self):
        code = dedent("""
            def function():
               wrong_indent = True  # 3 spaces instead of 4
                correct_indent = True
        """)
        
        filename = self.create_test_file(code)
        try:
            analyzer = PEP8Analyzer(filename)
            issues = analyzer.analyze()
            
            self.assertTrue(any(issue.code == 'E111' for issue in issues))
        finally:
            os.unlink(filename)

    def test_whitespace(self):
        code = dedent("""
            x=1+2  # Missing spaces around operators
            y = 3 
        """)  # Trailing whitespace
        
        filename = self.create_test_file(code)
        try:
            analyzer = PEP8Analyzer(filename, auto_correct=True)
            issues = analyzer.analyze()
            
            self.assertTrue(any(issue.code == 'E225' for issue in issues))
            self.assertTrue(any(issue.code == 'W291' for issue in issues))
            
            # Check auto-correction
            with open(filename, 'r') as f:
                corrected = f.read()
            self.assertIn('x = 1 + 2', corrected)
        finally:
            os.unlink(filename)

    def test_naming_conventions(self):
        code = dedent("""
            class badName:  # Should be CapWords
                def BAD_FUNCTION_NAME():  # Should be lowercase
                    pass
                        """)
        
        filename = self.create_test_file(code)
        try:
            analyzer = PEP8Analyzer(filename)
            issues = analyzer.analyze()
            
            self.assertTrue(any(issue.code == 'N801' for issue in issues))
            self.assertTrue(any(issue.code == 'N802' for issue in issues))
        finally:
            os.unlink(filename)

    def test_import_ordering(self):
        code = dedent("""
            import sys
            import os
            from datetime import datetime
            from abc import ABC
        """)
        
        filename = self.create_test_file(code)
        try:
            analyzer = PEP8Analyzer(filename, auto_correct=True)
            issues = analyzer.analyze()
            
            self.assertTrue(any(issue.code == 'I100' for issue in issues))
            
            # Check auto-correction
            with open(filename, 'r') as f:
                corrected = f.read()
            self.assertTrue(corrected.index('from abc') < corrected.index('import sys'))
        finally:
            os.unlink(filename)

if __name__ == '__main__':
    unittest.main()
