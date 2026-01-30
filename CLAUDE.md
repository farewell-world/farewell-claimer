# CLAUDE.md - Farewell Claimer

## Project Overview

Farewell Claimer is a Python CLI tool that helps claimers send farewell messages to recipients and generate zk-email proofs for claiming rewards on the Farewell smart contract.

**Status**: Functional proof-of-concept. Works with the Farewell protocol on Sepolia testnet.

**Live Demo**: https://farewell.world

**License**: BSD 3-Clause

## Repository Structure

```
farewell-claimer/
├── farewell_claimer.py      # Main CLI application (single file)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_smtp.py         # SMTP configuration tests
│   ├── test_email.py        # Email creation/sending tests
│   ├── test_proof.py        # Proof generation tests
│   └── test_ui.py           # UI helper tests
├── docs/
│   └── claimer-guide.md     # Step-by-step user guide
├── assets/
│   └── farewell-logo.png    # Project logo
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
├── pytest.ini              # Pytest configuration
└── README.md
```

## Quick Start

```bash
# Create virtual environment (recommended for PEP 668 compliance)
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run with exported JSON from Farewell UI
python farewell_claimer.py message.json

# Run interactive mode
python farewell_claimer.py
```

## Key Technologies

- **Language**: Python 3.8+
- **Email**: SMTP/STARTTLS, Gmail OAuth 2.0 via API
- **Dependencies**: colorama, google-auth-oauthlib, google-api-python-client
- **Testing**: pytest

## Application Architecture

### Single-File Design

The entire application is in `farewell_claimer.py` for easy distribution and portability. Key components:

1. **Data Classes**
   - `SMTPConfig` - Email server configuration
   - `MessageData` - Recipient, content, hash info
   - `ProofData` - Generated proof structure

2. **SMTP Providers**
   - Gmail (OAuth 2.0 - recommended)
   - Gmail (App Password)
   - Outlook/Hotmail
   - Yahoo
   - iCloud
   - Zoho
   - Custom SMTP

3. **Core Functions**
   - `create_farewell_email()` - Build MIME message with Farewell-Hash
   - `send_email()` / `send_email_gmail_api()` - Send via SMTP or Gmail API
   - `export_email_to_eml()` - Save .eml for proof generation
   - `generate_proof_structure()` - Create zk-email proof data

### Gmail OAuth Flow

1. User places `credentials.json` (from Google Cloud Console) in working directory
2. On first run, browser opens for OAuth consent
3. Token saved to `token.json` for future use
4. Required scopes: `gmail.send`, `gmail.compose`, `gmail.metadata`

### Email Format

Emails include a special `Farewell-Hash` marker in the body:

```
[Message content]

---
Farewell-Hash: 0x1234...abcd
---

This message was sent via Farewell Protocol (https://farewell.world)
```

This hash is extracted by the zk-email circuit to verify the message content matches the on-chain commitment.

## CLI Interface

### Input Modes

1. **JSON File** (recommended)
   ```bash
   python farewell_claimer.py message.json
   ```

   JSON format:
   ```json
   {
     "recipients": ["alice@example.com", "bob@example.com"],
     "contentHash": "0x1234...",
     "message": "The farewell message content...",
     "subject": "Optional custom subject"
   }
   ```

2. **Interactive Mode**
   ```bash
   python farewell_claimer.py
   ```
   Prompts for all required information.

### Output

Creates timestamped directory with:
```
farewell_proofs_YYYYMMDD_HHMMSS/
├── recipient_1_user_at_example_com.eml    # Email for proof generation
├── proof_1_user_at_example_com.json       # Proof data for blockchain
├── recipient_2_another_at_example_com.eml
└── proof_2_another_at_example_com.json
```

## Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=farewell_claimer --cov-report=term-missing

# Run specific test file
pytest tests/test_email.py -v
```

### Test Fixtures (`conftest.py`)

- `smtp_config` - Test SMTP configuration
- `mock_smtp` - Mocked SMTP connection
- `sample_eml_content` - Sample .eml for parsing tests
- `temp_output_dir` - Temporary directory for output files

## Key Functions Reference

### Email Creation

```python
def create_farewell_email(
    sender: str,
    recipient: str,
    subject: str,
    message_body: str,
    content_hash: str
) -> MIMEMultipart:
    """Create MIME email with Farewell-Hash embedded in body."""
```

### Email Sending

```python
def send_email(
    config: SMTPConfig,
    email_msg: MIMEMultipart,
    recipient: str
) -> Tuple[bool, str]:
    """Send email via SMTP or Gmail API. Returns (success, raw_message)."""

def send_email_gmail_api(
    config: SMTPConfig,
    email_msg: MIMEMultipart,
    recipient: str
) -> Tuple[bool, str]:
    """Send via Gmail API with OAuth 2.0."""
```

### Proof Generation

```python
def generate_proof_structure(
    recipient_email: str,
    content_hash: str,
    email_date: str,
    sender_email: str
) -> Dict:
    """Generate zk-email proof structure for blockchain submission."""
```

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints for function signatures
- Use dataclasses for structured data
- Colorama for terminal colors (cross-platform)

### Adding Email Providers

1. Add provider config to `SMTP_PROVIDERS` dict
2. Add option in `select_email_provider()` menu
3. Update README.md if special setup required

### Error Handling

- All SMTP operations wrapped in try/except
- User-friendly error messages with colorama formatting
- Connection testing before sending

## Security Considerations

### Files to Protect
- `credentials.json` - OAuth client secrets (in .gitignore)
- `token.json` - OAuth access/refresh tokens (in .gitignore)
- `*.eml` files - Contain message content and proof data

### App Passwords
When using SMTP (not OAuth), users should generate app-specific passwords rather than using their main account password.

## Workflow Integration

### Full Claiming Workflow

1. **Farewell UI**: Claim message and decrypt
2. **Farewell UI**: Export JSON via "Export for Claimer Tool" button
3. **Claimer**: Run `python farewell_claimer.py message.json`
4. **Claimer**: Select email provider, authenticate
5. **Claimer**: Emails sent, .eml files saved
6. **Farewell UI**: Upload .eml, click "Prove Delivery" for each recipient
7. **Farewell UI**: Once all proven, click "Claim Reward"

## Related Projects

- **Farewell UI**: https://github.com/pdroalves/farewell
- **Farewell Core**: https://github.com/pdroalves/farewell-core
- **zk-email**: https://prove.email

## Git Guidelines

- Use conventional commit messages (feat:, fix:, docs:, refactor:, etc.)
- Keep commits focused on a single logical change

## Maintenance Instructions

**IMPORTANT**: When making changes to this codebase:

1. **Update this CLAUDE.md** if CLI interface, functions, or architecture change
2. **Update README.md** if user-facing documentation changes
3. **Update docs/claimer-guide.md** if workflow changes
4. **Run tests** before committing: `pytest`
5. **Test with real email** (create test Gmail account for OAuth testing)
6. **Keep URL references** synchronized with https://farewell.world

### URL Consistency

The project URL appears in:
- `farewell_claimer.py` (email body text and HTML)
- `tests/conftest.py` (test fixtures)
- `README.md`
- `docs/claimer-guide.md`

When updating the URL, search for all occurrences:
```bash
grep -r "farewell.world" .
```

Any AI agent working on this repository should ensure documentation stays synchronized with code changes.
