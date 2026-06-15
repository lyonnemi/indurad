import pathlib
import os
import sys

if __name__ == "__main__":
    pathlib.Path(sys.argv[1]).write_text(os.environ["PYTHONPATH"])
