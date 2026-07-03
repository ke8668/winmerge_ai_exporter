# Contributing to WinMerge AI Review Exporter

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code and ideas, not the person
- Help others learn and grow
- Report issues privately to maintainers if needed

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Python version)
   - Error messages and logs

### Suggesting Features

1. **Check open issues** for similar suggestions
2. **Create a new issue** with:
   - Clear title describing the feature
   - Use case and motivation
   - Proposed implementation (if applicable)
   - Examples and mockups

### Submitting Changes

#### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd winmerge_ai_exporter

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .
pip install pytest pytest-cov
```

#### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Follow the coding style**
   - Use PEP 8 for Python code
   - Use meaningful variable names
   - Add docstrings to functions and classes
   - Include type hints where possible

3. **Add/update tests**
   ```bash
   # Run existing tests
   pytest tests/
   
   # Write new tests for your changes
   # Tests should be in tests/test_*.py
   ```

4. **Update documentation**
   - Update README.md if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md
   - Add comments to complex logic

5. **Verify all checks pass**
   ```bash
   # Syntax check
   find . -name "*.py" -type f | xargs python -m py_compile
   
   # Run all tests
   pytest tests/ -v
   
   # Check coverage
   pytest tests/ --cov=winmerge_ai_exporter
   ```

#### Committing Changes

This project uses **[Conventional Commits](https://www.conventionalcommits.org/)**.
This is not just a style guide — **the CD pipeline reads your commit messages to
automatically generate the Changelog and the GitHub Release notes**.  If you write
a vague message like `"fixed stuff"`, it will be invisible in the release.

Format:
```
type(scope): subject line (50 chars max)

Optional longer explanation. Wrap at 72 chars.
Explain WHAT changed and WHY, not HOW.

Fixes #123
```

| Type | When to use | Appears in Changelog as |
|---|---|---|
| `feat` | New user-visible feature | ✨ Features |
| `fix` | Bug fix | 🐛 Bug Fixes |
| `perf` | Performance improvement | ⚡ Performance |
| `refactor` | Code change with no behaviour change | ♻️ Refactors |
| `docs` | Documentation only | 📝 Docs |
| `test` | Adding / fixing tests | 🧪 Tests |
| `chore` / `build` / `ci` | Tooling, deps, workflows | 🔧 Chores / CI |

**Breaking changes** — add `!` after the type, or add `BREAKING CHANGE:` in the footer:
```
feat(api)!: remove deprecated strip_file_diff() helper
```

Examples:
```
feat(visualizer): add Mermaid state-machine diagram output

Adds a third diagram type (stateDiagram-v2) to CodeFlowAnalyzer.
Triggered by the existing "📈 Visualize Flow" GUI button.

Closes #57
```

```
fix(code_flow_analyzer): filter linker .map file noise

Lines like "common.o(i.Func) refers to other.o(...)" were being
mis-parsed as function calls, producing meaningless "Call: o()"
nodes in the Mermaid flowchart.

Fixes #61
```

#### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Test results confirming all checks pass

3. **Respond to reviews**
   - Address feedback promptly
   - Explain your reasoning if disagreeing
   - Request changes when ready for re-review

## Development Guidelines

### File Organization

```
winmerge_ai_exporter/
├── __init__.py              # Public API exports
├── diff_parser.py           # Diff parsing
├── redactor.py              # Code redaction
├── exporter.py              # Main export logic
├── code_flow_analyzer.py    # Flow visualization
└── ...

gui/
├── launcher.py              # Main GUI
└── mermaid_panel.py         # Visualization panel

tests/
├── test_*.py                # Test files
└── conftest.py              # Test configuration
```

### Adding New Features

1. **Create a new module** if the feature is complex
2. **Add comprehensive tests**
3. **Update module docstrings** and README
4. **Add to CHANGELOG.md**
5. **Ensure backward compatibility**

### License Headers

All new Python files must include:

```python
"""
module_name.py — Brief description.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Detailed description of what this module does.
"""
```

### Testing Standards

- **Minimum coverage**: 80% for new code
- **Test naming**: `test_<function>_<scenario>`
- **Test structure**: Arrange, Act, Assert (AAA)
- **Fixtures**: Use `conftest.py` for shared fixtures

Example:
```python
def test_redactor_api_safe_mode(self):
    """Test API-safe redaction preserves public APIs."""
    code = "SessionManager::Validate(token)"
    result = redact(code, RedactionMode.API_SAFE)
    
    assert "SessionManager" in result
    assert "Validate" in result
```

## Project Standards

### Version Numbering

```
vMAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes
```

### Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push: `git push && git push --tags`
6. Build: `./build-release.sh`
7. Create GitHub Release with distribution files

## Resources

- **Documentation**: See README.md, REDACTION_MODES.md, etc.
- **Issue Tracker**: GitHub Issues
- **Discussions**: GitHub Discussions
- **License**: MIT License (see LICENSE file)

## Questions?

- Open an issue with the `question` label
- Check existing documentation
- Review past issues and pull requests

## Thank You!

Your contributions help make this project better for everyone. We appreciate your time and effort!

---

**Last Updated**: 2026-06-28  
**License**: MIT - Original Author: Claude (Anthropic)
