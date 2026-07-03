# Changelog

All notable changes to this project will be documented in this file.

## [1.3.4] — 2026-07-03

### ♻️ Refactors


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Local CD Pipeline**: `deploy-local.sh` / `deploy-local.bat` — one-command
  local Continuous Deployment that mirrors what GitHub Actions does on tag push
  - Stage 1: Runs full CI (`run-ci-locally`) — hard stop on test failure
  - Stage 2: Checks for uncommitted changes before proceeding
  - Stage 3: Computes new version (`patch`/`minor`/`major`/exact) via a `VERSION` file
  - Stage 4: Builds executables (`build-release`), commits the version bump,
    creates an annotated git tag, and optionally pushes (triggering the
    GitHub Actions release build)
- **VERSION file**: Single source of truth for the current version number,
  read by both `build-release.sh/bat` and `deploy-local.sh/bat`
- **CI dependency fix**: `run-ci-locally` now checks for `pytest_cov`
  specifically (not just `pytest`), since `--cov` flags would otherwise
  fail silently on a fresh environment missing only `pytest-cov`
- **GitHub Actions tag sync**: The release `build` job now overwrites
  `VERSION` from the pushed git tag before building, as a safety net for
  tags created without going through `deploy-local`
- **`run-ci-locally.bat` NOPAUSE mode**: Supports being called from other
  scripts (like `deploy-local.bat`) without blocking on an interactive `pause`

### Changed
- `build-release.sh` / `build-release.bat` now read the version from the
  `VERSION` file when present, falling back to a hardcoded default only
  when run standalone without ever having been versioned

## [1.3.0] - 2026-06-28

### Added
- **Code Flow Visualization**: Automatic code architecture analysis and Mermaid diagram generation
  - Supports if/else, switch/case, loops, function calls, events, and try/catch
  - Multiple diagram types: Flowchart, Sequence, State Machine
  - `code_flow_analyzer.py` module with 340+ lines
  - GUI button "📈 Visualize Flow" for one-click visualization
  - 11 new tests for code flow analysis
- **Mermaid Panel**: GUI component for displaying and managing Mermaid diagrams
- **Git Integration**: Complete project version control setup
- **Distribution Guide**: Comprehensive guide for packaging and distribution
- **.gitignore**: Standard Python project ignore rules
- **CHANGELOG.md**: Version history tracking

### Changed
- Enhanced `launcher.py` with new visualization button and handler methods
- Improved GUI button layout for better usability

### Testing
- Total test count increased from 130 to 141 tests
- All new tests for code flow analyzer passing
- 100% syntax validation across all modules

## [1.2.2] - 2026-06-25

### Added
- **Code Redaction Complete**: All 13 Python files now have MIT License headers
- **Licensing Infrastructure**:
  - LICENSE file (MIT License)
  - Comprehensive license headers in all source files
  - Copyright information (2024-2025) properly attributed
- **Distribution Tools**:
  - `build-release.sh` for Linux/macOS one-click packaging
  - `build-release.bat` for Windows one-click packaging
  - Automated PyInstaller integration
  - DISTRIBUTION_GUIDE.md with detailed release instructions

### Fixed
- TclError resolution in GUI (proper parameter placement in pack calls)
- Duplicate docstring issues in multiple files
- Import order and module initialization

### Documentation
- Added DISTRIBUTION_GUIDE.md (1500+ lines)
- Added SECRET_ALGORITHMS.md for sensitive code handling
- Complete API documentation for all modules

## [1.2.1] - 2026-06-23

### Fixed
- AttributeError: '_on_mode_change' method now properly defined
- GUI event handler registration fixed

## [1.2.0] - 2026-06-22

### Added
- **api-safe-comments Mode**: Preserves all comments while hiding internals
- **Redacted Line Comment Preservation**: Comments in collapsed lines are extracted and shown
- **Drag-and-Drop Improvements**:
  - Ctrl+V paste support for all entry widgets
  - Clear visual labels indicating paste capability
  - Improved UX with emoji icons (📄 📋 📁)

### Changed
- Refactored `strip_hunk()` to intelligently extract comments from redacted lines
- Updated GUI labels for clarity
- Improved status messages and user feedback

## [1.1.0] - 2026-06-20

### Added
- **API-Safe Redaction Mode**: Hide internals while preserving public APIs and types
- **Four Redaction Modes**:
  - `full`: Hide everything except keywords
  - `api-safe`: Keep public APIs and types (recommended)
  - `api-safe-comments`: Keep public APIs and all comments
  - `signature`: Show only function signatures
- **Comprehensive Redaction Modes Guide**: REDACTION_MODES.md

### Changed
- Enhanced GUI with mode dropdown selector
- Improved risk scoring algorithm
- Better token estimation

## [1.0.0] - 2026-05-15

### Added
- Initial release of WinMerge AI Review Exporter
- Core functionality:
  - Parse unified diff format
  - Risk scoring for code changes
  - Architecture-level analysis
  - Token count estimation
  - Markdown report generation
- GUI interface with Tkinter
- CLI interface with argparse
- Complete test suite (130 tests)
- MIT License

---

## Guidelines for Contributors

### Versioning
- **MAJOR version** when you make incompatible API changes
- **MINOR version** when you add functionality in a backwards compatible manner
- **PATCH version** when you make backwards compatible bug fixes

### Commit Messages
Follow the format:
```
type(scope): subject

body

footer
```

Types: feat, fix, docs, style, refactor, perf, test, chore

### Before Committing
- [ ] All tests pass (`pytest tests/`)
- [ ] No syntax errors (`python -m py_compile`)
- [ ] Documentation updated
- [ ] License headers on new files
- [ ] Git commits are atomic and well-documented

---

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Build release: `./build-release.sh`
6. Upload to GitHub Releases
7. Announce release

---

**Format Inspiration**: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

Last Updated: 2026-06-28