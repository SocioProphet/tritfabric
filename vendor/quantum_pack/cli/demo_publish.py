#!/usr/bin/env python3
import subprocess, os, sys, json, shutil, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT/"out"
NB  = ROOT/"notebooks"/"demo_quantum_lane.ipynb"
PUB = ROOT/"publish"/"publish_proof.sh"

def main():
    # Execute the notebook (requires jupyter/nbconvert)
    if shutil.which("jupyter") is None:
        print("Install jupyter to execute the notebook: pip install jupyter nbconvert", file=sys.stderr)
        return 2
    # run and store the executed notebook next to it
    executed = OUT/"demo_quantum_lane.executed.ipynb"
    cmd = ["jupyter","nbconvert","--to","notebook","--execute","--output",str(executed),str(NB)]
    subprocess.check_call(cmd)
    # Publish to PDF + sign (requires pandoc + openssl)
    key = os.environ.get("TF_SIGN_KEY","signing_key.pem")
    subprocess.check_call([str(PUB), key])
    print("Done. See ./out for PDF and signature.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
