"""
Pytest fixtures for farewell-claimer tests.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock colorama before importing the module
mock_fore = MagicMock()
mock_fore.CYAN = ""
mock_fore.MAGENTA = ""
mock_fore.GREEN = ""
mock_fore.BLUE = ""
mock_fore.YELLOW = ""
mock_fore.RED = ""
mock_fore.WHITE = ""

mock_style = MagicMock()
mock_style.RESET_ALL = ""

mock_back = MagicMock()

# Patch colorama
sys.modules['colorama'] = MagicMock()
sys.modules['colorama'].init = MagicMock()
sys.modules['colorama'].Fore = mock_fore
sys.modules['colorama'].Back = mock_back
sys.modules['colorama'].Style = mock_style

# Now we can import the module
import farewell_claimer


@pytest.fixture
def smtp_config():
    """Create a test SMTP configuration."""
    return farewell_claimer.SMTPConfig(
        host="smtp.test.com",
        port=587,
        use_tls=True,
        use_ssl=False,
        email="sender@test.com",
        password="testpassword",
        display_name="Test Sender"
    )


@pytest.fixture
def smtp_config_ssl():
    """Create a test SMTP configuration with SSL."""
    return farewell_claimer.SMTPConfig(
        host="smtp.test.com",
        port=465,
        use_tls=False,
        use_ssl=True,
        email="sender@test.com",
        password="testpassword",
        display_name="Test Sender"
    )


@pytest.fixture
def sample_message_info():
    """Sample message information."""
    return {
        "recipients": ["recipient1@test.com", "recipient2@test.com"],
        "content_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "message": "This is a farewell message.\n\nWith love,\nSender"
    }


@pytest.fixture
def sample_eml_content():
    """Sample .eml file content."""
    return """From: Test Sender <sender@test.com>
To: recipient@test.com
Subject: Farewell Message Delivery
Date: Thu, 30 Jan 2025 12:00:00 +0000
Message-ID: <test123@test.com>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

This is a farewell message.

---
Farewell-Hash: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
---

This message was sent via Farewell Protocol (https://www.iampedro.com/farewell)
--boundary123--
"""


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "proofs"
    output_dir.mkdir()
    return str(output_dir)
