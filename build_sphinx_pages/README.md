---
only: no_build
---

# Sphinx Build Maintainer Documentation

This document contains information for maintainers of `indurad_ci.build_sphinx_pages`.
If you are not changing the source code of `indurad_ci`, you don't need to read this.

## Updating Tests

If you change the result of the tests in `.tests/documentation_projects/`, you can use the 
`update_doc.py` script.
This will build the html version of `basic_documentation`, and use the result to update the `j2` 
files in `basic_documentation_expected_artifacts`. You should look at the result to determine
whether the changes match your expectation!
