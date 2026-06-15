from setuptools import setup, find_packages

setup(
    name="indurad_ci",
    version="1",
    packages=find_packages(exclude=("launcher",)),
    install_requires=["requests>=2.25.1"],
)
