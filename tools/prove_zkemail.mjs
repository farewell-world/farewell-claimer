#!/usr/bin/env node
/**
 * prove_zkemail.mjs — snarkjs Groth16 prover for Farewell delivery proofs.
 *
 * Called by farewell_claimer.py via FAREWELL_PROVER_CMD. Reads:
 *   - First line of stdin: JSON {"recipient", "contentHash", "publicSignals"}
 *   - Remaining stdin: raw .eml content
 *
 * Outputs JSON to stdout: {pA, pB, pC, publicSignals}
 *
 * Requires circuit artifacts alongside this script:
 *   artifacts/farewell_delivery.wasm
 *   artifacts/farewell_delivery_final.zkey
 */

import { readFileSync, mkdtempSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";
import * as snarkjs from "snarkjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WASM_PATH = join(__dirname, "artifacts", "farewell_delivery.wasm");
const ZKEY_PATH = join(__dirname, "artifacts", "farewell_delivery_final.zkey");

async function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf-8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
  });
}

function fatal(msg) {
  process.stderr.write(`prove_zkemail: ${msg}\n`);
  process.exit(1);
}

async function main() {
  const raw = await readStdin();
  const newlineIdx = raw.indexOf("\n");
  if (newlineIdx === -1) fatal("expected JSON header line + .eml on stdin");

  const headerLine = raw.slice(0, newlineIdx);
  const emlContent = raw.slice(newlineIdx + 1);

  let meta;
  try {
    meta = JSON.parse(headerLine);
  } catch {
    fatal("first line is not valid JSON");
  }

  const { recipient, contentHash, senderAddress } = meta;
  if (!recipient || !contentHash || !senderAddress) {
    fatal("JSON header must contain 'recipient', 'contentHash', and 'senderAddress'");
  }

  // Dynamically import @zk-email/helpers (ESM)
  let generateEmailVerifierInputs, toCircomBigIntBytes;
  try {
    const helpers = await import("@zk-email/helpers");
    generateEmailVerifierInputs = helpers.generateEmailVerifierInputs;
    toCircomBigIntBytes = helpers.toCircomBigIntBytes;
  } catch (e) {
    fatal(`failed to import @zk-email/helpers: ${e.message}`);
  }

  // Generate EmailVerifier inputs from the .eml
  let circuitInputs;
  try {
    circuitInputs = await generateEmailVerifierInputs(
      Buffer.from(emlContent, "utf-8"),
      {
        maxHeadersLength: 1024,
        maxBodyLength: 1024,
        ignoreBodyHashCheck: false,
        // Providers quoted-printable-encode the body and soft-wrap at 76 cols,
        // splitting the 81-char "Farewell-Hash: 0x"+64hex marker. The circuit
        // (removeSoftLineBreaks=1) verifies the DKIM body hash over the raw body
        // but strips soft breaks before marker extraction, so we must supply the
        // decoded body and extract the marker offset from it.
        removeSoftLineBreaks: true,
      },
    );
  } catch (e) {
    fatal(`email verification failed: ${e.message}`);
  }

  // Find recipient email in the header to get its position
  const normalizedRecipient = recipient.toLowerCase().trim();
  const headerStr = Buffer.from(
    circuitInputs.emailHeader.map(Number),
  ).toString("ascii");

  const recipientStart = headerStr.toLowerCase().indexOf(normalizedRecipient);
  if (recipientStart === -1) {
    fatal(
      `recipient "${normalizedRecipient}" not found in email header. ` +
        `The To: header must contain this exact email address.`,
    );
  }

  // Content hash as a field element (strip 0x, parse as BigInt)
  const contentHashBigInt = BigInt(contentHash);

  // Locate the "Farewell-Hash: 0x" marker in the DECODED body (soft line breaks
  // removed). The circuit reads markerLen+64 contiguous bytes from this offset.
  if (!circuitInputs.decodedEmailBodyIn) {
    fatal("decodedEmailBodyIn missing — @zk-email/helpers must support removeSoftLineBreaks");
  }
  const decodedBody = Buffer.from(
    circuitInputs.decodedEmailBodyIn.map(Number),
  ).toString("latin1");
  const markerStart = decodedBody.indexOf("Farewell-Hash: 0x");
  if (markerStart === -1) {
    fatal("'Farewell-Hash: 0x' marker not found in the decoded email body");
  }

  // Build complete circuit input
  const fullInput = {
    ...circuitInputs,
    recipientEmailStart: recipientStart.toString(),
    recipientEmailLength: normalizedRecipient.length.toString(),
    contentHashIn: contentHashBigInt.toString(),
    contentHashMarkerStart: markerStart.toString(),
    senderAddress: BigInt(senderAddress).toString(),
  };

  // Generate the proof with rapidsnark (lean C++ Groth16 prover): compute the
  // witness with the wasm calculator (light — ~hundreds of MB), then prove with
  // rapidsnark, which needs only a few GB vs snarkjs's ~20GB. This keeps proving
  // feasible on modest hardware (a Pi / a normal claimer's laptop).
  // Set RAPIDSNARK_PATH to the rapidsnark `prover` binary (default: "rapidsnark").
  const RAPIDSNARK = process.env.RAPIDSNARK_PATH || "rapidsnark";
  let proof, publicSignals;
  const work = mkdtempSync(join(tmpdir(), "farewell-prove-"));
  try {
    const wtns = join(work, "witness.wtns");
    await snarkjs.wtns.calculate(fullInput, WASM_PATH, wtns);
    const proofPath = join(work, "proof.json");
    const publicPath = join(work, "public.json");
    execFileSync(RAPIDSNARK, [ZKEY_PATH, wtns, proofPath, publicPath], { stdio: "pipe" });
    proof = JSON.parse(readFileSync(proofPath, "utf-8"));
    publicSignals = JSON.parse(readFileSync(publicPath, "utf-8"));
  } catch (e) {
    if (process.env.FAREWELL_USE_SNARKJS === "1") {
      const result = await snarkjs.groth16.fullProve(fullInput, WASM_PATH, ZKEY_PATH);
      proof = result.proof;
      publicSignals = result.publicSignals;
    } else {
      fatal(
        `rapidsnark proving failed — is rapidsnark installed / on PATH (or RAPIDSNARK_PATH set)? ` +
          `Set FAREWELL_USE_SNARKJS=1 to use the heavy JS prover instead. ${e.message}`,
      );
    }
  } finally {
    try { rmSync(work, { recursive: true, force: true }); } catch { /* ignore */ }
  }

  // Format output for Farewell contract (pA/pB/pC as hex strings)
  const output = {
    pA: [proof.pi_a[0], proof.pi_a[1]],
    pB: [
      [proof.pi_b[0][1], proof.pi_b[0][0]],
      [proof.pi_b[1][1], proof.pi_b[1][0]],
    ],
    pC: [proof.pi_c[0], proof.pi_c[1]],
    publicSignals: publicSignals.map((s) => "0x" + BigInt(s).toString(16).padStart(64, "0")),
  };

  process.stdout.write(JSON.stringify(output) + "\n");
}

main().catch((e) => fatal(e.message));
