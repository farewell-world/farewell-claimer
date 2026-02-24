"""
Tests for proof generation functionality.
"""

import pytest
import json
from pathlib import Path

import farewell_claimer
from farewell_claimer import (
    generate_proof_data,
    save_proof,
    build_delivery_proof,
    validate_delivery_proof,
)


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


class TestBuildDeliveryProof:
    """Tests for building the DeliveryProofJson envelope."""

    def test_build_delivery_proof_structure(self, sample_eml_content):
        """Built proof has correct top-level structure."""
        proof = generate_proof_data(sample_eml_content, "a@b.com", "0x1234")
        dp = build_delivery_proof(
            owner="0xabc",
            message_index=3,
            recipient_proofs=[{"recipientIndex": 0, "proof": proof, "email": "a@b.com"}],
        )
        assert dp["type"] == "farewell-delivery-proof"
        assert dp["version"] == 1
        assert dp["owner"] == "0xabc"
        assert dp["messageIndex"] == 3
        assert len(dp["recipients"]) == 1
        assert "metadata" in dp

    def test_build_delivery_proof_multi_recipient(self, sample_eml_content):
        """Multi-recipient proofs are all included."""
        entries = []
        for i, email in enumerate(["a@b.com", "c@d.com", "e@f.com"]):
            proof = generate_proof_data(sample_eml_content, email, "0xaabb")
            entries.append({"recipientIndex": i, "proof": proof, "email": email})

        dp = build_delivery_proof("0x1", 0, entries)
        assert len(dp["recipients"]) == 3
        # Each recipient has distinct email hash
        hashes = [r["proof"]["publicSignals"][0] for r in dp["recipients"]]
        assert len(set(hashes)) == 3


class TestValidateDeliveryProof:
    """Tests for delivery proof validation."""

    def _make_valid_proof(self):
        """Helper: build a minimal valid delivery proof."""
        return {
            "version": 1,
            "type": "farewell-delivery-proof",
            "owner": "0xabc",
            "messageIndex": 0,
            "recipients": [
                {
                    "recipientIndex": 0,
                    "proof": {
                        "pA": ["0x0", "0x0"],
                        "pB": [["0x0", "0x0"], ["0x0", "0x0"]],
                        "pC": ["0x0", "0x0"],
                        "publicSignals": ["0xa", "0xb", "0xc"],
                    },
                    "email": "test@example.com",
                }
            ],
        }

    def test_valid_proof_passes(self):
        """A well-formed proof validates successfully."""
        ok, err = validate_delivery_proof(self._make_valid_proof())
        assert ok is True
        assert err == ""

    def test_wrong_type_fails(self):
        """Wrong type field is rejected."""
        p = self._make_valid_proof()
        p["type"] = "something-else"
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "type" in err

    def test_missing_type_fails(self):
        """Missing type field is rejected."""
        p = self._make_valid_proof()
        del p["type"]
        ok, err = validate_delivery_proof(p)
        assert ok is False

    def test_missing_owner_fails(self):
        """Missing owner is rejected."""
        p = self._make_valid_proof()
        del p["owner"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "owner" in err

    def test_missing_message_index_fails(self):
        """Missing messageIndex is rejected."""
        p = self._make_valid_proof()
        del p["messageIndex"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "messageIndex" in err

    def test_empty_recipients_fails(self):
        """Empty recipients array is rejected."""
        p = self._make_valid_proof()
        p["recipients"] = []
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "recipients" in err

    def test_missing_recipient_index_fails(self):
        """Recipient without recipientIndex is rejected."""
        p = self._make_valid_proof()
        del p["recipients"][0]["recipientIndex"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "recipientIndex" in err

    def test_missing_proof_object_fails(self):
        """Recipient without proof object is rejected."""
        p = self._make_valid_proof()
        del p["recipients"][0]["proof"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "proof" in err

    def test_missing_public_signals_fails(self):
        """Proof without publicSignals is rejected."""
        p = self._make_valid_proof()
        del p["recipients"][0]["proof"]["publicSignals"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "publicSignals" in err

    def test_too_few_public_signals_fails(self):
        """publicSignals with fewer than 3 elements is rejected."""
        p = self._make_valid_proof()
        p["recipients"][0]["proof"]["publicSignals"] = ["0xa", "0xb"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "publicSignals" in err

    def test_wrong_pa_shape_fails(self):
        """pA with wrong array length is rejected."""
        p = self._make_valid_proof()
        p["recipients"][0]["proof"]["pA"] = ["0x0"]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "pA" in err

    def test_wrong_pb_shape_fails(self):
        """pB that is not a 2x2 matrix is rejected."""
        p = self._make_valid_proof()
        p["recipients"][0]["proof"]["pB"] = [["0x0"], ["0x0", "0x0"]]
        ok, err = validate_delivery_proof(p)
        assert ok is False
        assert "pB" in err

    def test_not_a_dict_fails(self):
        """Non-dict input is rejected."""
        ok, err = validate_delivery_proof("not a dict")
        assert ok is False

    def test_content_hash_passthrough(self, sample_eml_content):
        """Content hash from claim package appears in publicSignals[2]."""
        content_hash = "0x" + "ff" * 32
        proof = generate_proof_data(sample_eml_content, "a@b.com", content_hash)
        dp = build_delivery_proof("0x1", 0, [
            {"recipientIndex": 0, "proof": proof, "email": "a@b.com"}
        ])
        ok, _ = validate_delivery_proof(dp)
        assert ok is True
        assert dp["recipients"][0]["proof"]["publicSignals"][2] == content_hash


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

    def test_full_delivery_proof_workflow(self, sample_eml_content, temp_output_dir):
        """Test complete delivery proof build → validate → save → reload workflow."""
        recipients = ["alice@test.com", "bob@test.com"]
        content_hash = "0x" + "cd" * 32

        # Generate per-recipient proofs
        entries = []
        for i, email in enumerate(recipients):
            proof = generate_proof_data(sample_eml_content, email, content_hash)
            entries.append({"recipientIndex": i, "proof": proof, "email": email})

        # Build envelope
        dp = build_delivery_proof("0xDEAD", 5, entries)

        # Validate
        ok, err = validate_delivery_proof(dp)
        assert ok is True, err

        # Save and reload
        filepath = save_proof(dp, "delivery-proof.json", temp_output_dir)
        with open(filepath, 'r') as f:
            loaded = json.load(f)

        assert loaded["type"] == "farewell-delivery-proof"
        assert loaded["owner"] == "0xDEAD"
        assert loaded["messageIndex"] == 5
        assert len(loaded["recipients"]) == 2
        for i, r in enumerate(loaded["recipients"]):
            assert r["recipientIndex"] == i
            assert r["proof"]["publicSignals"][2] == content_hash
