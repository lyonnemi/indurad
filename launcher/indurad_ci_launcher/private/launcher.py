#!/usr/bin/env python3
import argparse
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import textwrap
import yaml

_GITLAB_CI_CONFIG_PATH = pathlib.Path(os.environ.get("CI_CONFIG_PATH", ".gitlab-ci.yml"))
_INDURAD_CI_PROJECT = "software-qa/indurad-ci"
_INDURAD_CI_CHECKOUT = pathlib.Path(".indurad-ci")


# ignore "!reference" constructors when parsing .gitlab-ci.yml
yaml.add_multi_constructor("\x21", lambda loader, suffix, node: None, Loader=yaml.SafeLoader)


def _determine_indurad_ci_revision(
    working_directory: pathlib.Path,
) -> str | None:
    try:
        with (working_directory / _GITLAB_CI_CONFIG_PATH).open("r") as input_file:
            gitlab_ci_config = yaml.safe_load(stream=input_file)
    except FileNotFoundError:
        return None

    if not isinstance(gitlab_ci_config, dict) or "include" not in gitlab_ci_config:
        return None

    includes = gitlab_ci_config["include"]

    if not isinstance(includes, list):
        return None

    for include in includes:
        if (
            not isinstance(include, dict)
            or "project" not in include
            or include["project"] != _INDURAD_CI_PROJECT
            or "ref" not in include
        ):
            continue

        ref = include["ref"]
        if isinstance(ref, str):
            return ref

    return None


def run_git(
    command_line: list[str],
    print_error_message: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    git_path = shutil.which("git")

    if not git_path:
        raise FileNotFoundError("Could not find git in PATH")

    full_command_line = [
        git_path,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test",
    ] + command_line

    def _print_failure(stderr: str | bytes) -> None:
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        print(
            shlex.join(full_command_line),
            "failed with the following output:",
            stderr,
            file=sys.stderr,
            sep="\n",
        )

    try:
        completed_process = subprocess.run(
            full_command_line,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=check,
        )
    except subprocess.CalledProcessError as err:
        if print_error_message:
            _print_failure(stderr=err.stderr)
        raise

    if completed_process.returncode != 0 and print_error_message:
        _print_failure(stderr=completed_process.stderr)

    return completed_process


def _pull_indurad_ci(
    checkout_path: pathlib.Path,
) -> None:
    run_git(
        command_line=["-C", str(checkout_path), "pull"],
        print_error_message=False,
    )


def _git_clone_indurad_ci(
    remote_url: str,
    revision: str,
    target_path: pathlib.Path,
) -> bool:
    clone_process = run_git(["clone", remote_url, str(target_path)])

    if clone_process.returncode != 0:
        return False

    reset_process = run_git(["-C", str(target_path), "checkout", revision])

    return reset_process.returncode == 0


def _determine_checked_out_indurad_ci_revision(
    checkout_path: pathlib.Path,
) -> str | None:
    branch_name = run_git(
        command_line=["-C", str(checkout_path), "branch", "--show-current"],
        print_error_message=False,
    ).stdout.rstrip("\n")

    if branch_name:
        return branch_name

    return run_git(
        command_line=["-C", str(checkout_path), "rev-parse", "HEAD"],
        print_error_message=False,
    ).stdout.rstrip("\n")


def _check_git_checkout_contains_changes(
    checkout_path: pathlib.Path,
) -> bool:
    contains_uncommitted_changes = bool(
        run_git(
            command_line=["-C", str(checkout_path), "status", "--porcelain"],
            print_error_message=False,
        ).stdout
    )
    contains_committed_changes = bool(
        run_git(
            command_line=[
                "-C",
                str(checkout_path),
                "log",
                "@{upstream}..",
            ],
            print_error_message=False,
        ).stdout
    )
    return contains_uncommitted_changes or contains_committed_changes


def _ensure_indurad_ci_checkout_exists(
    working_directory: pathlib.Path,
    clone_remote_override: str | None,
) -> bool:
    indurad_ci_revision = _determine_indurad_ci_revision(
        working_directory=working_directory,
    )

    if not indurad_ci_revision:
        print(
            "Could not determine the indurad-ci revision " "from your Gitlab CI config.",
            f"Please make sure {working_directory / _GITLAB_CI_CONFIG_PATH} "
            "exists and includes the indurad-ci repository.",
            sep="\n",
            file=sys.stderr,
        )
        return False

    checkout_path = working_directory / _INDURAD_CI_CHECKOUT
    if checkout_path.exists():
        _pull_indurad_ci(
            checkout_path=checkout_path,
        )
        checked_out_revision = _determine_checked_out_indurad_ci_revision(
            checkout_path=checkout_path,
        )
        checkout_contains_changes = _check_git_checkout_contains_changes(
            checkout_path=checkout_path,
        )

        if indurad_ci_revision == checked_out_revision and not checkout_contains_changes:
            return True

        print(
            f"{checkout_path.absolute()} "
            "contains changes or the wrong revision, "
            "deleting and recreating the checkout"
        )
        shutil.rmtree(checkout_path)

    clone_succeeded = _git_clone_indurad_ci(
        revision=indurad_ci_revision,
        target_path=checkout_path,
        remote_url=(clone_remote_override or f"git@git.indurad.x:{_INDURAD_CI_PROJECT}.git"),
    )

    return clone_succeeded


def _get_run_environment_variables(
    working_directory: pathlib.Path,
) -> dict[str, str]:
    old_python_path_suffix = f':{os.environ["PYTHONPATH"]}' if "PYTHONPATH" in os.environ else ""
    return {"PYTHONPATH": f"{(working_directory / _INDURAD_CI_CHECKOUT).absolute()}" f"{old_python_path_suffix}"}


def _run_command(
    command_line: list[str],
    working_directory: pathlib.Path,
) -> int:
    environment = os.environ.copy()
    additional_environment = _get_run_environment_variables(
        working_directory=working_directory,
    )
    environment.update(additional_environment)

    executable_path = shutil.which(command_line[0])

    if not executable_path:
        raise FileNotFoundError(f"Could not find {command_line[0]} in PATH")

    resolved_command_line = [executable_path] + command_line[1:]
    print(
        " ".join(f"{key}={value}" for key, value in additional_environment.items()),
        shlex.join(resolved_command_line),
    )
    completed_process = subprocess.run(
        resolved_command_line,
        env=environment,
        cwd=working_directory,
    )
    return completed_process.returncode


def _make_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="indurad-ci",
        description=(
            "Runs scripts with PYTHONPATH set up "
            "so that the package indurad_ci is importable.\n"
            "Use this command to locally run Python-based CI jobs that import "
            "packages provided by the indurad-ci repository.\n"
            "\n"
            "You must run this tool in the root "
            "directory of your repository.\n"
            "./.gitlab-ci.yml must exist and "
            "include the indurad-ci repository.\n"
            'Set the environment variable "$CI_CONFIG_PATH" to configure an '
            "alternative path to your Gitlab CI config.\n"
            "\n"
            "This tool clones the indurad-ci repo to ./.indurad-ci "
            "within the repository.\n"
            "If ./.indurad-ci already exists, the git-revision is compared "
            "against the revision specified in .gitlab-ci.yml.\n"
            "If the revision does not match or "
            "the repository contains changes, "
            "this tool deletes ./.indurad-ci and clones the correct revision."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent(
            """
            examples:

            # clone indurad-ci and run the given command with PYTHONPATH set
            indurad-ci --run python3 -m ci.jobs.build_cpp20

            # short version for the run-command above
            indurad-ci ci.jobs.build_cpp20

            # clone indurad-ci to ./.indurad-ci
            indurad-ci --clone

            # clone indurad-ci and source the PYTHONPATH
            eval $(indurad-ci --source)

            configuration:

            Set CI_CONFIG_PATH to the relative path to your GitLab CI
            configuration file if your project uses a different confiugration
            than the default ("./.gitlab-ci.yml").
            """
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--run",
        type=str,
        metavar="COMMAND",
        help=(
            "clone indurad-ci and run COMMAND "
            "with the environment variable PYTHONPATH set "
            "so that indurad_ci is importable in Python"
        ),
    )
    group.add_argument(
        "--clone",
        action="store_true",
        help=(f"clone indurad-ci to ./{_INDURAD_CI_CHECKOUT}"),
    )
    group.add_argument(
        "--source",
        action="store_true",
        help=("clone indurad-ci and print the PYTHONPATH used by --run"),
    )
    group.add_argument(
        "python-module",
        type=str,
        nargs="?",
        help=("execute the entry point of the Python module " "with PYTHONPATH set so that indurad_ci is importable"),
    )
    parser.add_argument("remainder", nargs=argparse.REMAINDER)
    return parser


def entry_point(
    arguments: list[str] | None = None,
    working_directory: pathlib.Path = pathlib.Path.cwd(),
    clone_remote_override: str | None = None,
) -> int:
    parser = _make_argument_parser()
    args = parser.parse_args(arguments or sys.argv[1:])

    python_module: str | None = getattr(args, "python-module")
    source_mode: bool = args.source
    command_to_run: str | None = args.run
    remainder: list[str] = args.remainder

    checkout_success = _ensure_indurad_ci_checkout_exists(
        working_directory=working_directory,
        clone_remote_override=clone_remote_override,
    )

    if not checkout_success:
        return False

    exit_code: int = 0

    if command_to_run is not None:
        exit_code = _run_command(
            command_line=shlex.split(command_to_run),
            working_directory=working_directory,
        )
    elif python_module is not None:
        exit_code = _run_command(
            command_line=["python3", "-m"] + [python_module] + remainder,
            working_directory=working_directory,
        )
    elif source_mode:
        run_environment = _get_run_environment_variables(
            working_directory=working_directory,
        )
        for key, value in run_environment.items():
            print(f"export {key}={shlex.quote(value)}")

    return exit_code
