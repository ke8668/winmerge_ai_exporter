"""
redactor.py — Multi-mode "Stripped Patch" context redaction + selective pseudonymization.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

This module implements the core redaction logic for converting diffs to be LLM-safe
while preserving different levels of structural information based on redaction mode:

Redaction Modes:
  - FULL: Pseudonymize everything except keywords. Maximum secrecy.
  - API_SAFE: Keep public API names (PascalCase), return types, parameter types,
    stdlib names. Pseudonymize internal variables, details, magic numbers, strings.
    ⭐ RECOMMENDED for most enterprise codebases.
  - SIGNATURE: Keep only function/class signatures. Hide implementations.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .diff_parser import FileDiff, Hunk


class RedactionMode(Enum):
    """Redaction strategy level."""
    FULL = "full"
    API_SAFE = "api-safe"
    API_SAFE_COMMENTS = "api-safe-comments"  # NEW: Keep all comments intact
    SIGNATURE = "signature"


COLLAPSE_MARKER = "··· [{n} line(s) redacted] ···"

# ───────────────────────────────────────────────────────────────────────────
# Keyword / stdlib allowlist — always preserved
# ───────────────────────────────────────────────────────────────────────────

_KEYWORDS = {
    # control flow
    "if", "else", "elif", "for", "while", "do", "switch", "case", "default",
    "break", "continue", "return", "goto", "try", "catch", "finally", "throw",
    "raise", "except", "with", "as", "yield", "async", "await",
    # declarations
    "def", "class", "struct", "enum", "union", "namespace", "using", "import",
    "from", "include",
    # access / modifiers
    "public", "private", "protected", "static", "const", "constexpr", "final",
    "override", "virtual", "abstract", "sealed", "readonly", "volatile",
    "extern", "inline", "friend", "template", "typename", "auto",
    # types
    "void", "int", "long", "short", "char", "bool", "float", "double",
    "unsigned", "signed", "string", "var", "let", "function", "new", "delete",
    # object/this
    "this", "self", "super", "null", "nullptr", "None",
    # boolean
    "true", "false", "True", "False",
    # logical
    "and", "or", "not", "in", "is", "lambda",
    # OOP
    "interface", "implements", "extends", "instanceof",
    # other
    "pass", "global", "nonlocal", "del", "assert", "package", "module",
    "export", "default", "sizeof", "typedef", "operator", "explicit",
    "mutable", "noexcept", "thread_local",
    # STL / stdlib commonly safe to expose
    "std", "System", "Console", "Math", "Object", "Array", "Promise",
    "vector", "map", "set", "pair", "list", "dict", "tuple",
}

# ───────────────────────────────────────────────────────────────────────────
# API-Safe mode: patterns to preserve (not pseudonymize)
# ───────────────────────────────────────────────────────────────────────────

# PascalCase = typically public API names
_PASCAL_CASE_RE = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b")

# ALL_CAPS_WITH_UNDERSCORES = constants, enums
_CONSTANT_RE = re.compile(r"\b[A-Z_][A-Z0-9_]*\b")

# Common public API prefixes (methods that smell like public API)
_PUBLIC_METHOD_PATTERNS = {
    "Validate", "Check", "Verify", "Lock", "Unlock", "Get", "Set",
    "Create", "Delete", "Remove", "Add", "Update", "Record", "Log",
    "Encrypt", "Decrypt", "Hash", "Sign", "Verify", "Authenticate",
    "Initialize", "Shutdown", "Connect", "Disconnect", "Open", "Close",
    "Load", "Save", "Parse", "Format", "Encode", "Decode",
}

# Type names to always preserve (even if lowercase)
_TYPE_NAMES = {
    "bool", "int", "void", "char", "float", "double", "size_t",
    "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "int8_t", "int16_t", "int32_t", "int64_t",
    "string", "vector", "map", "set", "list", "dict",
    "RequestContext", "Response", "Result", "Status",
}

_IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(\.\d+)?(?:[eE][+-]?\d+)?[fFlLuU]?\b")
_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')

# Comment patterns for various languages (C/C++/C#/Java/Python/JS/TS)
_SINGLE_LINE_COMMENT_RE = re.compile(r"(//.*?$|#.*?$)", re.MULTILINE)  # // or #
_MULTI_LINE_COMMENT_RE = re.compile(r"(/\*.*?\*/|'''.*?'''|\"\"\".*?\"\"\")", re.DOTALL)  # /* */ or ''' or """


def _short_hash(token: str, salt: str) -> str:
    h = hashlib.sha256((salt + "::" + token).encode("utf-8")).hexdigest()
    return h[:6]


def _should_preserve_in_api_safe(token: str) -> bool:
    """Check if token should be preserved in API-Safe mode."""
    if token in _KEYWORDS or token in _TYPE_NAMES:
        return True
    # PascalCase API names
    if _PASCAL_CASE_RE.fullmatch(token):
        return True
    # ALL_CAPS constants
    if _CONSTANT_RE.fullmatch(token) and "_" in token:
        return True
    # Known public method prefixes
    for prefix in _PUBLIC_METHOD_PATTERNS:
        if token.startswith(prefix) and len(token) > len(prefix):
            return True
    return False


def _pseudonymize_line(
    line: str,
    salt: str,
    ident_map: dict[str, str],
    mode: RedactionMode = RedactionMode.API_SAFE,
) -> str:
    """
    Replace string/number literals and (conditionally) identifiers with
    stable, generic placeholders. Behavior depends on redaction mode.
    
    In API_SAFE_COMMENTS mode, all comment text is preserved intact.
    """
    # Preserve diff marker prefix (+/-/space) and leading whitespace
    prefix = ""
    rest = line
    if line[:1] in ("+", "-", " "):
        prefix = line[0]
        rest = line[1:]

    leading_ws_match = re.match(r"^(\s*)", rest)
    leading_ws = leading_ws_match.group(1) if leading_ws_match else ""
    body = rest[len(leading_ws):]

    # === Handle API_SAFE_COMMENTS mode: extract and protect comments ===
    comment_markers = {}
    if mode == RedactionMode.API_SAFE_COMMENTS:
        # Protect single-line comments (// #)
        def _protect_single_comment(m):
            idx = len(comment_markers)
            comment_markers[idx] = m.group(0)
            return f"____COMMENT_{idx}____"
        body = _SINGLE_LINE_COMMENT_RE.sub(_protect_single_comment, body)
        
        # Protect multi-line comments (/* */ ''' """)
        def _protect_multi_comment(m):
            idx = len(comment_markers)
            comment_markers[idx] = m.group(0)
            return f"____COMMENT_{idx}____"
        body = _MULTI_LINE_COMMENT_RE.sub(_protect_multi_comment, body)

    # 1. Strip string literals -> sentinel
    _str_idx = [0]
    def _str_sub(m):
        _str_idx[0] += 1
        return f"____STR_{_str_idx[0]}____"
    body = _STRING_RE.sub(_str_sub, body)

    # 2. Strip numeric literals -> sentinel (but keep 0/1)
    _num_idx = [0]
    def _num_sub(m):
        val = m.group(0)
        if val in ("0", "1", "-1"):
            return val
        _num_idx[0] += 1
        return f"____NUM_{_num_idx[0]}____"
    body = _NUMBER_RE.sub(_num_sub, body)

    # 3. Pseudonymize identifiers (mode-dependent)
    def _ident_sub(m):
        tok = m.group(0)
        if tok in _KEYWORDS:
            return tok
        # Skip sentinel markers
        if tok.startswith("____") and tok.endswith("____"):
            return tok
        # API-Safe: preserve public APIs and types
        if mode in (RedactionMode.API_SAFE, RedactionMode.API_SAFE_COMMENTS) \
           and _should_preserve_in_api_safe(tok):
            return tok
        # Pseudonymize everything else
        if tok not in ident_map:
            ident_map[tok] = f"sym_{_short_hash(tok, salt)}"
        return ident_map[tok]

    body = _IDENT_RE.sub(_ident_sub, body)

    # 4. Replace sentinels with final form
    import re as re_module
    body = re_module.sub(r"____STR_\d+____", '"<str>"', body)
    body = re_module.sub(r"____NUM_\d+____", "<n>", body)
    
    # 5. Restore comments (if API_SAFE_COMMENTS mode)
    if mode == RedactionMode.API_SAFE_COMMENTS:
        for idx, comment in comment_markers.items():
            body = body.replace(f"____COMMENT_{idx}____", comment)

    return prefix + leading_ws + body


# ───────────────────────────────────────────────────────────────────────────
# Hunk stripping
# ───────────────────────────────────────────────────────────────────────────

@dataclass
class StripOptions:
    mode: RedactionMode = RedactionMode.API_SAFE
    core_context: int = 1          # symmetric context lines kept around changes
    collapse_marker: str = COLLAPSE_MARKER


def strip_hunk(
    hunk: "Hunk",
    opts: StripOptions,
    salt: str,
    ident_map: dict[str, str],
) -> list[str]:
    """
    Strip a single hunk according to options.
    Returns a new list of lines with context collapsed and identifiers redacted.
    
    For API_SAFE_COMMENTS mode: even redacted (collapsed) lines will have
    their comments extracted and preserved.
    """
    lines = hunk.lines
    if not lines:
        return []

    header = lines[0] if lines[0].startswith("@@") else None
    body = lines[1:] if header else lines

    n = len(body)
    keep = [False] * n
    for i, l in enumerate(body):
        if l.startswith("+") and not l.startswith("+++"):
            keep[i] = True
        elif l.startswith("-") and not l.startswith("---"):
            keep[i] = True

    # Expand keep mask by core_context on both sides
    if opts.core_context > 0:
        expanded = keep[:]
        for i, k in enumerate(keep):
            if k:
                for d in range(1, opts.core_context + 1):
                    if i - d >= 0:
                        expanded[i - d] = True
                    if i + d < n:
                        expanded[i + d] = True
        keep = expanded

    out: list[str] = []
    if header:
        out.append(header)

    i = 0
    while i < n:
        if keep[i]:
            line = body[i]
            line = _pseudonymize_line(line, salt, ident_map, opts.mode)
            out.append(line)
            i += 1
        else:
            j = i
            while j < n and not keep[j]:
                j += 1
            redacted_count = j - i
            
            # For API_SAFE_COMMENTS: extract comments from redacted lines
            if opts.mode == RedactionMode.API_SAFE_COMMENTS:
                comments = []
                for k in range(i, j):
                    line = body[k]
                    # Extract single-line comments
                    single_match = _SINGLE_LINE_COMMENT_RE.search(line)
                    if single_match:
                        comments.append(single_match.group(0))
                    # Extract multi-line comments
                    multi_match = _MULTI_LINE_COMMENT_RE.search(line)
                    if multi_match:
                        comments.append(multi_match.group(0))
                
                # Add redacted marker with comments
                marker = opts.collapse_marker.format(n=redacted_count)
                if comments:
                    out.append(marker + "  " + "  ".join(comments))
                else:
                    out.append(marker)
            else:
                out.append(opts.collapse_marker.format(n=redacted_count))
            
            i = j

    return out


def strip_file_diff(
    fd: "FileDiff",
    hunks: list["Hunk"],
    opts: StripOptions | None = None,
) -> list[list[str]]:
    """
    Apply stripping to a list of hunks belonging to one file.
    Returns a list of stripped line-lists, one per hunk, in the same order.

    A per-file salt is derived from the file path so the same identifier
    maps to the same placeholder *within* a file (preserving readability)
    but different files get different placeholders for the same name.
    """
    opts = opts or StripOptions()
    salt = fd.path
    ident_map: dict[str, str] = {}

    result = []
    for hunk in hunks:
        result.append(strip_hunk(hunk, opts, salt, ident_map))
    return result
