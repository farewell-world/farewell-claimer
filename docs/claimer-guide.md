# Farewell Claimer Guide

This guide explains how to claim rewards from Farewell messages by proving email delivery using zk-email proofs.

## Overview

When someone passes away and their Farewell messages are released, claimers can:
1. Claim the message on the Farewell UI
2. Decrypt the recipient email and message content
3. Send the message to the recipient via email
4. Prove delivery using zk-email
5. Claim any attached ETH reward

## Prerequisites

- A claimed Farewell message (you must have called `claim()` on the contract)
- Access to an email account (Gmail recommended with OAuth 2.0)
- Python 3.8+ installed
- The [farewell-claimer](https://github.com/pdroalves/farewell-claimer) tool

## Step 1: Install the Claimer Tool

```bash
# Clone the repository
git clone https://github.com/pdroalves/farewell-claimer.git
cd farewell-claimer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Claim and Decrypt the Message

1. Go to the [Farewell UI](https://www.iampedro.com/farewell)
2. Navigate to the **Claim** tab
3. Enter the deceased user's address and message index
4. Click **Mark Deceased** (if not already done)
5. Click **Claim Message**
6. Click **Retrieve & Decrypt**
7. You'll see the decrypted recipient email, message content, and sk share

## Step 3: Export Message Data

After decrypting, you'll see an **"Export for Claimer Tool"** button. Click it to download a JSON file containing:

```json
{
  "recipients": ["recipient@example.com"],
  "contentHash": "0x1234...",
  "message": "The farewell message content...",
  "publicMessage": "Optional public note",
  "skShare": "12345...",
  "subject": "Farewell Message Delivery"
}
```

## Step 4: Set Up Gmail OAuth (Recommended)

For the easiest experience, set up Gmail OAuth 2.0:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Select "Desktop app" as application type
   - Download the JSON file
5. Save the file as `credentials.json` in the farewell-claimer directory

## Step 5: Send the Email

Run the claimer tool with your exported JSON file:

```bash
python farewell_claimer.py farewell-message-0.json
```

The tool will:
1. Ask you to select Gmail (OAuth 2.0)
2. Open a browser for you to authorize (first time only)
3. Show a summary of the message
4. Send the email to the recipient
5. Save the sent email as a `.eml` file
6. Generate a proof structure

### Output Files

After running, you'll find:

```
farewell_proofs_YYYYMMDD_HHMMSS/
├── recipient_1_alice_at_example_com.eml    # Sent email for proof
└── proof_1_alice_at_example_com.json       # Proof data
```

## Step 6: Prove Delivery

1. Return to the Farewell UI
2. In the **Delivery Proof** section, you'll see the recipients
3. For each recipient:
   - Click **Upload .eml**
   - Select the corresponding `.eml` file
   - Click **Prove Delivery**
4. The proof is verified on-chain

## Step 7: Claim the Reward

Once all recipients have been proven:

1. The **Claim Reward** button becomes active
2. Click it to withdraw the attached ETH reward
3. The reward is transferred to your wallet

## Alternative: Interactive Mode

If you don't have an export file, you can run the claimer in interactive mode:

```bash
python farewell_claimer.py
```

You'll be prompted to enter:
- Recipient email(s)
- Content hash
- Message content

## Email Provider Options

### Gmail with OAuth 2.0 (Recommended)
- No password needed
- Most secure option
- Requires one-time setup (see Step 4)

### Gmail with App Password
- Enable 2-Factor Authentication
- Generate an [App Password](https://support.google.com/accounts/answer/185833)

### Other Providers
- **Outlook**: Use regular credentials
- **Yahoo**: Generate an [App Password](https://help.yahoo.com/kb/generate-third-party-passwords-sln15241.html)
- **iCloud**: Generate an [App-Specific Password](https://support.apple.com/en-us/HT204397)

## Troubleshooting

### "Authentication Failed"
- For Gmail, use OAuth 2.0 or an App Password (not your regular password)
- Ensure 2FA is enabled on your account

### "Connection Timeout"
- Check your internet connection
- Some networks block SMTP traffic on port 587

### "Email Not Delivered"
- Check the recipient's spam folder
- Verify the email address is correct

### "Proof Verification Failed"
- Ensure the `.eml` file hasn't been modified
- The recipient email must match exactly what's in the contract

## Security Notes

- **Never commit** `credentials.json` or `token.json` to git
- **Keep `.eml` files secure** - they contain the full email content
- The `skShare` in the export allows decryption - treat it as sensitive

## How ZK-Email Proofs Work

The proof system verifies:
1. The email was signed with a valid DKIM signature (from a trusted provider like Gmail)
2. The recipient (TO field) matches the committed hash stored on-chain
3. The email body contains the correct `Farewell-Hash`

This proves you actually sent the email without revealing the email content to anyone but the verifier.

## Related Documentation

- [farewell-claimer README](https://github.com/pdroalves/farewell-claimer)
- [farewell-core Protocol](https://github.com/pdroalves/farewell-core)
- [zk.email Documentation](https://docs.zk.email/)
