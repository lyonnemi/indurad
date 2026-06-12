"""
Creates a `calvin.conf` with the correct toolchain,
platform and monolith module.
"""
import os
import pathlib
import jinja2


def _main():
    softfs_path = pathlib.Path(os.environ["SOFTFS_SOURCE_PATH"])
    calvin_conf_template_path = softfs_path / "templates/calvin.conf"
    calvin_conf_path = softfs_path / "calvin.conf"

    calvin_conf = jinja2.Template(calvin_conf_template_path.read_text(encoding="utf-8"))
    calvin_conf_path.write_text(
        calvin_conf.render(
            platform=os.environ["TOOLCHAIN_CI_PLATFORM"],
            toolchain_version=os.environ["TOOLCHAIN_CI_TOOLCHAIN_VERSION"],
            monolith_url=(f'git@{os.environ["CI_SERVER_HOST"]}:' f'{os.environ["TOOLCHAIN_CI_MONOLITH_PROJECT"]}.git'),
            monolith_revision=os.environ["TOOLCHAIN_CI_MONOLITH_REVISION"],
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    _main()
