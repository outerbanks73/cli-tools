# CLAUDE.md - getscript CLI Guidelines

## Project Vision
A lightweight CLI for fetching transcripts from Apple Podcasts.
Target Users: macOS developers who value speed and pipes (`|`).

## Build & Test Commands
- **Install (editable):** `pip install -e .`
- **Run locally:** `getscript [URL|ID] [options]` or just `getscript` for interactive mode
- **Test suite:** `pytest` or `pytest -v`
- **Requires:** Python 3.10+, macOS 15.5+ with Xcode CLI tools for transcript fetching

## Interactive Mode
Running `getscript` with no arguments enters interactive mode:
1. Prompts for a search term
2. Shows up to 20 results
3. Lets user pick by number
4. Prompts for filename, saves to `~/Documents/` as `.txt`

## CLI Design Principles (CRITICAL)
1. **Silence is Golden:** No "Hello!" or "Welcome!" banners unless `--verbose` is used.
2. **Standard Streams:** Output primary data to `stdout`. Output errors/logs to `stderr`.
3. **Exit Codes:**
   - `0` for success.
   - `1` for general errors.
   - `2` for usage errors.
   - `130` for user interrupt.
4. **Composability:** Ensure output can be piped into `grep`, `awk`, or `jq`.
5. **Speed:** Startup time must be <100ms. Use lazy imports for heavy modules.

## Code Style & Patterns
- **Language:** Python 3.10+
- **Error Handling:** Avoid generic try-catch. Use specific error types and clean exit messages.
- **Documentation:** Every command must have a `-h` / `--help` flag with examples.

## File Structure
- `getscript/cli.py`: Entry point and argument parsing.
- `getscript/detect.py`: Apple Podcasts URL/ID detection.
- `getscript/apple.py`: Apple Podcasts fetching (macOS only, Obj-C).
- `getscript/output.py`: Output formatters (text, JSON, Markdown, TTML).
- `getscript/config.py`: XDG config/cache handling.
- `getscript/search.py`: iTunes Search API backend.
- `getscript/picker.py`: Interactive fzf selection.
- `getscript/progress.py`: TTY-aware progress spinner.
- `getscript/completions.py`: Shell completion generation.
- `getscript/upload.py`: Upload to shared Voxly transcript pool (Supabase Edge Function).

## Version Management

Version is defined in `pyproject.toml` and read at runtime via `importlib.metadata`.

Use GitHub to track all updates. If a bad build is deployed, revert to the earlier release.

### Search, Don't Checklist
When bumping versions, `grep -rn "old_version"` across the entire repo.

### Always Create Git Tags
After committing a version bump: `git tag vX.Y.Z && git push origin vX.Y.Z`. Tags make releases discoverable and enable proper GitHub Releases.

### API Keys: Hash, Don't Store
Store SHA-256 hash of API keys, never the raw key. Show the key once on creation. Store a prefix for display purposes. Soft-revoke via timestamp, never hard-delete.
