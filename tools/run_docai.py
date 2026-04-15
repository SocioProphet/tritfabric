from __future__ import annotations

import argparse
import json

from slate.serve.doc_graph import build_local_doc_pipeline


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("path", help="document or image path")
    args = p.parse_args()

    pipe = build_local_doc_pipeline()
    out = pipe(args.path)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
