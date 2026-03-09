# CLAUDE.md - CLI Project Guidelines

## Project Vision
A lightweight, high-performance CLI tool for [Purpose]. 
Target Users: Linux/macOS developers who value speed and pipes (`|`).

## Build & Test Commands
- **Install dependencies:** `npm install` (or `go mod tidy` / `pip install`)
- **Build project:** `npm run build`
- **Run locally:** `./bin/run [args]`
- **Test suite:** `npm test`
- **Linting:** `npm run lint`

## CLI Design Principles (CRITICAL)
1. **Silence is Golden:** No "Hello!" or "Welcome!" banners unless `--verbose` is used.
2. **Standard Streams:** Output primary data to `stdout`. Output errors/logs to `stderr`.
3. **Exit Codes:** - `0` for success.
   - `1` for general errors.
   - `127` for command not found.
4. **Composability:** Ensure output can be piped into `grep`, `awk`, or `jq`. 
5. **Speed:** Startup time must be <100ms. Avoid heavy dependency bloat.

## Code Style & Patterns
- **Language:** [e.g., TypeScript / Go / Rust]
- **Error Handling:** Avoid generic try-catch. Use specific error types and clean exit messages.
- **Formatting:** Follow standard [Prettier/gofmt] rules.
- **Documentation:** Every command must have a `-h` / `--help` flag with examples.

## File Structure
- `src/commands/`: Implementation of CLI subcommands.
- `src/utils/`: Shared logic (API calls, file I/O).
- `src/ui/`: Formatting logic (colors via Chalk/Crayons, spinners).

## Version Management

Use github to track all updates. If a bad build is deployed, it needs to be easily reversed by reverting back to the earlier release.

### Search, Don't Checklist
When bumping versions, `grep -rn "old_version"` across the entire repo. JS constants like `CURRENT_VERSION` are easy to miss. The version was stuck at 1.8.1 in one file while everything else was 1.8.6 — nobody noticed.

### Always Create Git Tags
After committing a version bump: `git tag vX.Y.Z && git push origin vX.Y.Z`. Tags make releases discoverable and enable proper GitHub Releases.

### API Keys: Hash, Don't Store
Store SHA-256 hash of API keys, never the raw key. Show the key once on creation. Store a prefix for display purposes. Soft-revoke via timestamp, never hard-delete.
