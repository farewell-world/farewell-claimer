"""
Tests for email creation and sending functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from email.mime.multipart import MIMEMultipart
import smtplib

import farewell_claimer
from farewell_claimer import create_farewell_email, send_email, save_eml


class TestCreateFarewellEmail:
    """Tests for email creation."""

    def test_create_email_returns_mime_multipart(self):
        """Test that create_farewell_email returns MIMEMultipart."""
        email = create_farewell_email(
            sender_email="sender@test.com",
            sender_name="Test Sender",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body="Test message body",
            content_hash="0x1234567890abcdef"
        )
        assert isinstance(email, MIMEMultipart)

    def test_create_email_has_correct_headers(self):
        """Test email has correct headers."""
        email = create_farewell_email(
            sender_email="sender@test.com",
            sender_name="Test Sender",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body="Test message body",
            content_hash="0x1234567890abcdef"
        )
        assert email['From'] == "Test Sender <sender@test.com>"
        assert email['To'] == "recipient@test.com"
        assert email['Subject'] == "Test Subject"
        assert email['Date'] is not None
        assert email['Message-ID'] is not None

    def test_create_email_contains_farewell_hash(self):
        """Test email body contains Farewell-Hash."""
        import base64
        content_hash = "0x1234567890abcdef1234567890abcdef"
        email = create_farewell_email(
            sender_email="sender@test.com",
            sender_name="Test Sender",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body="Test message body",
            content_hash=content_hash
        )
        # Check in the payload of the parts (may be base64 encoded)
        for part in email.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    assert f"Farewell-Hash: {content_hash}" in payload.decode('utf-8')
                    return
        # Fallback: check raw string (in case not encoded)
        raw_email = email.as_string()
        assert content_hash in raw_email

    def test_create_email_contains_message_body(self):
        """Test email contains the message body."""
        message_body = "This is a unique test message content"
        email = create_farewell_email(
            sender_email="sender@test.com",
            sender_name="Test Sender",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body=message_body,
            content_hash="0x1234"
        )
        # Check in the payload of the parts (may be base64 encoded)
        for part in email.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    assert message_body in payload.decode('utf-8')
                    return
        # Fallback: check raw string
        raw_email = email.as_string()
        assert message_body in raw_email

    def test_create_email_has_multipart_content(self):
        """Test email has both plain text and HTML parts."""
        email = create_farewell_email(
            sender_email="sender@test.com",
            sender_name="Test Sender",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body="Test message body",
            content_hash="0x1234"
        )
        # Should have 2 parts: text/plain and text/html
        parts = list(email.walk())
        content_types = [part.get_content_type() for part in parts]
        assert 'text/plain' in content_types
        assert 'text/html' in content_types

    def test_create_email_message_id_uses_sender_domain(self):
        """Test Message-ID uses sender's domain."""
        email = create_farewell_email(
            sender_email="sender@mydomain.com",
            sender_name="Test Sender",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body="Test message body",
            content_hash="0x1234"
        )
        assert "mydomain.com" in email['Message-ID']


class TestSendEmail:
    """Tests for email sending."""

    @patch('farewell_claimer.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class, smtp_config):
        """Test successful email sending."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        email = create_farewell_email(
            sender_email=smtp_config.email,
            sender_name=smtp_config.display_name,
            recipient_email="recipient@test.com",
            subject="Test",
            message_body="Test body",
            content_hash="0x1234"
        )

        success, raw_msg = send_email(smtp_config, email, "recipient@test.com")

        assert success is True
        assert len(raw_msg) > 0
        mock_smtp.sendmail.assert_called_once()

    @patch('farewell_claimer.smtplib.SMTP_SSL')
    def test_send_email_ssl_success(self, mock_smtp_ssl_class, smtp_config_ssl):
        """Test successful email sending with SSL."""
        mock_smtp = MagicMock()
        mock_smtp_ssl_class.return_value = mock_smtp

        email = create_farewell_email(
            sender_email=smtp_config_ssl.email,
            sender_name=smtp_config_ssl.display_name,
            recipient_email="recipient@test.com",
            subject="Test",
            message_body="Test body",
            content_hash="0x1234"
        )

        success, raw_msg = send_email(smtp_config_ssl, email, "recipient@test.com")

        assert success is True
        mock_smtp_ssl_class.assert_called_once()

    @patch('farewell_claimer.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp_class, smtp_config):
        """Test failed email sending."""
        mock_smtp = MagicMock()
        mock_smtp.sendmail.side_effect = Exception("Send failed")
        mock_smtp_class.return_value = mock_smtp

        email = create_farewell_email(
            sender_email=smtp_config.email,
            sender_name=smtp_config.display_name,
            recipient_email="recipient@test.com",
            subject="Test",
            message_body="Test body",
            content_hash="0x1234"
        )

        success, error_msg = send_email(smtp_config, email, "recipient@test.com")

        assert success is False
        assert "Send failed" in error_msg

    @patch('farewell_claimer.smtplib.SMTP')
    def test_send_email_returns_raw_message(self, mock_smtp_class, smtp_config):
        """Test that successful send returns raw email message."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        email = create_farewell_email(
            sender_email=smtp_config.email,
            sender_name=smtp_config.display_name,
            recipient_email="recipient@test.com",
            subject="Test Subject",
            message_body="Test body",
            content_hash="0x1234"
        )

        success, raw_msg = send_email(smtp_config, email, "recipient@test.com")

        assert success is True
        assert "Test Subject" in raw_msg
        # Content may be base64 encoded, so check for presence of hash in any form
        # or check for base64 encoded version
        import base64
        hash_plain = "Farewell-Hash"
        hash_b64 = base64.b64encode(hash_plain.encode()).decode()
        assert hash_plain in raw_msg or hash_b64[:10] in raw_msg or "0x1234" in raw_msg


class TestSaveEml:
    """Tests for .eml file saving."""

    def test_save_eml_creates_file(self, temp_output_dir):
        """Test that save_eml creates a file."""
        raw_message = "From: test@test.com\nTo: recipient@test.com\n\nTest body"

        filepath = save_eml(raw_message, "test.eml", temp_output_dir)

        assert filepath.endswith("test.eml")
        with open(filepath, 'r') as f:
            content = f.read()
        assert content == raw_message

    def test_save_eml_creates_output_directory(self, tmp_path):
        """Test that save_eml creates output directory if needed."""
        new_dir = str(tmp_path / "new_proofs_dir")
        raw_message = "Test message"

        filepath = save_eml(raw_message, "test.eml", new_dir)

        assert filepath.endswith("test.eml")
        with open(filepath, 'r') as f:
            assert f.read() == raw_message

    def test_save_eml_preserves_unicode(self, temp_output_dir):
        """Test that save_eml preserves unicode characters."""
        raw_message = "From: test@test.com\n\nHello! Ñoño 你好 🎉"

        filepath = save_eml(raw_message, "unicode.eml", temp_output_dir)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "Ñoño" in content
        assert "你好" in content
