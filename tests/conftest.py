"""Pytest configuration for audiobook_ru tests."""
import sys
from pathlib import Path

import pytest

# Ensure the src directory is on the path so we can import audiobook_ru
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def project_dir():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def sample_text():
    """Provide a sample Russian text for testing."""
    return """Глава 1

Вот начало книги. Здесь описано первое событие.

Второе предложение в первом абзаце.

Глава 2

Здесь продолжается история. Третье предложение.

Четвертое предложание.

Глава 3

Заключительная часть книги. Последнее предложение.
"""