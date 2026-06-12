## `compatibility_report.py`

Script to produce a compatibility report from files created by `target_list.py`.
Outputs a HTML report and a JSON file for archival purposes.
See `compatiblity_report.py -h` for usage information.
Run `python3 -m unittest discover` to run tests.

### Python Dependencies

 - `jinja2` for proper HTML report generation

### Format of the output JSON

* `.version` is the version of the archive format
* `.targets` show various target types
  * `LIBRARY` are static/shared libraries
  * `EXECUTABLES` are executable applications
  * `OTHER` are everything else
* `.configurations.targets` contains a list of indices into `.targets`
  * if a target index is in this list, then this target was build for the configuration

```json
{
  "version" : 1,
  "revision" : "<committish>",
  "targets" : [
    [ "<target artefact path>", "LIBRARY", "MODULE|STATIC|SHARED", "CXX|C|OTHER" ],
    [ "<target artefact path>", "EXECUTABLE", "CXX|C|OTHER" ],
    [ "<target artefact path>", "OTHER" ]
  ],
  "configurations": [
     {
      "distro" : "<ROOTFS distribution>",
      "toolchain_version" : "<ROOTFS version>",
      "platform" : "<platform identifier>",
      "cxx" : "<C++ standard>",
      "targets" : [
        "<target artefact index>",
        "<target artefact index>"
      ]
     },
     {
      "distro" : "<ROOTFS distribution>",
      "toolchain_version" : "<ROOTFS version>",
      "platform" : "<platform identifier>",
      "cxx" : "<C++ standard>",
      "targets" : [
        "<target artefact index>",
        "<target artefact index>"
      ]
     }
  ]
}
```
