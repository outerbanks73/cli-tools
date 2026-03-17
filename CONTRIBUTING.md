# Contributing to getscript

## Prerequisites

- **Python 3.10+**
- **macOS 15.5+** with Xcode CLI tools — required to run Apple Podcasts tests (these are skipped on Linux)
- **fzf** — required for picker/search tests

## Development Setup

```bash
git clone https://github.com/outerbanks73/cli-tools.git
cd cli-tools
pip install -e ".[test]"    # or: pip install -e . && pip install pytest
pytest -v
```

## Project Structure

| File | Purpose |
|------|---------|
| `getscript/cli.py` | Entry point and argument parsing |
| `getscript/detect.py` | URL/ID source detection (Apple vs YouTube) |
| `getscript/apple.py` | Apple Podcasts fetching (macOS, Obj-C helper, AMSMescal/FairPlay) |
| `getscript/youtube.py` | YouTube transcript fetching (proxy, cookies) |
| `getscript/output.py` | Output formatters: text, JSON, Markdown, TTML |
| `getscript/upload.py` | Shared transcript library submission |
| `getscript/config.py` | XDG config/cache, env var handling |
| `getscript/search.py` | YouTube API v3, iTunes Search API backends |
| `getscript/picker.py` | Interactive fzf selection |
| `getscript/progress.py` | TTY-aware progress spinner |
| `getscript/completions.py` | Shell completion generation (bash/zsh/fish) |

## Testing

100 tests across 9 modules. Run with:

```bash
pytest -v
```

CI runs the full matrix: Python 3.10, 3.11, 3.12, 3.13 on both Ubuntu and macOS.

Apple Podcasts tests require macOS and are automatically skipped on Linux. Most external calls are mocked — live network tests are marked and skippable.

## Code Style

- **Lazy imports** for heavy modules — startup must stay under 100ms
- **stderr** for all non-data output (progress, warnings, errors)
- **stdout** is sacred — only transcript data goes there
- Keep it simple. No unnecessary type annotations, no over-abstraction.

## Pull Requests

1. Describe what changed and why
2. Include tests for new behavior
3. One logical change per PR
4. Run `pytest -v` before submitting

## Release Process

1. Bump `version` in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit, tag: `git tag v0.X.Y`
4. Push: `git push origin main --tags`
5. Create a GitHub Release from the tag — CI publishes to PyPI and updates the Homebrew tap automatically

## Bug Reports

Open an issue at [github.com/outerbanks73/cli-tools/issues](https://github.com/outerbanks73/cli-tools/issues) with:

- `getscript --version` output
- OS and Python version
- What you ran and what happened
