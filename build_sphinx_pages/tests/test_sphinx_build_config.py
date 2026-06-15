import pathlib
import unittest

from indurad_ci.build_sphinx_pages import BuildSphinxPagesError
from indurad_ci.build_sphinx_pages.private.sphinx_build_config import (
    OutputFormat,
    SphinxBuildConfig,
    read_config_from_environment,
    ChapterStart,
    PageNumberPosition,
)

_EXAMPLE_FS = pathlib.Path(__file__).parent / "exclude_pattern_test"


class TestSphinxBuildConfig(unittest.TestCase):
    def test_correct_date_pattern(self) -> None:
        sphinx_build_config = SphinxBuildConfig(
            working_dir_path=_EXAMPLE_FS,
            project_name="project",
            output_format=OutputFormat.HTML,
            _build_tags=(),
            author="author",
            email="email",
            document_version="",
            watermark_text="",
            watermark_scale=1,
            source_path=pathlib.Path(),
            source_repo_path=pathlib.Path(),
            include_paths=(
                ".",
                "exclude_dir1/include4",
                "exclude_dir1/include_dir2",
                "include_dir1/exclude_dir3/include8",
            ),
            exclude_paths=(
                "include_dir1/exclude_dir3",
                "include_dir1/exclude2",
                "exclude_dir1/include_dir2/exclude9",
                "exclude_dir4",
                "exclude1",
            ),
            suppress_issues=(),
            warnings_as_errors=True,
            _custom_requirements=(),
            _autodoc_source_paths=(),
            build_target="",
            config_path=pathlib.Path(),
            entry_point="",
            debug=False,
            kicker="",
            subheading="",
            logo_paths=(),
            repo_structure=(),
            insert_disclaimer=True,
            document_date="2026-01-19",
            chapterstart=ChapterStart.OPENANY,
            even_page_num_pos=PageNumberPosition.R,
            odd_page_num_pos=PageNumberPosition.R,
        )
        read_config_from_environment(sphinx_build_config)

    def test_wrong_date_pattern(self) -> None:
        sphinx_build_config = SphinxBuildConfig(
            working_dir_path=_EXAMPLE_FS,
            project_name="project",
            output_format=OutputFormat.HTML,
            _build_tags=(),
            author="author",
            email="email",
            document_version="",
            watermark_text="",
            watermark_scale=1,
            source_path=pathlib.Path(),
            source_repo_path=pathlib.Path(),
            include_paths=(
                ".",
                "exclude_dir1/include4",
                "exclude_dir1/include_dir2",
                "include_dir1/exclude_dir3/include8",
            ),
            exclude_paths=(
                "include_dir1/exclude_dir3",
                "include_dir1/exclude2",
                "exclude_dir1/include_dir2/exclude9",
                "exclude_dir4",
                "exclude1",
            ),
            suppress_issues=(),
            warnings_as_errors=True,
            _custom_requirements=(),
            _autodoc_source_paths=(),
            build_target="",
            config_path=pathlib.Path(),
            entry_point="",
            debug=False,
            kicker="",
            subheading="",
            logo_paths=(),
            repo_structure=(),
            insert_disclaimer=True,
            document_date="2026:01:19",
            chapterstart=ChapterStart.OPENANY,
            even_page_num_pos=PageNumberPosition.R,
            odd_page_num_pos=PageNumberPosition.R,
        )
        with self.assertRaises(BuildSphinxPagesError) as error:
            read_config_from_environment(sphinx_build_config)
        self.assertEqual(
            str(error.exception),
            "`SPHINX_DOCUMENT_DATE` is not formatted correctly. It needs to be a string, with format `YYYY-MM-DD`.",
        )
