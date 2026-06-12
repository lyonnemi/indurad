"""Parses 'ninja -t targets all' output and provides a list of targets"""
from typing import Optional, Dict, TextIO

from .build_target import BuildTarget


def _parse_library(target_type: str) -> Optional[BuildTarget]:
    tokens = target_type.split("_")

    if len(tokens) < 3:
        return None

    lang = tokens[0] if tokens[0] in ["CXX", "C"] else "OTHER"
    lib_type = tokens[1] if tokens[1] in ["MODULE", "SHARED", "STATIC"] else "OTHER"
    lib = tokens[2]

    if lib != "LIBRARY":
        return None

    return BuildTarget(target_type=lib, target_language=lang, library_type=lib_type)


def _parse_executable(target_type: str) -> Optional[BuildTarget]:
    tokens = target_type.split("_")

    if len(tokens) < 2:
        return None

    lang = tokens[0] if tokens[0] in ["CXX", "C"] else "OTHER"
    exe = tokens[1]

    if exe != "EXECUTABLE":
        return None

    return BuildTarget(target_type=exe, target_language=lang)


def parse_ninja_log(input_file: TextIO, strip_prefix: str = "") -> Dict[str, BuildTarget]:
    """Parses 'ninja -t targets all' output"""

    targets: Dict[str, BuildTarget] = {}
    for line in input_file:
        tokens = line.split(": ")

        if len(tokens) != 2:
            continue

        target_type = tokens[1]

        if target_type == "SYMLINK":
            continue

        target_id = tokens[0] if tokens[0].startswith(strip_prefix) else tokens[0][len(strip_prefix) :]

        parsed_target: Optional[BuildTarget] = None

        if "LIBRARY" in target_type:
            parsed_target = _parse_library(target_type)
        elif "EXECUTABLE" in target_type:
            parsed_target = _parse_executable(target_type)

        targets[target_id] = (
            parsed_target if parsed_target else BuildTarget(target_type="OTHER", target_language="OTHER")
        )

    return targets
