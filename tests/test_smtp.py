"""
Tests for SMTP configuration and connection functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import smtplib

import farewell_claimer
from farewell_claimer import SMTPConfig, SMTP_PRESETS


class TestSMTPConfig:
    """Tests for SMTPConfig dataclass."""

    def test_smtp_config_creation(self):
        """Test creating an SMTP config."""
        config = SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            use_tls=True,
            use_ssl=False,
            email="test@gmail.com",
            password="secret"
        )
        assert config.host == "smtp.gmail.com"
        assert config.port == 587
        assert config.use_tls is True
        assert config.use_ssl is False
        assert config.email == "test@gmail.com"
        assert config.password == "secret"
        assert config.display_name is None

    def test_smtp_config_with_display_name(self):
        """Test SMTP config with optional display name."""
        config = SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            use_tls=True,
            use_ssl=False,
            email="test@gmail.com",
            password="secret",
            display_name="John Doe"
        )
        assert config.display_name == "John Doe"


class TestSMTPPresets:
    """Tests for SMTP presets configuration."""

    def test_gmail_preset_exists(self):
        """Test Gmail preset configuration."""
        assert "gmail" in SMTP_PRESETS
        gmail = SMTP_PRESETS["gmail"]
        assert gmail["host"] == "smtp.gmail.com"
        assert gmail["port"] == 587
        assert gmail["use_tls"] is True
        assert gmail["use_ssl"] is False

    def test_outlook_preset_exists(self):
        """Test Outlook preset configuration."""
        assert "outlook" in SMTP_PRESETS
        outlook = SMTP_PRESETS["outlook"]
        assert outlook["host"] == "smtp-mail.outlook.com"
        assert outlook["port"] == 587

    def test_yahoo_preset_exists(self):
        """Test Yahoo preset configuration."""
        assert "yahoo" in SMTP_PRESETS
        yahoo = SMTP_PRESETS["yahoo"]
        assert yahoo["host"] == "smtp.mail.yahoo.com"
        assert yahoo["port"] == 587

    def test_icloud_preset_exists(self):
        """Test iCloud preset configuration."""
        assert "icloud" in SMTP_PRESETS
        icloud = SMTP_PRESETS["icloud"]
        assert icloud["host"] == "smtp.mail.me.com"
        assert icloud["port"] == 587

    def test_all_presets_have_required_fields(self):
        """Test all presets have required fields."""
        required_fields = ["host", "port", "use_tls", "use_ssl"]
        for provider, preset in SMTP_PRESETS.items():
            for field in required_fields:
                assert field in preset, f"{provider} missing {field}"


class TestSMTPConnection:
    """Tests for SMTP connection testing."""

    @patch('farewell_claimer.smtplib.SMTP')
    def test_smtp_connection_success_tls(self, mock_smtp_class, smtp_config):
        """Test successful SMTP connection with TLS."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        result = farewell_claimer.test_smtp_connection(smtp_config)

        assert result is True
        mock_smtp_class.assert_called_once_with(smtp_config.host, smtp_config.port, timeout=30)
        mock_smtp.ehlo.assert_called()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with(smtp_config.email, smtp_config.password)
        mock_smtp.quit.assert_called_once()

    @patch('farewell_claimer.smtplib.SMTP_SSL')
    def test_smtp_connection_success_ssl(self, mock_smtp_ssl_class, smtp_config_ssl):
        """Test successful SMTP connection with SSL."""
        mock_smtp = MagicMock()
        mock_smtp_ssl_class.return_value = mock_smtp

        result = farewell_claimer.test_smtp_connection(smtp_config_ssl)

        assert result is True
        mock_smtp_ssl_class.assert_called_once_with(smtp_config_ssl.host, smtp_config_ssl.port, timeout=30)
        mock_smtp.login.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @patch('farewell_claimer.smtplib.SMTP')
    def test_smtp_connection_auth_failure(self, mock_smtp_class, smtp_config):
        """Test SMTP connection with authentication failure."""
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
        mock_smtp_class.return_value = mock_smtp

        result = farewell_claimer.test_smtp_connection(smtp_config)

        assert result is False

    @patch('farewell_claimer.smtplib.SMTP')
    def test_smtp_connection_network_error(self, mock_smtp_class, smtp_config):
        """Test SMTP connection with network error."""
        mock_smtp_class.side_effect = Exception("Network error")

        result = farewell_claimer.test_smtp_connection(smtp_config)

        assert result is False

    @patch('farewell_claimer.smtplib.SMTP')
    def test_smtp_connection_timeout(self, mock_smtp_class, smtp_config):
        """Test SMTP connection timeout."""
        mock_smtp_class.side_effect = TimeoutError("Connection timed out")

        result = farewell_claimer.test_smtp_connection(smtp_config)

        assert result is False
