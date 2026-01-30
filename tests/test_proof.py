"""
Tests for proof generation functionality.
"""

import pytest
import json
from pathlib import Path

import farewell_claimer
from farewell_claimer import generate_proof_data, save_proof


class TestGenerateProofData:
    """Tests for proof data generation."""

    def test_generate_proof_returns_dict(self, sample_eml_content):
        """Test that generate_proof_data returns a dictionary."""
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash="0x1234567890abcdef"
        )
        assert isinstance(proof, dict)

    def test_generate_proof_has_required_fields(self, sample_eml_content):
        """Test proof has all required fields for smart contract."""
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash="0x1234567890abcdef"
        )

        assert "pA" in proof
        assert "pB" in proof
        assert "pC" in proof
        assert "publicSignals" in proof

    def test_generate_proof_pa_format(self, sample_eml_content):
        """Test pA has correct format."""
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash="0x1234"
        )

        assert isinstance(proof["pA"], list)
        assert len(proof["pA"]) == 2

    def test_generate_proof_pb_format(self, sample_eml_content):
        """Test pB has correct format (2x2 matrix)."""
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash="0x1234"
        )

        assert isinstance(proof["pB"], list)
        assert len(proof["pB"]) == 2
        assert len(proof["pB"][0]) == 2
        assert len(proof["pB"][1]) == 2

    def test_generate_proof_pc_format(self, sample_eml_content):
        """Test pC has correct format."""
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash="0x1234"
        )

        assert isinstance(proof["pC"], list)
        assert len(proof["pC"]) == 2

    def test_generate_proof_public_signals_format(self, sample_eml_content):
        """Test publicSignals has correct format."""
        content_hash = "0x1234567890abcdef"
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash=content_hash
        )

        signals = proof["publicSignals"]
        assert isinstance(signals, list)
        assert len(signals) == 3
        # [0] = recipient email hash
        # [1] = DKIM pubkey hash
        # [2] = content hash
        assert signals[2] == content_hash

    def test_generate_proof_recipient_hash_is_hex(self, sample_eml_content):
        """Test recipient hash is a valid hex string."""
        proof = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="recipient@test.com",
            content_hash="0x1234"
        )

        recipient_hash = proof["publicSignals"][0]
        assert recipient_hash.startswith("0x")
        assert len(recipient_hash) == 66  # 0x + 64 hex chars

    def test_generate_proof_normalizes_email(self, sample_eml_content):
        """Test that email is normalized (lowercase, stripped)."""
        proof1 = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="Test@Example.COM  ",
            content_hash="0x1234"
        )
        proof2 = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="test@example.com",
            content_hash="0x1234"
        )

        # Same normalized email should produce same hash
        assert proof1["publicSignals"][0] == proof2["publicSignals"][0]

    def test_generate_proof_different_emails_different_hash(self, sample_eml_content):
        """Test that different emails produce different hashes."""
        proof1 = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="user1@test.com",
            content_hash="0x1234"
        )
        proof2 = generate_proof_data(
            eml_content=sample_eml_content,
            recipient_email="user2@test.com",
            content_hash="0x1234"
        )

        assert proof1["publicSignals"][0] != proof2["publicSignals"][0]


class TestSaveProof:
    """Tests for proof saving functionality."""

    def test_save_proof_creates_file(self, temp_output_dir):
        """Test that save_proof creates a JSON file."""
        proof = {
            "pA": ["0x1", "0x2"],
            "pB": [["0x3", "0x4"], ["0x5", "0x6"]],
            "pC": ["0x7", "0x8"],
            "publicSignals": ["0xa", "0xb", "0xc"]
        }

        filepath = save_proof(proof, "test_proof.json", temp_output_dir)

        assert filepath.endswith("test_proof.json")
        assert Path(filepath).exists()

    def test_save_proof_valid_json(self, temp_output_dir):
        """Test that saved proof is valid JSON."""
        proof = {
            "pA": ["0x1", "0x2"],
            "pB": [["0x3", "0x4"], ["0x5", "0x6"]],
            "pC": ["0x7", "0x8"],
            "publicSignals": ["0xa", "0xb", "0xc"]
        }

        filepath = save_proof(proof, "test_proof.json", temp_output_dir)

        with open(filepath, 'r') as f:
            loaded_proof = json.load(f)

        assert loaded_proof == proof

    def test_save_proof_creates_directory(self, tmp_path):
        """Test that save_proof creates output directory if needed."""
        new_dir = str(tmp_path / "new_proofs_dir")
        proof = {"test": "data"}

        filepath = save_proof(proof, "test.json", new_dir)

        assert Path(filepath).exists()

    def test_save_proof_formatted_json(self, temp_output_dir):
        """Test that saved JSON is properly formatted (indented)."""
        proof = {"pA": ["0x1", "0x2"]}

        filepath = save_proof(proof, "formatted.json", temp_output_dir)

        with open(filepath, 'r') as f:
            content = f.read()

        # Indented JSON should have newlines
        assert "\n" in content


class TestProofIntegration:
    """Integration tests for proof generation workflow."""

    def test_full_proof_workflow(self, sample_eml_content, temp_output_dir):
        """Test complete proof generation workflow."""
        recipient = "recipient@test.com"
        content_hash = "0x" + "ab" * 32

        # Generate proof
        proof = generate_proof_data(sample_eml_content, recipient, content_hash)

        # Save proof
        filepath = save_proof(proof, "integration_test.json", temp_output_dir)

        # Load and verify
        with open(filepath, 'r') as f:
            loaded = json.load(f)

        assert loaded["publicSignals"][2] == content_hash
        assert loaded["pA"] == proof["pA"]
        assert loaded["pB"] == proof["pB"]
        assert loaded["pC"] == proof["pC"]
