#!/usr/bin/env python3
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


def run_mermaid(args: list[str], sandbox: bool) -> tuple[bool, str, str]:
    """
    Runs mermaid with or without sandbox
    @param args: Arguments for mermaid
    @param sandbox: Whether the sandbox is to be used
    @return: True if the process succeeded, the content of stdout, and the content of stderr
    """
    mermaid_cli = "node_modules/@mermaid-js/mermaid-cli/src/cli.js"

    if sandbox:
        p = subprocess.run([mermaid_cli, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "puppeteer-config.json"
            config.write_text(
                textwrap.dedent(
                    """\
                    {
                      "args": ["--no-sandbox"]
                    }
                    """
                )
            )
            p = subprocess.run(
                [mermaid_cli, "-p", config, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    return p.returncode == 0, p.stdout.decode(), p.stderr.decode()


def main() -> None:
    # indurad uses Docker in GitLab CI. In Docker, Chromium needs the `--no-sandbox` flag
    args = sys.argv[1:]

    if os.environ.get("GITLAB_CI") or pathlib.Path("/.dockerenv").exists():
        success, stdout, stderr = run_mermaid(args, sandbox=False)
    else:
        success, stdout, stderr = run_mermaid(args, sandbox=True)
        if not success and "--no-sandbox" in stderr:
            success, stdout, stderr = run_mermaid(args, sandbox=False)
    print(stdout)
    if not success:
        print(stderr)
        sys.exit(-1)


if __name__ == "__main__":
    main()
