from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("getscript")
except PackageNotFoundError:
    __version__ = "0.9.1a"  # fallback for editable installs without metadata
