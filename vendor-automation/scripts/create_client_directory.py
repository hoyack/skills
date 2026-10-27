#!/usr/bin/env python3
"""
Thin wrapper around onboard_client.py for Rachel's SOUL.md interface.

Usage:
    create_client_directory.py "Client Name" --group Active
    create_client_directory.py "Client Name" --group Builders
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ONBOARD_SCRIPT = os.path.join(SCRIPT_DIR, "onboard_client.py")


def main():
    if not os.path.exists(ONBOARD_SCRIPT):
        print(f"ERROR: onboard_client.py not found at {ONBOARD_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    # Pass through arguments unchanged
    result = subprocess.run([sys.executable, ONBOARD_SCRIPT] + sys.argv[1:])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
