# Farewell Claimer

[![CI](https://github.com/farewell-world/farewell-claimer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/farewell-world/farewell-claimer/actions/workflows/ci.yml?query=branch%3Amain)

<p align="center"> <img src="assets/farewell-logo.png" alt="Farewell Logo" width="600"/> </p>

A command-line tool for Farewell message claimers to send emails to recipients and generate zk-email proofs for claiming rewards on the Farewell smart contract.

## Overview

When someone passes away and their Farewell messages are released, claimers need to:
1. Send the decrypted message content to the intended recipients
2. Prove that they sent the emails using zk-email proofs
3. Submit the proofs to the smart contract to claim any attached rewards

This tool automates steps 1 and 2, making it easy to deliver farewell messages and generate the necessary proofs.

**Full Guide**: See [docs/claimer-guide.md](docs/claimer-guide.md) for step-by-step instructions.

## Features

- **Interactive CLI** with colorful, user-friendly interface
- **Gmail OAuth 2.0** - No password needed! Just authorize via browser (recommended)
- **Multiple email providers** - Gmail, Outlook, Yahoo, iCloud, Zoho, or custom SMTP
- **Batch sending** - Send to multiple recipients in one session
- **Automatic .eml export** - Saves sent emails for proof generation
- **Claim package decryption** - Decrypts AES-128-GCM encrypted messages from the Farewell UI
- **Proof generation** - Creates zk-email proof structures for the blockchain
- **Connection testing** - Validates SMTP credentials before sending

## Installation

### Requirements

- Python 3.8+
- `cryptography` package (for decrypting claim packages)

### Quick Start (Recommended)

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Alternative: Install with pipx

If you just want to run the tool without setting up a dev environment:

```bash
pipx install colorama
python3 farewell_claimer.py
```

### Why a virtual environment?

Modern Linux distributions (Ubuntu 23.04+, Debian 12+, Fedora 38+) use PEP 668 to prevent system-wide pip installations, which protects your system Python. Using a virtual environment is the recommended approach.

## Usage

### From Farewell UI Export (Recommended)

1. Claim a message on the [Farewell UI](https://farewell.world)
2. Download the claim package JSON
3. Run the tool with the exported file:

```bash
python farewell_claimer.py claim-package.json
```

4. When prompted, enter the off-chain secret (`s'`) that the message recipient should have received from the sender
5. The tool decrypts the message and guides you through sending it

### Interactive Mode

If you don't have an export file, run without arguments:

```bash
python farewell_claimer.py
```

The tool will guide you through:

1. **SMTP Configuration** - Select your email provider and enter credentials
2. **Message Information** - Enter recipient emails, content hash, and message
3. **Send & Prove** - Emails are sent and proofs are generated automatically

### JSON File Formats

The tool supports two input formats:

**Claim package** (from Farewell UI — contains encrypted message, requires `s'` to decrypt):

```json
{
  "type": "farewell-claim-package",
  "recipients": ["alice@example.com"],
  "skShare": "0x...",
  "encryptedPayload": "0x...",
  "contentHash": "0x1234...",
  "subject": "Farewell Message Delivery"
}
```

**Direct format** (pre-decrypted message, for manual use):

```json
{
  "recipients": ["alice@example.com", "bob@example.com"],
  "contentHash": "0x1234567890abcdef...",
  "message": "Your farewell message content...",
  "subject": "Optional custom subject"
}
```

### Email Provider Setup

#### Gmail with OAuth 2.0 (Recommended)

The easiest and most secure option - no password required!

**One-time setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Select "Desktop app" as application type
   - Download the JSON file
5. Save the file as `credentials.json` in the farewell-claimer directory

**Usage:**
- Run the tool and select "Gmail (OAuth 2.0)"
- A browser window opens for you to sign in
- Grant permission to send emails
- Done! Token is saved for future use

#### Gmail with App Password (Alternative)
- Enable 2-Factor Authentication
- Generate an [App Password](https://support.google.com/accounts/answer/185833)
- Use the App Password instead of your regular password

#### Outlook/Hotmail
- Use your regular credentials
- May need to enable "Less secure apps" in account settings

#### Yahoo
- Generate an [App Password](https://help.yahoo.com/kb/generate-third-party-passwords-sln15241.html)

#### iCloud
- Generate an [App-Specific Password](https://support.apple.com/en-us/HT204397)

### Output Files

After running, the tool creates a timestamped directory with:

```
farewell_proofs_YYYYMMDD_HHMMSS/
├── recipient_1_user_at_example_com.eml    # Email for proof generation
├── proof_1_user_at_example_com.json       # Proof data for blockchain
├── recipient_2_another_at_example_com.eml
└── proof_2_another_at_example_com.json
```

### Claiming Rewards

1. Go to the [Farewell claim page](https://farewell.world)
2. Navigate to the message you claimed
3. For each recipient:
   - Upload the corresponding `.eml` file
   - Click "Prove Delivery"
4. Once all recipients are proven, click "Claim Reward"

## Development

### Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install dev dependencies
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Make sure venv is activated
source .venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=farewell_claimer --cov-report=term-missing

# Run specific test file
pytest tests/test_email.py -v
```

### Project Structure

```
farewell-claimer/
├── farewell_claimer.py      # Main CLI application (single file)
├── docs/
│   └── claimer-guide.md     # Step-by-step user guide
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_smtp.py         # SMTP configuration tests
│   ├── test_email.py        # Email creation/sending tests
│   ├── test_proof.py        # Proof generation tests
│   └── test_ui.py           # UI helper tests
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
├── pytest.ini              # Pytest configuration
└── README.md
```

## Security Considerations

- **OAuth Credentials**: Never commit `credentials.json` or `token.json` - they are in `.gitignore`
- **App Passwords**: If using SMTP, use app-specific passwords instead of your main account password
- **Proof Files**: The generated `.eml` and `.json` files contain sensitive information. Keep them secure.

## How It Works

### Claim Package Decryption

When loading a claim package from the Farewell UI, the tool:

1. Detects the `"type": "farewell-claim-package"` format
2. Prompts for `s'` (the off-chain secret the recipient should have)
3. Reconstructs the AES key: `sk = skShare XOR s'`
4. Decrypts the AES-128-GCM encrypted payload to recover the original message

This is the [key sharing scheme](https://github.com/farewell-world/farewell-core#key-sharing-scheme) used by Farewell — the message can only be decrypted by combining the on-chain key share with the off-chain secret.

### Email Sending

1. Connects to your SMTP server with TLS encryption
2. Creates a properly formatted email with the `Farewell-Hash` embedded in the body
3. Sends the email and captures the raw message for proof generation

### Proof Generation

1. Extracts email metadata and content
2. Computes the recipient email hash (matching the smart contract's commitment)
3. Creates a proof structure compatible with the Farewell Groth16 verifier

### ZK-Email Integration

The generated proofs are designed to work with zk-email circuits that verify:
- The email was signed with a valid DKIM signature
- The recipient (TO field) matches the committed hash
- The email body contains the correct `Farewell-Hash`

## Troubleshooting

### Authentication Failed
- Verify your email and password
- For Gmail/Outlook/Yahoo, use an App Password instead of your regular password
- Check that 2FA is enabled if required

### Connection Timeout
- Check your internet connection
- Verify the SMTP server and port are correct
- Some networks block outgoing SMTP traffic

### Email Not Delivered
- Check the recipient's spam folder
- Verify the recipient email address is correct
- Some email providers have rate limits

## Disclaimer

This is a personal project by the author, who is employed by [Zama](https://www.zama.ai/). Farewell is **not** an official Zama product, and Zama bears no responsibility for its development, maintenance, or use. All views and code are the author's own.

## License

BSD 3-Clause License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Farewell Protocol](https://farewell.world) - Main application
- [Farewell Core](https://github.com/farewell-world/farewell-core) - Smart contracts

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
