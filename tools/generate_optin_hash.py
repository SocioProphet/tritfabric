from __future__ import annotations

import hashlib
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python tools/generate_optin_hash.py <token>")
        raise SystemExit(2)
    token = sys.argv[1]
    print(hashlib.sha256(token.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
