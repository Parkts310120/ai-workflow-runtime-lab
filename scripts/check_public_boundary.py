from __future__ import annotations

import re
import subprocess
from pathlib import Path


FORBIDDEN_PATH_NAMES = {".env", "id_rsa", "id_ed25519"}
FORBIDDEN_SUFFIXES = {".pem", ".p12", ".pfx"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?im)^\s*(?:[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY))\s*=\s*['\"]?[A-Za-z0-9_./+=-]{12,}['\"]?\s*$"),
)


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    return [Path(line) for line in output.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if path.name in FORBIDDEN_PATH_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"forbidden sensitive path: {path}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"secret-like material in: {path}")
                break
    if findings:
        print("Public-boundary check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Public-boundary check passed for tracked text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
