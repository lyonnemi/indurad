from setuptools import setup, find_packages

setup(
    name="indurad_ci_launcher",
    version="1.0.0",
    install_requires=[
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "indurad-ci = indurad_ci_launcher.private.launcher:entry_point",
        ]
    },
    packages=find_packages(),
    include_package_data=True,
)
