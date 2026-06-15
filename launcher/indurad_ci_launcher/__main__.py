import sys
from indurad_ci_launcher.private.launcher import entry_point

if __name__ == "__main__":
    exit_code = entry_point()
    sys.exit(exit_code)
