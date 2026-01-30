# Farewell Claimer
<p align="center"> <img src="assets/farewell-logo.png" alt="Farewell Logo" width="600"/> </p>

A command-line tool for Farewell message claimers to send emails to recipients and generate zk-email proofs for claiming rewards on the Farewell smart contract.

## Overview

When someone passes away and their Farewell messages are released, claimers need to:
1. Send the decrypted message content to the intended recipients
2. Prove that they sent the emails using zk-email proofs
3. Submit the proofs to the smart contract to claim any attached rewards

This tool automates steps 1 and 2, making it easy to deliver farewell messages and generate the necessary proofs.

## Features

- **Interactive CLI** with colorful, user-friendly interface
- **Multiple email providers** - Gmail, Outlook, Yahoo, iCloud, Zoho, or custom SMTP
- **Batch sending** - Send to multiple recipients in one session
- **Automatic .eml export** - Saves sent emails for proof generation
- **Proof generation** - Creates zk-email proof structures for the blockchain
- **Connection testing** - Validates SMTP credentials before sending

## Installation

### Requirements

- Python 3.8+

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

### Basic Usage

```bash
python farewell_claimer.py
```

The tool will guide you through:

1. **SMTP Configuration** - Select your email provider and enter credentials
2. **Message Information** - Enter recipient emails, content hash, and message
3. **Send & Prove** - Emails are sent and proofs are generated automatically

### Email Provider Setup

#### Gmail
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

1. Go to the [Farewell claim page](https://www.iampedro.com/farewell)
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
├── farewell_claimer.py      # Main CLI application
├── tests/
│   ├── __init__.py
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

- **Credentials**: Never commit your email credentials. The tool prompts for them each time.
- **App Passwords**: Always use app-specific passwords instead of your main account password.
- **Proof Files**: The generated `.eml` and `.json` files contain sensitive information. Keep them secure.

## How It Works

### Email Sending

1. Connects to your SMTP server with TLS encryption
2. Creates a properly formatted email with the Farewell-Hash embedded
3. Sends the email and captures the raw message for proof generation

### Proof Generation

1. Extracts email metadata and content
2. Computes the recipient email hash (matching the smart contract's commitment)
3. Creates a proof structure compatible with the Farewell Groth16 verifier

### ZK-Email Integration

The generated proofs are designed to work with zk-email circuits that verify:
- The email was signed with a valid DKIM signature
- The recipient (TO field) matches the committed hash
- The email body contains the correct Farewell-Hash

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

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Farewell Protocol](https://github.com/pdroalves/farewell) - Main application
- [Farewell Core](https://github.com/pdroalves/farewell-core) - Smart contracts

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
