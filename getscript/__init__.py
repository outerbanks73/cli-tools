from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("getscript")
except PackageNotFoundError:
    __version__ = "0.13.0"  # fallback for editable installs without metadata
