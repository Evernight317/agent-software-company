"""Tests for code file and review parsing."""

from company.agents.parser import parse_code_files, parse_review


SAMPLE_CODE_OUTPUT = """\
Here's the implementation:

### FILE: src/main.py
```python
def hello():
    print("hello")
```

### FILE: tests/test_main.py
```python
def test_hello():
    assert True
```
"""

SAMPLE_REVIEW_APPROVED = """\
The code looks good. APPROVED
"""

SAMPLE_REVIEW_CHANGES = """\
CHANGES_REQUESTED

- FILE: src/main.py
- LINE: 5
- SEVERITY: warning
- COMMENT: Missing error handling

- FILE: src/main.py
- LINE: 10
- SEVERITY: suggestion
- COMMENT: Add type hints
"""


def test_parse_code_files_count():
    files = parse_code_files(SAMPLE_CODE_OUTPUT)
    assert len(files) == 2


def test_parse_code_file_paths():
    files = parse_code_files(SAMPLE_CODE_OUTPUT)
    assert files[0].path == "src/main.py"
    assert files[1].path == "tests/test_main.py"


def test_parse_code_file_content():
    files = parse_code_files(SAMPLE_CODE_OUTPUT)
    assert "def hello" in files[0].content
    assert "test_hello" in files[1].content


def test_parse_code_file_language():
    files = parse_code_files(SAMPLE_CODE_OUTPUT)
    assert files[0].language == "python"


def test_parse_code_empty():
    files = parse_code_files("No code here")
    assert files == []


def test_parse_review_approved():
    review = parse_review(SAMPLE_REVIEW_APPROVED)
    assert review.approved is True
    assert len(review.comments) == 0


def test_parse_review_changes():
    review = parse_review(SAMPLE_REVIEW_CHANGES)
    assert review.changes_requested is True
    assert review.approved is False
    assert len(review.comments) == 2


def test_parse_review_comment_fields():
    review = parse_review(SAMPLE_REVIEW_CHANGES)
    assert review.comments[0].file == "src/main.py"
    assert review.comments[0].line == 5
    assert review.comments[0].severity == "warning"
    assert "error handling" in review.comments[0].comment
