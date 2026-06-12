import pathlib
import unittest

from ..private.target_list import parse_ninja_log
from ..private.build_target import BuildTarget

_ASSETS_PATH = pathlib.Path(__file__).parent / "assets"


class TestTargetList(unittest.TestCase):
    def test_parse_target_list(self):
        ninja_log_path = _ASSETS_PATH / "ninja_test.log"
        with ninja_log_path.open("r", encoding="utf-8") as input_file:
            targets = parse_ninja_log(input_file=input_file, strip_prefix="")

        self.assertEqual(17, len(targets))
        self.assertEqual(
            BuildTarget(target_type="LIBRARY", target_language="CXX", library_type="SHARED"),
            targets.get("tools/radar_idat/irpu/lib/radar/radar_idat/radar/" "libradar-idat-radar.so"),
        )
        self.assertEqual(
            BuildTarget(target_type="EXECUTABLE", target_language="CXX", library_type=None),
            targets.get("tools/radar_idat/radar_idat_irpu"),
        )
