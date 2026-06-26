#!/usr/bin/env python3
"""Crypto & Hash Tools — hashid, openssl, gpg, rsactftool, xortool, quipquip"""

import subprocess, json, sys, shutil, hashlib, base64
from pathlib import Path
from typing import List, Dict, Optional

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/crypto")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str], timeout: int = 300, capture: bool = True) -> dict:
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout)
        return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr, "rc": r.returncode}
    except FileNotFoundError:
        return {"ok": False, "error": f"Tool not found: {cmd[0]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout"}

def _which(tool: str) -> bool: return shutil.which(tool) is not None

# ── Hash Identification ──────────────────────────────────────────────────
def hashid_identify(hash_str: str) -> dict:
    return _run(["hashid", "-mj", hash_str])

def hash_identifier(hash_str: str) -> dict:
    return _run(["hash-identifier"], input_data=hash_str + "\n", timeout=15)

# ── Hash Generation ──────────────────────────────────────────────────────
def hash_generate(data: str, algo: str = "sha256") -> Optional[str]:
    h = hashlib.new(algo, data.encode())
    return h.hexdigest()

def hash_file(filepath: str, algo: str = "sha256") -> Optional[str]:
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ── OpenSSL ──────────────────────────────────────────────────────────────
def openssl_encrypt(filepath: str, password: str, algo: str = "aes-256-cbc",
                    outfile: str = "") -> dict:
    path = outfile or filepath + ".enc"
    return _run(["openssl", "enc", f"-{algo}", "-salt", "-pbkdf2",
                 "-in", filepath, "-out", path, "-pass", f"pass:{password}"])

def openssl_decrypt(filepath: str, password: str, algo: str = "aes-256-cbc",
                    outfile: str = "") -> dict:
    path = outfile or filepath.replace(".enc", ".dec")
    return _run(["openssl", "enc", f"-{algo}", "-d", "-pbkdf2",
                 "-in", filepath, "-out", path, "-pass", f"pass:{password}"])

def openssl_hash(filepath: str, algo: str = "sha256") -> dict:
    return _run(["openssl", "dgst", f"-{algo}", filepath])

# ── GPG ──────────────────────────────────────────────────────────────────
def gpg_encrypt(filepath: str, recipient: str, output: str = "") -> dict:
    path = output or filepath + ".gpg"
    return _run(["gpg", "--encrypt", "--recipient", recipient, "--output", path, filepath])

def gpg_decrypt(filepath: str, output: str = "") -> dict:
    path = output or filepath.replace(".gpg", ".dec")
    return _run(["gpg", "--decrypt", "--output", path, filepath])

def gpg_import_key(keyfile: str) -> dict:
    return _run(["gpg", "--import", keyfile])

# ── RSA Attacks ──────────────────────────────────────────────────────────
def rsactftool_attack(pubkey: str, attack: str = "auto") -> dict:
    """Attack RSA public key. attacks: auto, fermat, wiener, smallq, etc."""
    return _run(["python3", "-m", "RsaCtfTool", "--publickey", pubkey,
                 "--attack", attack], timeout=300)

def rsactftool_from_n_e(n: str, e: str = "65537") -> dict:
    return _run(["python3", "-m", "RsaCtfTool", "-n", n, "-e", e], timeout=300)

# ── XOR Analysis ─────────────────────────────────────────────────────────
def xortool_analyze(filepath: str, max_key_len: int = 32) -> dict:
    return _run(["xortool", "-l", str(max_key_len), "-c", "20", filepath])

def xortool_decode(filepath: str, key: str) -> dict:
    """Decode XOR-obfuscated file with known key."""
    return _run(["xortool", "-x", filepath, key])

# ── Base64 / Encoding ────────────────────────────────────────────────────
def base64_encode(data: str) -> str:
    return base64.b64encode(data.encode()).decode()

def base64_decode(data: str) -> str:
    return base64.b64decode(data).decode()

def xor_encrypt(data: str, key: str) -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def rot13(data: str) -> str:
    return data.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))

# ── Caesar / Cipher Tools ────────────────────────────────────────────────
def caesar_decrypt(ciphertext: str, shift: int = 0) -> List[str]:
    """Brute-force all Caesar shifts if shift=0."""
    results = []
    shifts = range(1, 26) if shift == 0 else [shift]
    for s in shifts:
        plain = "".join(
            chr((ord(c) - 65 - s) % 26 + 65) if c.isupper() else
            chr((ord(c) - 97 - s) % 26 + 97) if c.islower() else c
            for c in ciphertext
        )
        results.append({"shift": s, "plaintext": plain})
    return results

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "hashid":   print(json.dumps(hashid_identify(sys.argv[2])))
    elif cmd == "hash":   print(hash_generate(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "sha256"))
    elif cmd == "base64e": print(base64_encode(sys.argv[2]))
    elif cmd == "base64d": print(base64_decode(sys.argv[2]))
    elif cmd == "caesar": print(json.dumps(caesar_decrypt(sys.argv[2])))
    elif cmd == "rsa":    print(json.dumps(rsactftool_attack(sys.argv[2])))
    else: print("Commands: hashid | hash | base64e | base64d | caesar | rsa")
