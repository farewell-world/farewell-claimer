#!/usr/bin/env python3
"""
Farewell Claimer Helper Script
==============================

A user-friendly tool to help Farewell message claimers:
1. Send emails to recipients with the required Farewell-Hash
2. Export sent emails as .eml files
3. Generate zk-email proofs for the Farewell smart contract

Requirements:
    pip install colorama google-auth-oauthlib google-api-python-client

Usage:
    python farewell_claimer.py                      # Interactive mode
    python farewell_claimer.py message.json         # Load from file
    python farewell_claimer.py -f message.json      # Load from file (explicit)

Author: Farewell Protocol
License: GPL-3.0
"""

import os
import sys
import json
import smtplib
import hashlib
import time
import base64
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
from dataclasses import dataclass, field

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    print("Please install colorama: pip install colorama")
    sys.exit(1)

# Optional: Google OAuth support
GOOGLE_OAUTH_AVAILABLE = False
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    pass  # OAuth is optional, will use password-based auth

# ============ Configuration ============

@dataclass
class SMTPConfig:
    """SMTP server configuration."""
    host: str
    port: int
    use_tls: bool
    use_ssl: bool
    email: str
    password: str
    display_name: Optional[str] = None
    use_oauth: bool = False
    oauth_credentials: Optional[any] = None


# Gmail OAuth scopes - send permission + metadata for profile access
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.metadata'
]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Pre-configured SMTP settings for popular providers
SMTP_PRESETS: Dict[str, Dict] = {
    "gmail_oauth": {
        "host": "gmail-api",
        "port": 0,
        "use_tls": False,
        "use_ssl": False,
        "use_oauth": True,
        "note": "Uses OAuth 2.0 - no password required! Opens browser for authorization.",
        "help_url": "https://console.cloud.google.com/"
    },
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "note": "Requires an App Password (enable 2FA first)",
        "help_url": "https://support.google.com/accounts/answer/185833"
    },
    "outlook": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "note": "Use your regular Outlook/Hotmail credentials",
        "help_url": "https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-for-outlook-com"
    },
    "yahoo": {
        "host": "smtp.mail.yahoo.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "note": "Generate an App Password in Yahoo Account settings",
        "help_url": "https://help.yahoo.com/kb/generate-third-party-passwords-sln15241.html"
    },
    "icloud": {
        "host": "smtp.mail.me.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "note": "Generate an app-specific password at appleid.apple.com",
        "help_url": "https://support.apple.com/en-us/HT204397"
    },
    "zoho": {
        "host": "smtp.zoho.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "note": "Use your Zoho Mail credentials",
        "help_url": "https://www.zoho.com/mail/help/zoho-smtp.html"
    },
    "protonmail": {
        "host": "smtp.protonmail.ch",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "note": "Requires ProtonMail Bridge - not fully supported yet",
        "help_url": "https://protonmail.com/bridge/"
    }
}

# ============ UI Helpers ============

def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the Farewell banner with logo."""
    banner = f"""
{Fore.CYAN}                        ╭──────╮
                    ╭───╯      ╰───╮
                ╭───╯      {Fore.WHITE}│{Fore.CYAN}       ╰───╮
            ╭───╯          {Fore.WHITE}│{Fore.CYAN}           ╰───╮
          ╭─╯            {Fore.WHITE}╭─┴─╮{Fore.CYAN}             ╰─╮
        ╭─╯              {Fore.WHITE}│   │{Fore.CYAN}               ╰─╮
       ╭╯                {Fore.WHITE}│   │{Fore.CYAN}                 ╰╮
      ╭╯                 {Fore.WHITE}│   │{Fore.CYAN}                  ╰╮
      │                  {Fore.WHITE}╰───╯{Fore.CYAN}                   │
      │                                          │
      │      {Fore.WHITE}F A R E W E L L{Fore.CYAN}                    │
      │                                          │
      ╰╮                                        ╭╯
       ╰╮       {Fore.YELLOW}Claimer Helper{Fore.CYAN}                ╭╯
        ╰─╮   {Fore.YELLOW}ZK-Email Proof Generator{Fore.CYAN}     ╭─╯
          ╰─╮                              ╭─╯
            ╰───╮                      ╭───╯
                ╰───╮              ╭───╯
                    ╰───╮      ╭───╯
                        ╰──────╯
{Style.RESET_ALL}"""
    print(banner)

def print_section(title: str):
    """Print a section header."""
    print(f"\n{Fore.CYAN}{'─' * 60}")
    print(f"{Fore.CYAN}  {title}")
    print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}\n")

def print_success(msg: str):
    """Print success message."""
    print(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")

def print_error(msg: str):
    """Print error message."""
    print(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")

def print_warning(msg: str):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")

def print_info(msg: str):
    """Print info message."""
    print(f"{Fore.BLUE}ℹ {msg}{Style.RESET_ALL}")

def prompt(msg: str, default: str = "") -> str:
    """Prompt user for input."""
    if default:
        result = input(f"{Fore.WHITE}{msg} [{Fore.CYAN}{default}{Fore.WHITE}]: {Style.RESET_ALL}")
        return result if result else default
    return input(f"{Fore.WHITE}{msg}: {Style.RESET_ALL}")

def prompt_password(msg: str) -> str:
    """Prompt user for password (hidden input)."""
    import getpass
    return getpass.getpass(f"{Fore.WHITE}{msg}: {Style.RESET_ALL}")

def select_option(options: List[str], title: str = "Select an option:") -> int:
    """Display numbered options and return selected index."""
    print(f"{Fore.WHITE}{title}{Style.RESET_ALL}")
    for i, opt in enumerate(options, 1):
        print(f"  {Fore.CYAN}{i}.{Style.RESET_ALL} {opt}")

    while True:
        try:
            choice = int(prompt("Enter your choice"))
            if 1 <= choice <= len(options):
                return choice - 1
            print_error(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_error("Please enter a valid number")

def confirm(msg: str, default: bool = True) -> bool:
    """Ask for confirmation."""
    suffix = "[Y/n]" if default else "[y/N]"
    result = prompt(f"{msg} {suffix}").lower()
    if not result:
        return default
    return result in ('y', 'yes')

# ============ Gmail OAuth ============

def setup_gmail_oauth() -> Optional[SMTPConfig]:
    """Setup Gmail with OAuth 2.0 authentication."""
    if not GOOGLE_OAUTH_AVAILABLE:
        print_error("Google OAuth libraries not installed!")
        print_info("Install with: pip install google-auth-oauthlib google-api-python-client")
        return None

    # Check for credentials.json
    if not Path(CREDENTIALS_FILE).exists():
        print_error(f"'{CREDENTIALS_FILE}' not found!")
        print_info("To set up Gmail OAuth:")
        print_info("  1. Go to https://console.cloud.google.com/")
        print_info("  2. Create a project (or select existing)")
        print_info("  3. Enable the Gmail API")
        print_info("  4. Create OAuth 2.0 credentials (Desktop app)")
        print_info(f"  5. Download and save as '{CREDENTIALS_FILE}' in this directory")
        return None

    creds = None

    # Load existing token if available
    if Path(TOKEN_FILE).exists():
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
            print_info("Found existing OAuth token.")
        except Exception:
            pass

    # If no valid credentials, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print_info("Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print_warning(f"Could not refresh token: {e}")
                creds = None

        if not creds:
            print_info("Opening browser for Google authorization...")
            print_info("Please sign in and grant permission to send emails.")
            print()

            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print_error(f"OAuth flow failed: {e}")
                return None

        # Save the token for future use
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print_success(f"Token saved to '{TOKEN_FILE}' for future use.")
        except Exception as e:
            print_warning(f"Could not save token: {e}")

    # Get the user's email address
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile['emailAddress']
        print_success(f"Authenticated as: {email}")
    except Exception as e:
        print_error(f"Could not get user profile: {e}")
        return None

    display_name = prompt("Display name (optional)", email.split('@')[0])

    return SMTPConfig(
        host="gmail-api",
        port=0,
        use_tls=False,
        use_ssl=False,
        email=email,
        password="",
        display_name=display_name,
        use_oauth=True,
        oauth_credentials=creds
    )


def send_email_gmail_api(config: SMTPConfig, email_msg: MIMEMultipart, recipient: str) -> Tuple[bool, str]:
    """Send email using Gmail API (OAuth)."""
    if not GOOGLE_OAUTH_AVAILABLE:
        return False, "Google OAuth libraries not installed"

    try:
        service = build('gmail', 'v1', credentials=config.oauth_credentials)

        # Get raw message
        raw_msg = email_msg.as_string()

        # Encode for Gmail API
        encoded_message = base64.urlsafe_b64encode(raw_msg.encode('utf-8')).decode('utf-8')

        # Send via Gmail API
        message = {'raw': encoded_message}
        service.users().messages().send(userId='me', body=message).execute()

        return True, raw_msg
    except HttpError as e:
        return False, f"Gmail API error: {e}"
    except Exception as e:
        return False, str(e)


def test_gmail_oauth_connection(config: SMTPConfig) -> bool:
    """Test Gmail OAuth connection by checking profile."""
    print_info("Testing Gmail OAuth connection...")
    try:
        service = build('gmail', 'v1', credentials=config.oauth_credentials)
        profile = service.users().getProfile(userId='me').execute()
        print_success(f"Gmail OAuth connection successful! ({profile['emailAddress']})")
        return True
    except Exception as e:
        print_error(f"Gmail OAuth test failed: {e}")
        return False


# ============ SMTP Configuration ============

def setup_smtp() -> Optional[SMTPConfig]:
    """Interactive SMTP setup."""
    print_section("SMTP Configuration")

    # Build provider list dynamically
    providers = []
    provider_names = []

    # Gmail OAuth (recommended if available)
    if GOOGLE_OAUTH_AVAILABLE and Path(CREDENTIALS_FILE).exists():
        providers.append("gmail_oauth")
        provider_names.append(f"{Fore.GREEN}Gmail (OAuth 2.0){Style.RESET_ALL} - Recommended, no password needed!")
    elif GOOGLE_OAUTH_AVAILABLE:
        providers.append("gmail_oauth")
        provider_names.append(f"{Fore.GREEN}Gmail (OAuth 2.0){Style.RESET_ALL} - Requires credentials.json setup")

    # Standard providers
    providers.append("gmail")
    provider_names.append(f"{Fore.GREEN}Gmail (App Password){Style.RESET_ALL} - smtp.gmail.com")

    providers.extend(["outlook", "yahoo", "icloud", "zoho", "protonmail", "manual"])
    provider_names.extend([
        f"{Fore.BLUE}Outlook/Hotmail{Style.RESET_ALL} (smtp-mail.outlook.com)",
        f"{Fore.MAGENTA}Yahoo{Style.RESET_ALL} (smtp.mail.yahoo.com)",
        f"{Fore.CYAN}iCloud{Style.RESET_ALL} (smtp.mail.me.com)",
        f"{Fore.YELLOW}Zoho{Style.RESET_ALL} (smtp.zoho.com)",
        f"{Fore.WHITE}ProtonMail{Style.RESET_ALL} (requires Bridge)",
        f"{Fore.RED}Manual Configuration{Style.RESET_ALL} (custom SMTP server)"
    ])

    choice = select_option(provider_names, "Select your email provider:")
    provider = providers[choice]

    # Handle special cases
    if provider == "gmail_oauth":
        return setup_gmail_oauth()

    if provider == "manual":
        return setup_smtp_manual()

    preset = SMTP_PRESETS[provider]

    print()
    print_info(f"Selected: {provider.upper()}")
    print_info(f"Server: {preset['host']}:{preset['port']}")
    if preset.get('note'):
        print_warning(preset['note'])
        if preset.get('help_url'):
            print_info(f"Help: {preset['help_url']}")
    print()

    email = prompt("Your email address")
    password = prompt_password("Your password (or app password)")
    display_name = prompt("Display name (optional)", email.split('@')[0])

    return SMTPConfig(
        host=preset['host'],
        port=preset['port'],
        use_tls=preset['use_tls'],
        use_ssl=preset['use_ssl'],
        email=email,
        password=password,
        display_name=display_name
    )

def setup_smtp_manual() -> SMTPConfig:
    """Manual SMTP configuration."""
    print_section("Manual SMTP Configuration")

    host = prompt("SMTP server hostname")
    port = int(prompt("SMTP port", "587"))
    use_tls = confirm("Use STARTTLS?", True)
    use_ssl = confirm("Use SSL/TLS?", False) if not use_tls else False
    email = prompt("Your email address")
    password = prompt_password("Your password")
    display_name = prompt("Display name (optional)", email.split('@')[0])

    return SMTPConfig(
        host=host,
        port=port,
        use_tls=use_tls,
        use_ssl=use_ssl,
        email=email,
        password=password,
        display_name=display_name
    )

def test_smtp_connection(config: SMTPConfig) -> bool:
    """Test SMTP connection."""
    # Use Gmail OAuth test if applicable
    if config.use_oauth:
        return test_gmail_oauth_connection(config)

    print_info("Testing SMTP connection...")
    try:
        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.host, config.port, timeout=30)
        else:
            server = smtplib.SMTP(config.host, config.port, timeout=30)

        server.ehlo()

        if config.use_tls and not config.use_ssl:
            server.starttls()
            server.ehlo()

        server.login(config.email, config.password)
        server.quit()

        print_success("SMTP connection successful!")
        return True
    except smtplib.SMTPAuthenticationError:
        print_error("Authentication failed. Check your email and password.")
        print_info("For Gmail/Outlook, you may need to use an App Password.")
        return False
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False

# ============ Email Sending ============

def create_farewell_email(
    sender_email: str,
    sender_name: str,
    recipient_email: str,
    subject: str,
    message_body: str,
    content_hash: str
) -> MIMEMultipart:
    """Create an email with Farewell-Hash embedded."""
    msg = MIMEMultipart('alternative')

    # Headers
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[1])

    # Body with Farewell-Hash
    body_with_hash = f"""{message_body}

---
Farewell-Hash: {content_hash}
---

This message was sent via Farewell Protocol (https://www.iampedro.com/farewell)
A zk-email proof may be generated to verify delivery of this message.
"""

    # Plain text version
    text_part = MIMEText(body_with_hash, 'plain', 'utf-8')
    msg.attach(text_part)

    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
        {message_body.replace(chr(10), '<br>')}

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">

        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; font-family: monospace;">
            <strong>Farewell-Hash:</strong><br>
            <code style="word-break: break-all;">{content_hash}</code>
        </div>

        <p style="color: #666; font-size: 12px; margin-top: 20px;">
            This message was sent via <a href="https://www.iampedro.com/farewell">Farewell Protocol</a>.<br>
            A zk-email proof may be generated to verify delivery of this message.
        </p>
    </div>
</body>
</html>
"""
    html_part = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(html_part)

    return msg

def send_email(config: SMTPConfig, email_msg: MIMEMultipart, recipient: str) -> Tuple[bool, str]:
    """Send an email and return (success, raw_message)."""
    # Use Gmail API if OAuth is configured
    if config.use_oauth:
        return send_email_gmail_api(config, email_msg, recipient)

    try:
        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.host, config.port, timeout=30)
        else:
            server = smtplib.SMTP(config.host, config.port, timeout=30)

        server.ehlo()

        if config.use_tls and not config.use_ssl:
            server.starttls()
            server.ehlo()

        server.login(config.email, config.password)

        raw_msg = email_msg.as_string()
        server.sendmail(config.email, recipient, raw_msg)
        server.quit()

        return True, raw_msg
    except Exception as e:
        return False, str(e)

def save_eml(raw_message: str, filename: str, output_dir: str = "proofs") -> str:
    """Save email as .eml file."""
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(raw_message)
    return str(filepath)

# ============ Proof Generation ============

def generate_proof_data(eml_content: str, recipient_email: str, content_hash: str) -> Dict:
    """
    Generate proof data from .eml file.

    Note: This generates a placeholder proof structure.
    In production, this would integrate with the actual zk-email circuit prover.
    """
    # Compute recipient email hash (matching the contract's expectation)
    # Using keccak256 as placeholder for Poseidon
    recipient_normalized = recipient_email.lower().strip()
    recipient_hash = "0x" + hashlib.sha3_256(recipient_normalized.encode()).hexdigest()

    # Extract DKIM info (simplified)
    dkim_pubkey_hash = "0x" + "0" * 64  # Placeholder

    # The proof structure that would be submitted to the contract
    proof = {
        "pA": ["0x0", "0x0"],
        "pB": [["0x0", "0x0"], ["0x0", "0x0"]],
        "pC": ["0x0", "0x0"],
        "publicSignals": [
            recipient_hash,      # [0] recipient email hash
            dkim_pubkey_hash,    # [1] DKIM pubkey hash
            content_hash         # [2] content hash
        ]
    }

    return proof

def save_proof(proof: Dict, filename: str, output_dir: str = "proofs") -> str:
    """Save proof as JSON file."""
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / filename
    with open(filepath, 'w') as f:
        json.dump(proof, f, indent=2)
    return str(filepath)

# ============ Main Flow ============

def load_message_from_file(filepath: str) -> Optional[Dict]:
    """
    Load message data from a JSON file exported from Farewell UI.

    Expected JSON format:
    {
        "recipients": ["email1@example.com", "email2@example.com"],
        "contentHash": "0x1234...",
        "message": "The farewell message content...",
        "subject": "Optional custom subject"
    }
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print_error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON file: {e}")
        return None

    # Validate required fields
    if 'recipients' not in data:
        print_error("Missing 'recipients' field in JSON")
        return None
    if 'contentHash' not in data and 'content_hash' not in data:
        print_error("Missing 'contentHash' field in JSON")
        return None
    if 'message' not in data:
        print_error("Missing 'message' field in JSON")
        return None

    # Normalize field names (support both camelCase and snake_case)
    recipients = data['recipients']
    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]

    content_hash = data.get('contentHash') or data.get('content_hash', '')
    if not content_hash.startswith('0x'):
        content_hash = '0x' + content_hash

    result = {
        "recipients": recipients,
        "content_hash": content_hash,
        "message": data['message'],
        "subject": data.get('subject', 'Farewell Message Delivery')
    }

    print_success(f"Loaded message data from: {filepath}")
    print_info(f"  Recipients: {len(result['recipients'])}")
    print_info(f"  Content hash: {result['content_hash'][:20]}...")

    return result


def get_message_info() -> Dict:
    """Get Farewell message information from user (interactive mode)."""
    print_section("Message Information")

    print_info("Enter the information from the decrypted Farewell message:")
    print()

    recipients = prompt("Recipient email(s) (comma-separated for multiple)").split(',')
    recipients = [r.strip() for r in recipients if r.strip()]

    content_hash = prompt("Payload Content Hash (from contract, starts with 0x)")
    if not content_hash.startswith('0x'):
        content_hash = '0x' + content_hash

    message_content = []
    print_info("Enter the message content (end with an empty line):")
    while True:
        line = input()
        if not line:
            break
        message_content.append(line)

    return {
        "recipients": recipients,
        "content_hash": content_hash,
        "message": "\n".join(message_content),
        "subject": "Farewell Message Delivery"
    }

def main_flow(message_file: Optional[str] = None):
    """Main application flow."""
    clear_screen()
    print_banner()

    # Load message from file if provided
    msg_info = None
    if message_file:
        print_section("Loading Message Data")
        msg_info = load_message_from_file(message_file)
        if msg_info is None:
            return
        print()

    print(f"""
{Fore.WHITE}Welcome to the Farewell Claimer Helper!{Style.RESET_ALL}

This tool will help you:
  {Fore.GREEN}1.{Style.RESET_ALL} Configure your email sending
  {Fore.GREEN}2.{Style.RESET_ALL} Send the Farewell message to recipients
  {Fore.GREEN}3.{Style.RESET_ALL} Generate zk-email proofs for the blockchain

{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}
""")
    input()

    # Step 1: SMTP Configuration
    smtp_config = setup_smtp()

    if smtp_config is None:
        print_error("SMTP configuration failed.")
        return

    if not test_smtp_connection(smtp_config):
        if not confirm("Connection failed. Try again?"):
            print_error("Aborting.")
            return
        smtp_config = setup_smtp()
        if smtp_config is None or not test_smtp_connection(smtp_config):
            print_error("Could not connect to SMTP server. Please check your settings.")
            return

    # Step 2: Get Message Information (if not loaded from file)
    if msg_info is None:
        msg_info = get_message_info()

    if not msg_info['recipients']:
        print_error("No recipients specified!")
        return

    # Summary
    print_section("Summary")
    print(f"  {Fore.WHITE}From:{Style.RESET_ALL} {smtp_config.email}")
    print(f"  {Fore.WHITE}Recipients:{Style.RESET_ALL} {', '.join(msg_info['recipients'])}")
    print(f"  {Fore.WHITE}Content Hash:{Style.RESET_ALL} {msg_info['content_hash']}")
    print(f"  {Fore.WHITE}Message Preview:{Style.RESET_ALL}")
    for line in msg_info['message'].split('\n')[:3]:
        print(f"    {Fore.CYAN}{line[:60]}{'...' if len(line) > 60 else ''}{Style.RESET_ALL}")
    print()

    if not confirm("Proceed with sending?"):
        print_info("Aborted by user.")
        return

    # Step 3: Send emails and generate proofs
    print_section("Sending Emails & Generating Proofs")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    proofs_dir = f"farewell_proofs_{timestamp}"

    results = []
    for i, recipient in enumerate(msg_info['recipients'], 1):
        print(f"\n{Fore.CYAN}[{i}/{len(msg_info['recipients'])}]{Style.RESET_ALL} Processing: {recipient}")

        # Create email
        subject = msg_info.get('subject', 'Farewell Message Delivery')
        email_msg = create_farewell_email(
            sender_email=smtp_config.email,
            sender_name=smtp_config.display_name or smtp_config.email,
            recipient_email=recipient,
            subject=subject,
            message_body=msg_info['message'],
            content_hash=msg_info['content_hash']
        )

        # Send email
        print_info(f"Sending email to {recipient}...")
        success, raw_msg = send_email(smtp_config, email_msg, recipient)

        if not success:
            print_error(f"Failed to send: {raw_msg}")
            results.append({"recipient": recipient, "success": False, "error": raw_msg})
            continue

        print_success("Email sent!")

        # Save .eml file
        eml_filename = f"recipient_{i}_{recipient.replace('@', '_at_')}.eml"
        eml_path = save_eml(raw_msg, eml_filename, proofs_dir)
        print_success(f"Saved .eml: {eml_path}")

        # Generate proof
        print_info("Generating proof...")
        proof = generate_proof_data(raw_msg, recipient, msg_info['content_hash'])
        proof_filename = f"proof_{i}_{recipient.replace('@', '_at_')}.json"
        proof_path = save_proof(proof, proof_filename, proofs_dir)
        print_success(f"Saved proof: {proof_path}")

        results.append({
            "recipient": recipient,
            "success": True,
            "eml_path": eml_path,
            "proof_path": proof_path
        })

        # Small delay between emails
        if i < len(msg_info['recipients']):
            time.sleep(1)

    # Final Summary
    print_section("Results")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    if successful:
        print_success(f"{len(successful)} email(s) sent successfully!")
        print()
        print(f"{Fore.WHITE}Generated files in: {Fore.CYAN}{proofs_dir}/{Style.RESET_ALL}")
        print()
        for r in successful:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {r['recipient']}")
            print(f"    .eml:   {r['eml_path']}")
            print(f"    proof:  {r['proof_path']}")

    if failed:
        print()
        print_error(f"{len(failed)} email(s) failed:")
        for r in failed:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {r['recipient']}: {r.get('error', 'Unknown error')}")

    # Instructions
    print_section("Next Steps")
    print(f"""
{Fore.WHITE}To claim your reward on Farewell:{Style.RESET_ALL}

  1. Go to the Farewell claim page
  2. For each recipient, upload the corresponding .eml file
  3. Click "Prove Delivery" for each recipient
  4. Once all recipients are proven, click "Claim Reward"

{Fore.YELLOW}Note:{Style.RESET_ALL} The proof files (.json) can also be used to manually
submit proofs if the UI upload doesn't work.

{Fore.GREEN}Thank you for using Farewell!{Style.RESET_ALL}
""")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Farewell Claimer - Send emails and generate zk-email proofs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                       Interactive mode
  %(prog)s message.json          Load message data from JSON file
  %(prog)s -f message.json       Same as above (explicit flag)

JSON file format:
  {
    "recipients": ["alice@example.com", "bob@example.com"],
    "contentHash": "0x1234...",
    "message": "Your farewell message content..."
  }

Export this JSON from the Farewell UI after claiming a message.
"""
    )
    parser.add_argument(
        'file',
        nargs='?',
        help='JSON file with message data (exported from Farewell UI)'
    )
    parser.add_argument(
        '-f', '--file',
        dest='file_flag',
        help='JSON file with message data (alternative to positional argument)'
    )
    return parser.parse_args()


def main():
    """Entry point."""
    args = parse_args()

    # Determine message file (positional arg takes precedence)
    message_file = args.file or args.file_flag

    try:
        main_flow(message_file)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
