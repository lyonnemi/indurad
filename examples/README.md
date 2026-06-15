# Examples

[[_TOC_]]

## Overview

This subfolder contains an example of how to write your own CI job and
integrate it into your project.

## Setup

To integrate this example into your own project, follow these steps:

* Copy the content of [my_project/](examples/my_project/) into your project root folder.
  * If your project already contains a `.gitlab-ci.yml`, these must be merged.
* Edit `ci/config/config.py` to fit your project structure (e.g., `SOFTFS_SOURCE_PATH`
  might need to be adjusted to your current structure). Note that defined path variables
  are relative to the project root folder.
* This example integrates the three ci jobs `build_softfs`, `run_project_main`
  and `run_project_tests`. If those jobs are sufficient for your needs, you can stop here.
* For editing or adding user-defined jobs, please refer to the next section.

## Custom Jobs

To create your own CI job, create a script called `my_own_job.py` under `ci/jobs`.
Note that there must be an empty `__init__.py` file next to it.

Add the following lines of code to your job script. These line will enable you to
call the script locally, using the `indurad-launcher`.

```py
def _main():
    context: BuildContext = my_own_job()
    sys.exit(0 if context.success else 1)


if __name__ == '__main__':
    _main()
```
Now you can start implementing the `my_own_job()` function and customize the job to your needs.
It is recommended to utilize `BuildContext` as return value, which helps tracking the
success or errors within your job. [run_project_main](../indurad_ci/run_project_main/__main__.py)
provides an example on how to properly integrate this class with your job script.

Useful includes that will equip your job with the full might of `indurad-ci` are:

```py
from indurad_ci.build_context import BuildContext
from indurad_ci.build_softfs import build_softfs, BuildSoftfsResults
from indurad_ci.cmake import cmake_build, CmakeBuildStage
```
A usages example is given by [run_project_tests](../indurad_ci/run_project_tests/__main__.py).

To integrate `my_own_job` into your pipeline just copy this example into your
`.gitlab-ci.yml`.
```commandline
'🕵 Run custom jobs':
  extends: '.indurad-ci-scripts'
  needs: [ ]
  script:
    - 'python3 -m ci.jobs.my_own_job.py'
```

### Configuration

It is recommended to use a common configuration file for all custom job scripts
located under `ci/config/config.py`. This way there is no need to redefine
the same variable in different jobs and makes it less prone to error while
making the configuration accessible to all developers.

To access variables or functions defined in `ci/config/config.py` integrate them in
`ci/config/__init__.py`.

Predefined variables are:

```py
# project specific constants
ARTIFACTS_PATH = pathlib.Path('checkout')
BUILD_PATH = pathlib.Path('build')
# path to calvin.conf for your specific project
SOFTFS_SOURCE_PATH = pathlib.Path('iRPU-Central')
# target you want to run/test
RUN_TARGETS = ('localdev',)
TEST_TARGET = ('project-test-all',)
# Base config usable by `cmake_build`
BASE_BUILD_CONFIG = (
  ....
)
```

To include them in `my_own_job.py` copy and adapt the snippet below:

```python
from ci.config.config import (
    BUILD_PATH,
    SOFTFS_SOURCE_PATH,
    RUN_TARGETS,
)
```

### Local testing

To test your newly written job locally, you can use the `indurad-ci` command line
tool. The following command checks out the `indurad-ci` revision referenced in your
`.gitlab-ci.yml`, configures the `PYTHONPATH` environment variable and then calls
Python with the provided Python module in one step:

```commandline
indurad-ci ci.jobs.my_own_job
```

NOTE: Your locally run job might fail because of missing python packages. Thankfully you can just
install them via `pip` while your `venv` is active.
