"""
Contains config-variables usable by custom CI Jobs.
If used in projects we recommend to edit this
config-file instead of the actual CI job scripts.
"""

import os
import pathlib
import typing

from indurad_ci.cmake import (
    BuildConfiguration,
    CmakeCxxStandard,
    CmakeBuildType,
)

# project specific constants
ARTIFACTS_PATH = pathlib.Path("checkout")
BUILD_PATH = pathlib.Path("build")
# path to calvin.conf for your specific project
SOFTFS_SOURCE_PATH = pathlib.Path("iRPU-Central")
# target you want to run/test
RUN_TARGETS = ("localdev",)
TEST_TARGET = ("project-test-all",)


def _num_jobs() -> int:
    num_usable_cpus = len(os.sched_getaffinity(0))
    return int(typing.cast(str, os.environ.get("JOBS"))) if "JOBS" in os.environ else num_usable_cpus


NUM_PARALLEL_JOBS: int = _num_jobs()
# Base config usable by `cmake_build`
BASE_BUILD_CONFIG = (
    BuildConfiguration()
    .with_parallel_jobs(num_parallel_jobs=NUM_PARALLEL_JOBS)
    .with_build_type(build_type=CmakeBuildType.RELWITHDEBINFO)
    .with_cxx_standard(cxx_standard=CmakeCxxStandard.CPP17)
    # .with_cmake_variable(name="MyName", value="MyValue")
)
