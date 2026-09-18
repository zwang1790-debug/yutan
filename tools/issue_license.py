"""Offline seller tool for issuing YTR1 licenses.

Usage:
  python tools/issue_license.py --device-hash HASH --plan personal_monthly --days 30
Private key is read from LICENSE_PRIVATE_KEY (base64 raw Ed25519 key) or
--private-key-file. Never place it in the application package.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.license_issuer_core import issue_license


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-hash", required=True)
    parser.add_argument("--plan", default="personal_monthly")
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--version", default="2.1.1")
    parser.add_argument("--private-key-file")
    args = parser.parse_args()
    try:
        code, _payload = issue_license(
            device_hash=args.device_hash,
            plan=args.plan,
            days=args.days,
            version=args.version,
            private_key_path=args.private_key_file,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(code)


if __name__ == "__main__":
    main()
