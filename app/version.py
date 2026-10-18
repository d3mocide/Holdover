"""The running version, from the installed package metadata (pyproject.toml is the source)."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("holdover")
except PackageNotFoundError:  # running from a bare checkout without installing
    __version__ = "dev"
