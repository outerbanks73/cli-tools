from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("getscript")
except PackageNotFoundError:
    __version__ = "0.14.1"  # fallback for editable installs without metadata
