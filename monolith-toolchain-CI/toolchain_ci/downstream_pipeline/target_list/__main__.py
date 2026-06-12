import argparse
import os
import pathlib
import shutil
import subprocess
import sys

from .private.target_list import parse_ninja_log
from .private.toolchain_build import ToolchainBuild


def _main():
    """Converts output of 'ninja -t targets all' read from standard input
     to a portable toolchain_build (json) format.

    The output format is defined as follows:

    {
      "version" : 1, # protocol version (this file format)
      "revision" : "<committish>",
      "distro" : "<ROOTFS distribution>",
      "toolchain_version" : "<ROOTFS version>",
      "platform" : "<ROOTFS target platform>",
      "cxx" : "<C++ standard>",
      "build_state" : "SUCCESS|UNSTABLE|FAILURE|ABORTED",
      "targets" : [
        [
            "<target artifact path>",
             "LIBRARY",
              "MODULE|STATIC|SHARED",
               "CXX|C|OTHER"
        ], # for libraries
        [
            "<target artifact path>",
            "EXECUTABLE",
            "CXX|C|OTHER"
        ] # for executables
        [ "<target artifact path>", "OTHER" ] # otherwise
      ]
    }
    """

    parser = argparse.ArgumentParser(
        description=(
            "Converts output of \033[1mninja -t targets all\033[0m"
            " read from standard input "
            "to a portable toolchain_build (json) format."
        )
    )
    _ = parser.parse_args()

    output_path = pathlib.Path(
        f'target-list.{os.environ["CI_JOB_ID"]}.json' if "CI_JOB_ID" in os.environ else "target-list.json"
    )
    distro: str = os.environ["TOOLCHAIN_CI_DISTRO"]
    platform: str = os.environ["TOOLCHAIN_CI_PLATFORM"]
    cxx_standard: str = os.environ["TOOLCHAIN_CI_CMAKE_CXX_STANDARD"]
    revision: str = os.environ["TOOLCHAIN_CI_MONOLITH_REVISION"]
    build_state: str = os.environ["CI_JOB_STATUS"].upper()
    strip_prefix = "monolith/"

    if platform == "local":
        lsb_release_path = shutil.which("lsb_release")

        if not lsb_release_path:
            raise FileNotFoundError("Could not find lsb_release in PATH")

        toolchain_version = subprocess.check_output(
            args=[lsb_release_path, "--description", "--short"], encoding="utf-8"
        )
    else:
        toolchain_version: str = os.environ["TOOLCHAIN_CI_TOOLCHAIN_VERSION"]

    targets = parse_ninja_log(input_file=sys.stdin, strip_prefix=strip_prefix)
    toolchain_build = ToolchainBuild(
        version=2,
        distro=distro,
        toolchain_version=toolchain_version,
        revision=revision,
        cxx=cxx_standard,
        build_state=build_state,
        targets=targets,
        platform=platform,
    )
    toolchain_build.write_json(output_path)


if __name__ == "__main__":
    _main()
