"""Generate an Ed25519 key pair for the seller's offline license issuer."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def enc(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="license-keys")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_value = private_key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_value = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    (output / "private.key").write_text(enc(private_value) + "\n", encoding="ascii")
    (output / "public.key").write_text(enc(public_value) + "\n", encoding="ascii")
    print(f"公钥：{output / 'public.key'}")
    print(f"私钥：{output / 'private.key'}（仅保存在卖家授权环境，不要打包或提交）")


if __name__ == "__main__":
    main()
