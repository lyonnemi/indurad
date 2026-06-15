# indurad_ci_launcher

This Python package provides the CLI-command `indurad-ci`.

Run the command `indurad-ci` to locally execute Python-based CI jobs
that make use of Python packages in the `./indurad_ci` directory in this repository.

```
usage: indurad-ci [-h] [--run COMMAND] [--clone] [--source]
                  [python-module] ...

Runs scripts with PYTHONPATH set up so that the package indurad_ci is importable.
Use this command to locally run Python-based CI jobs that import packages provided by the indurad-ci repository.

You must run this tool in the root directory of your repository.
./.gitlab-ci.yml must exist and include the indurad-ci repository.
Set the environment variable "$CI_CONFIG_PATH" to configure an alternative path to your Gitlab CI config.

This tool clones the indurad-ci repo to ./.indurad-ci within the repository.
If ./.indurad-ci already exists, the git-revision is compared against the revision specified in .gitlab-ci.yml.
If the revision does not match or the repository contains changes, this tool deletes ./.indurad-ci and clones the correct revision.

positional arguments:
  python-module  execute the entry point of the Python module with PYTHONPATH set so that indurad_ci is importable
  remainder

options:
  -h, --help     show this help message and exit
  --run COMMAND  clone indurad-ci and run COMMAND with the environment variable PYTHONPATH set so that indurad_ci is importable in Python
  --clone        clone indurad-ci to ./.indurad-ci
  --source       clone indurad-ci and print the PYTHONPATH used by --run

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
```

# Maintainer Documentation

## Testing

If you want to test a given revision of the `indurad-ci` launcher, you can set up
your own local test environment as described below:

Install the `indurad_ci_launcher` from a local checkout for testing:

```shell
# install indurad_ci_launcher
git clone git@git.indurad.x:software-qa/indurad-ci.git --branch my-indurad-ci-dev-branch
python3 -m venv venv
source venv/bin/activate
pip install -e indurad-ci/launcher

# run indurad_ci_launcher
indurad-ci --help
```

You are now in a [virtual environment](https://docs.python.org/3/tutorial/venv.html) with `indurad-ci` installed
from the local checkout.


## Release process

* Create an issue in the [CI_Tools](https://redmine.indurad.x/projects/2285/issues) project
* `git pull`
* generate `debian/changelog`: `gbp dch -a -R`
* add and commit the changes: `/usr/share/indurad/dpkg-building/dcr`
* `ARCH=amd64 DIST=bullseye-indurad git-pbuilder update`
* `ARCH=amd64 DIST=bullseye-indurad gbp buildpackage --git-tag`
* Lint package: `lintian -EviI --pedantic --fail-on error,warning,info indurad-ci-launcher_*_amd64.changes`
* `git push`
* `git push --tag`
* Upload the package to the APT-Repository as documented [here](https://git.indurad.x/it/server-ansible/apt-incoming-server-setup/)
