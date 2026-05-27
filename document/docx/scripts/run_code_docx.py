from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import json
from pathlib import Path


# ── Environment ───────────────────────────────────────────────────

_npm_root_cache: str | None = None


def _global_npm_root() -> str:
    """沙箱已预装 node/npm，结果缓存避免重复 spawn 子进程。"""
    global _npm_root_cache
    if _npm_root_cache is not None:
        return _npm_root_cache

    node_path = os.environ.get("NODE_PATH", "").strip()
    if node_path:
        first = node_path.split(os.pathsep)[0]
        if os.path.isdir(first):
            _npm_root_cache = first
            return first

    try:
        result = subprocess.run(
            ["npm", "root", "-g"],
            check=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        root = result.stdout.strip()
        if root and os.path.isdir(root):
            _npm_root_cache = root
            return root
    except (subprocess.CalledProcessError, OSError):
        pass

    raise RuntimeError(
        "无法获取 npm 全局 node_modules 路径。"
        "请确认 npm 已安装，或手动设置环境变量 NODE_PATH。"
    )


def _with_global_node_path(env: dict[str, str] | None = None) -> dict[str, str]:
    merged = dict(env or os.environ)
    global_root = _global_npm_root()
    existing = merged.get("NODE_PATH", "").strip()
    merged["NODE_PATH"] = (
        f"{global_root}{os.pathsep}{existing}" if existing else global_root
    )
    return merged


def _backup_path(script: Path) -> Path:
    return script.with_suffix(".js.bak")


# ── Error formatting ─────────────────────────────────────────────

def _extract_error_context(script: Path, stderr: str) -> str:
    """Parse Node.js error output and attach source context around the failing line."""
    lines = script.read_text(encoding="utf-8").splitlines()

    match = re.search(re.escape(str(script)) + r":(\d+)", stderr)
    if not match:
        match = re.search(re.escape(script.name) + r":(\d+)", stderr)
    if not match:
        return stderr

    error_line = int(match.group(1))
    start = max(0, error_line - 4)
    end = min(len(lines), error_line + 3)

    ctx = []
    for i in range(start, end):
        marker = " >>>" if i == error_line - 1 else "    "
        ctx.append(f"{marker} {i + 1:4d} | {lines[i]}")

    return f"{stderr}\n\n── 出错位置（第 {error_line} 行附近）──\n" + "\n".join(ctx)


# ── Auto-fix (silent corrections before any checks) ──────────────

_UNICODE_REPLACEMENTS: list[tuple[str, str, str]] = [
    ("\u201c", '"', "左双引号"),   # "
    ("\u201d", '"', "右双引号"),   # "
    ("\u2018", "'", "左单引号"),   # '
    ("\u2019", "'", "右单引号"),   # '
    ("\uff08", "(", "全角左括号"), # （
    ("\uff09", ")", "全角右括号"), # ）
    ("\uff1b", ";", "全角分号"),   # ；
    ("\uff5b", "{", "全角左花括号"), # ｛
    ("\uff5d", "}", "全角右花括号"), # ｝
]


def _find_string_ranges(source: str) -> list[tuple[int, int]]:
    """Return [(start, end), ...] character-index ranges of JS string literals.

    Recognises single-quoted, double-quoted, and template-literal strings
    with backslash escape handling.  Also skips ``//`` and ``/* */`` comments
    so that characters inside comments are treated as code (harmless to fix).
    """
    ranges: list[tuple[int, int]] = []
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            j = source.find("\n", i)
            i = j + 1 if j != -1 else n
            continue
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            j = source.find("*/", i + 2)
            i = j + 2 if j != -1 else n
            continue
        if ch in ("'", '"', "`"):
            start = i
            i += 1
            while i < n:
                if source[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if source[i] == ch:
                    i += 1
                    break
                i += 1
            ranges.append((start, i))
            continue
        i += 1
    return ranges


def _replace_outside_strings(
    source: str,
    bad_char: str,
    good_char: str,
    string_ranges: list[tuple[int, int]],
) -> tuple[str, int]:
    """Replace *bad_char* → *good_char* only in code regions (outside string literals).

    All replacements are single-char → single-char so positions stay stable.
    Returns ``(new_source, replacement_count)``.
    """
    parts: list[str] = []
    count = 0
    last = 0
    for start, end in string_ranges:
        seg = source[last:start]
        c = seg.count(bad_char)
        if c:
            seg = seg.replace(bad_char, good_char)
            count += c
        parts.append(seg)
        parts.append(source[start:end])
        last = end
    seg = source[last:]
    c = seg.count(bad_char)
    if c:
        seg = seg.replace(bad_char, good_char)
        count += c
    parts.append(seg)
    return "".join(parts), count


_TS_ASSERTION_RE = re.compile(
    r"\s+as\s+(?:any|unknown|string|number|boolean|object|never|const)\b"
)


def _strip_ts_assertions(source: str) -> tuple[str, list[str]]:
    """Strip common TypeScript assertions from generated JS.

    LLM output occasionally leaks TS-only syntax like:
      verticalAlign: 'center' as any,
    which is invalid in plain Node.js execution.
    """
    lines = source.splitlines()
    fixes: list[str] = []
    changed = False

    for idx, line in enumerate(lines):
        if " as " not in line:
            continue

        ranges = _find_string_ranges(line)
        parts: list[str] = []
        last = 0
        count = 0

        for m in _TS_ASSERTION_RE.finditer(line):
            if any(start <= m.start() < end for start, end in ranges):
                continue
            parts.append(line[last:m.start()])
            last = m.end()
            count += 1

        if not count:
            continue

        parts.append(line[last:])
        lines[idx] = "".join(parts)
        fixes.append(f"第 {idx + 1} 行: 移除 TypeScript 断言 ({count} 处)")
        changed = True

    if not changed:
        return source, []

    suffix = "\n" if source.endswith("\n") else ""
    return "\n".join(lines) + suffix, fixes


def _index_in_ranges(index: int, ranges: list[tuple[int, int]]) -> bool:
    """Return True if *index* falls inside any ``(start, end)`` string range."""
    return any(start <= index < end for start, end in ranges)


def _fix_broken_arrow_suffix(line: str) -> str:
    """Strip stray closing tokens after an arrow at end-of-line.

    LLM output sometimes produces:
      ``cols.map((c, i) => } }``
    when it meant a multi-line arrow body:
      ``cols.map((c, i) =>``

    We only touch cases where everything after ``=>`` is whitespace plus
    closing tokens. Legitimate inline bodies like ``x => ({ a: 1 })`` are
    left untouched because they contain real code after the arrow.
    """
    match = re.search(r"=>\s*(?:[}\]),;]+(?:\s+[}\]),;]+)*)\s*$", line)
    if not match:
        return line

    if _index_in_ranges(match.start(), _find_string_ranges(line)):
        return line

    trailing_ws = re.search(r"\s*$", line)
    suffix = trailing_ws.group(0) if trailing_ws else ""
    return line[: match.start()] + "=>" + suffix


def _auto_fix_unicode(script: Path) -> list[str]:
    """Replace smart quotes and fullwidth punctuation with ASCII equivalents.

    Fullwidth characters in JS **code** are always wrong (common LLM output
    artifact), but fullwidth characters inside string literals may be
    intentional (e.g. Chinese parentheses ``（）`` in text content).
    Replacements therefore only apply outside JS string literals.

    Returns list of fix descriptions (empty if nothing changed).
    """
    original = script.read_text(encoding="utf-8")
    string_ranges = _find_string_ranges(original)
    source = original
    fixes = []

    for bad_char, good_char, desc in _UNICODE_REPLACEMENTS:
        new_source, count = _replace_outside_strings(
            source, bad_char, good_char, string_ranges,
        )
        if count > 0:
            old_lines = source.splitlines()
            new_lines = new_source.splitlines()
            hit_lines = [
                str(i)
                for i, (a, b) in enumerate(zip(old_lines, new_lines), 1)
                if a != b
            ]
            source = new_source
            loc = f"第 {','.join(hit_lines)} 行" if hit_lines else ""
            fixes.append(f"{desc} {bad_char!r} → {good_char!r} ({count} 处) {loc}")

    if fixes:
        script.write_text(source, encoding="utf-8")

    return fixes


def _fix_mismatched_backtick(line: str) -> str:
    r"""Fix a single line where a template literal opens with ` but closes with ' or " (or vice versa).

    Common LLM artifact: the model uses backtick to enable ``${var}``
    interpolation but accidentally closes the string with a single or
    double quote instead of a matching backtick.

    Example::

        text: `（自 ${dateStr} 起至 ${endDateStr} 止）。恳请批准。',
              ^                                                       ^
              backtick opens                             single quote (BUG)

    Fixed to::

        text: `（自 ${dateStr} 起至 ${endDateStr} 止）。恳请批准。`,

    Only triggers when the string body contains ``${`` (confirming
    template-literal intent), to avoid false positives with legitimate
    multi-line template literals.
    """
    n = len(line)
    i = 0
    parts: list[str] = []

    while i < n:
        ch = line[i]

        if ch not in ("`", "'", '"'):
            parts.append(ch)
            i += 1
            continue

        open_quote = ch
        j = i + 1
        has_interp = False
        close_j = -1

        while j < n:
            if line[j] == "\\" and j + 1 < n:
                j += 2
                continue
            if line[j] == "$" and j + 1 < n and line[j + 1] == "{":
                has_interp = True
            if line[j] == open_quote:
                close_j = j
                break
            j += 1

        if close_j >= 0:
            parts.append(line[i : close_j + 1])
            i = close_j + 1
            continue

        if not has_interp:
            parts.append(line[i:])
            return "".join(parts)

        for k in range(n - 1, i, -1):
            if line[k] in ("`", "'", '"') and line[k] != open_quote:
                rest = line[k + 1 :].strip()
                if not rest or rest[0] in ",);]:}":
                    parts.append("`")
                    parts.append(line[i + 1 : k])
                    parts.append("`")
                    parts.append(line[k + 1 :])
                    return "".join(parts)
                break

        parts.append(line[i:])
        return "".join(parts)

    return "".join(parts)


def _auto_fix_mismatched_quotes(script: Path) -> list[str]:
    r"""Fix backtick-opened strings that close with ``'`` or ``"`` (or vice versa).

    Must run **before** ``_auto_fix_unicode`` because a mismatched backtick
    causes ``_find_string_ranges`` to treat a huge span as one string,
    preventing fullwidth-punctuation replacements in code regions.
    """
    source = script.read_text(encoding="utf-8")
    lines = source.splitlines()
    fixes: list[str] = []
    changed = False

    for idx, line in enumerate(lines):
        new_line = _fix_mismatched_backtick(line)
        if new_line != line:
            lines[idx] = new_line
            fixes.append(
                f"引号不匹配 (` / ' 或 \" 混用) → 统一为模板字符串 (第 {idx + 1} 行)"
            )
            changed = True

    if changed:
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return fixes


def _auto_fix_broken_unicode_escape(script: Path) -> list[str]:
    r"""Fix truncated \uXXXX escapes from LLM streaming interruption.

    When write_file output is cut mid-unicode-escape and the model
    resumes with raw Chinese text, the file ends up with::

        bodyText("\u4e0b...\u5f3a\u化学习算法...")

    ``\u化`` is invalid JS (``\u`` must be followed by 4 hex digits).

    Fix strategy:
      1. Remove the broken ``\u`` prefix (keep the raw UTF-8 character —
         Node.js handles mixed escaped + raw UTF-8 in string literals).
      2. If the string literal is left unclosed (common when truncation
         happens inside a function argument), close it with ``"),``.
    """
    source = script.read_text(encoding="utf-8")

    broken_re = re.compile(r"\\u(?!\{[0-9a-fA-F]+\})(?![0-9a-fA-F]{4})")
    if not broken_re.search(source):
        return []

    lines = source.splitlines()
    fixes: list[str] = []

    for idx, line in enumerate(lines):
        if not broken_re.search(line):
            continue

        new_line = broken_re.sub("", line)

        in_str: str | None = None
        i = 0
        n = len(new_line)
        while i < n:
            ch = new_line[i]
            if in_str:
                if ch == "\\" and i + 1 < n:
                    i += 2
                    continue
                if ch == in_str:
                    in_str = None
            elif ch in ('"', "'", "`"):
                in_str = ch
            i += 1

        if in_str:
            stripped = new_line.rstrip()
            new_line = stripped + in_str + "),"
            fixes.append(f"截断的 Unicode 转义 + 闭合字符串 (第 {idx + 1} 行)")
        else:
            fixes.append(f"截断的 Unicode 转义 (第 {idx + 1} 行)")

        lines[idx] = new_line

    if fixes:
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return fixes


def _auto_fix_unicode_escapes(script: Path) -> list[str]:
    r"""Convert \uXXXX escapes inside string literals back to raw characters.

    LLMs frequently output Chinese text as ``\u6700\u540e`` instead of
    ``最后``.  Both are valid JS, but raw characters improve readability.
    Only replaces inside string literals to avoid breaking code.
    """
    source = script.read_text(encoding="utf-8")
    escape_re = re.compile(r"\\u([0-9a-fA-F]{4})")
    if not escape_re.search(source):
        return []

    string_ranges = _find_string_ranges(source)
    if not string_ranges:
        return []

    chars: list[str] = list(source)
    count = 0
    for m in reversed(list(escape_re.finditer(source))):
        start, end = m.start(), m.end()
        if not any(s <= start < e for s, e in string_ranges):
            continue
        raw_char = chr(int(m.group(1), 16))
        if raw_char in ('\n', '\r', '\t', '\\', '"', "'", '`'):
            continue
        chars[start:end] = [raw_char]
        count += 1

    if count == 0:
        return []

    script.write_text("".join(chars), encoding="utf-8")
    return [f"\\uXXXX 转义 → 原始字符 ({count} 处)"]


def _auto_fix_unclosed_strings(script: Path) -> list[str]:
    r"""Fix lines where a ``"`` or ``'`` string literal opens but never closes.

    In JavaScript, single- and double-quoted strings **cannot** span multiple
    lines (unlike template literals).  So if a line opens ``"`` or ``'`` and
    reaches EOL without the matching close, it is always an error — typically
    caused by LLM streaming truncation.

    Strategy per unclosed line:

    1. Append the matching close quote.
    2. Heuristically determine a suffix:
       - If the line looks like a function argument (e.g. ``bodyText("...``),
         append ``),`` to close the call.
       - If the line looks like an object property value (e.g. ``text: "...``),
         append ``,`` to end the property.
       - Otherwise just close the quote.

    Template literals (backtick) are intentionally skipped — they legitimately
    span multiple lines.
    """
    source = script.read_text(encoding="utf-8")
    lines = source.splitlines()
    fixes: list[str] = []
    changed = False

    for idx, line in enumerate(lines):
        in_str: str | None = None
        i = 0
        n = len(line)
        open_pos = -1

        while i < n:
            ch = line[i]
            if in_str:
                if ch == "\\" and i + 1 < n:
                    i += 2
                    continue
                if ch == in_str:
                    in_str = None
                    open_pos = -1
            elif ch in ('"', "'"):
                in_str = ch
                open_pos = i
            elif ch == "`":
                # skip backtick strings on this line (may be multi-line)
                j = i + 1
                while j < n:
                    if line[j] == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if line[j] == "`":
                        break
                    j += 1
                i = j + 1 if j < n else j
                continue
            elif ch == "/" and i + 1 < n:
                if line[i + 1] == "/":
                    break  # rest is line comment
                if line[i + 1] == "*":
                    break  # block comment start, stop scanning
            i += 1

        if in_str is None or in_str == "`":
            continue

        # This line has an unclosed " or ' — fix it
        stripped = line.rstrip()

        # Determine suffix: look at what precedes the opening quote
        prefix = line[:open_pos].rstrip() if open_pos >= 0 else ""
        if prefix.endswith("("):
            suffix = in_str + "),"
        elif prefix.endswith(",") or prefix.endswith(":"):
            suffix = in_str + ","
        else:
            suffix = in_str

        lines[idx] = stripped + suffix
        fixes.append(f"未闭合字符串 ({in_str}...{in_str}) → 自动补全 (第 {idx + 1} 行)")
        changed = True

    if changed:
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return fixes


_CALL_PAREN_RE = re.compile(
    r"""\b(body|h\.p|h\.h[1-6]|h\.bullet|h\.numbered|h\.text|h\.spacer)\s*(['"`])""",
)


def _fix_missing_call_paren(line: str) -> str:
    """Fix ``body'...'`` → ``body('...')`` (missing left parenthesis).

    LLMs frequently drop the ``(`` when producing long sequences of
    ``body('...')`` calls.  The pattern is: a known function name
    immediately followed by a quote character with no ``(`` in between.
    """
    m = _CALL_PAREN_RE.search(line)
    if not m:
        return line
    return _CALL_PAREN_RE.sub(r"\1(\2", line)


def _auto_fix_syntax(script: Path, env: dict[str, str]) -> list[str]:
    """Batch-fix syntax errors that can be repaired mechanically.

    Phase 1 (bulk scan, no subprocess): fix every line in one pass
      - Missing call parenthesis: body'...' → body('...')
      - require() `as` → `:`:  { Header as H } → { Header: H }
      - Nested quotes:  bodyText("简称"星川"") → bodyText('简称"星川"')
      - Unbalanced braces: { para: { ... } }) → { para: { ... } } })
    Phase 2 (loop with node --check): pick off any remaining edge cases
    """
    fixes = []
    source = script.read_text(encoding="utf-8")

    source, ts_fixes = _strip_ts_assertions(source)
    fixes.extend(ts_fixes)

    new_source, as_fixes = _fix_require_as(source)
    if as_fixes:
        source = new_source
        fixes.extend(as_fixes)

    source, enum_fixes = _fix_bad_enums(source)
    fixes.extend(enum_fixes)

    lines = source.splitlines()
    changed = bool(ts_fixes or as_fixes or enum_fixes)

    for idx, line in enumerate(lines):
        new_line = _fix_missing_call_paren(line)
        if new_line != line:
            lines[idx] = new_line
            fixes.append(f"第 {idx + 1} 行: 函数调用补全左括号")
            line = new_line
            changed = True

        new_line = _fix_nested_dq(line)
        if new_line != line:
            lines[idx] = new_line
            fixes.append(f"第 {idx + 1} 行: 嵌套双引号 → 单引号/模板字符串")
            line = new_line
            changed = True

        new_line = _fix_nested_sq(line)
        if new_line != line:
            lines[idx] = new_line
            fixes.append(f"第 {idx + 1} 行: 嵌套单引号 → 模板字符串/双引号")
            line = new_line
            changed = True

        new_line = _fix_broken_arrow_suffix(line)
        if new_line != line:
            lines[idx] = new_line
            fixes.append(f"第 {idx + 1} 行: 移除箭头函数后的多余闭合符")
            line = new_line
            changed = True

        new_line = _fix_unbalanced_braces(line)
        if new_line != line:
            lines[idx] = new_line
            fixes.append(f"第 {idx + 1} 行: 花括号补全")
            changed = True

    if changed:
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")

    already_tried: set[int] = set()
    for _attempt in range(10):
        r = subprocess.run(
            ["node", "--check", str(script)],
            capture_output=True, text=True, env=env,
            encoding="utf-8",
        )
        if r.returncode == 0:
            break

        match = re.search(re.escape(str(script)) + r":(\d+)", r.stderr)
        if not match:
            match = re.search(re.escape(script.name) + r":(\d+)", r.stderr)
        if not match:
            break

        line_no = int(match.group(1))
        if line_no in already_tried:
            break
        already_tried.add(line_no)

        lines = script.read_text(encoding="utf-8").splitlines()
        if not (0 < line_no <= len(lines)):
            break

        line = lines[line_no - 1]
        new_line = _fix_missing_call_paren(line)
        if new_line == line:
            new_line = _fix_nested_dq(line)
        if new_line == line:
            new_line = _fix_nested_sq(line)
        if new_line == line:
            new_line = _fix_broken_arrow_suffix(line)
        if new_line == line:
            new_line = _fix_unbalanced_braces(line)
        if new_line == line:
            fixed_source = _fix_unclosed_brackets_at_line(script, line_no)
            if fixed_source:
                script.write_text(fixed_source, encoding="utf-8")
                fixes.append(f"第 {line_no} 行: 补全未闭合的括号（全局平衡分析）")
                continue
            break

        lines[line_no - 1] = new_line
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fixes.append(f"第 {line_no} 行: 语法修复（phase 2）")

    return fixes


_ENUM_FIXES: list[tuple[str, str, str]] = [
    (r"BorderStyle\.NONE\b", "BorderStyle.NIL", "BorderStyle.NONE → NIL"),
    (r"AlignmentType\.JUSTIFY\b", "AlignmentType.JUSTIFIED", "AlignmentType.JUSTIFY → JUSTIFIED"),
    (r"ShadingType\.SOLID\b", "ShadingType.CLEAR", "ShadingType.SOLID → CLEAR"),
    (r"HeadingLevel\.HEADING(\d)(?!_)", r"HeadingLevel.HEADING_\1", "HeadingLevel.HEADING1 → HEADING_1"),
]


def _fix_bad_enums(source: str) -> tuple[str, list[str]]:
    """Auto-fix common docx-js enum mistakes."""
    fixes: list[str] = []
    for pattern, replacement, desc in _ENUM_FIXES:
        new_source = re.sub(pattern, replacement, source)
        if new_source != source:
            count = len(re.findall(pattern, source))
            fixes.append(f"{desc} ({count} 处)")
            source = new_source
    return source, fixes


def _fix_require_as(source: str) -> tuple[str, list[str]]:
    """Fix ESM-style `as` in CommonJS require destructuring (may span multiple lines).

    const { Header as H } = require("docx")  →  const { Header: H } = require("docx")
    """
    fixes: list[str] = []

    def _replace_block(m: re.Match) -> str:
        block = m.group(0)
        if ' as ' not in block:
            return block
        new_block = re.sub(r'(\w+)\s+as\s+(\w+)', r'\1: \2', block)
        if new_block != block:
            fixes.append("require() 解构中 `as` → `:` (ESM → CommonJS)")
        return new_block

    new_source = re.sub(
        r'const\s*\{[^}]*\}\s*=\s*require\s*\([^)]+\)',
        _replace_block,
        source,
        flags=re.DOTALL,
    )
    return new_source, fixes


def _fix_nested_dq(line: str) -> str:
    """Convert double-quoted strings that contain inner double quotes to single-quoted.

    Correctly skips over single-quoted and backtick-quoted strings so that
    literal " characters inside '...' or `...` are not mistaken for
    double-quoted JS string delimiters.
    """
    i = 0
    n = len(line)
    result: list[str] = []

    while i < n:
        ch = line[i]

        # Skip single-quoted and backtick strings entirely (they can contain literal ")
        if ch in ("'", '`'):
            j = i + 1
            while j < n:
                if line[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                if line[j] == ch:
                    j += 1
                    break
                j += 1
            result.append(line[i:j])
            i = j
            continue

        if ch != '"':
            result.append(ch)
            i += 1
            continue

        j = i + 1
        has_inner = False

        while j < n:
            if line[j] == '\\':
                j += 2
                continue
            if line[j] == '"':
                if _is_js_string_close(line, j):
                    break
                else:
                    has_inner = True
            j += 1
        else:
            result.append(line[i:])
            return ''.join(result)

        content = line[i + 1 : j]
        if has_inner:
            if "'" not in content:
                result.append("'" + content + "'")
            elif '`' not in content and '${' not in content:
                result.append('`' + content + '`')
            else:
                result.append('"' + content.replace('"', '\\"') + '"')
        else:
            result.append('"' + content + '"')
        i = j + 1

    return ''.join(result)


def _fix_nested_sq(line: str) -> str:
    """Convert single-quoted strings that contain inner single quotes to backtick strings.

    Mirror of ``_fix_nested_dq`` for the single-quote case.  Chinese text
    commonly nests single quotes inside double quotes: "他说'走吧'就离开了".
    When such text sits inside a JS single-quoted string the inner ``'``
    breaks the parser::

        body('"他说了什么'送到楼梯口'的话"'),   // SyntaxError

    Fixed to::

        body(`"他说了什么'送到楼梯口'的话"`),
    """
    i = 0
    n = len(line)
    result: list[str] = []

    while i < n:
        ch = line[i]

        # Skip double-quoted and backtick strings entirely
        if ch in ('"', '`'):
            j = i + 1
            while j < n:
                if line[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                if line[j] == ch:
                    j += 1
                    break
                j += 1
            result.append(line[i:j])
            i = j
            continue

        if ch != "'":
            result.append(ch)
            i += 1
            continue

        j = i + 1
        has_inner = False

        while j < n:
            if line[j] == '\\':
                j += 2
                continue
            if line[j] == "'":
                if _is_js_string_close(line, j):
                    break
                else:
                    has_inner = True
            j += 1
        else:
            result.append(line[i:])
            return ''.join(result)

        content = line[i + 1 : j]
        if has_inner:
            if '`' not in content and '${' not in content:
                result.append('`' + content + '`')
            elif '"' not in content:
                result.append('"' + content + '"')
            else:
                result.append("'" + content.replace("'", "\\'") + "'")
        else:
            result.append("'" + content + "'")
        i = j + 1

    return ''.join(result)


def _is_js_string_close(line: str, pos: int) -> bool:
    """Determine if the quote at *pos* is a JS string-closing delimiter (not an inner Chinese quote)."""
    rest = line[pos + 1:]
    stripped = rest.lstrip()
    if not stripped:
        return True

    ch = stripped[0]

    if ch in '],;+|&?:}':
        return True

    if ch == ')':
        after_paren = stripped[1:].lstrip()
        if not after_paren or after_paren[0] in ',;.)]\n+|&?}':
            return True
        if after_paren.startswith('.then') or after_paren.startswith('.catch'):
            return True
        return False

    if ch == ',':
        return True

    return False


_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}
_CLOSE_SET = {")", "]", "}"}


def _fix_unbalanced_braces(line: str) -> str:
    r"""Fix bracket-nesting errors within a single line.

    Handles two categories:

    1. **Missing ``}`` before ``)`` or ``]``** (most common LLM artifact)::

         { spacing: { after: 30, line: 260 })   →   { spacing: { after: 30, line: 260 } })

       When a ``)`` or ``]`` is encountered but the stack top expects ``}``,
       insert missing ``}`` closers one at a time until the ``)``/``]`` matches.

    2. **Surplus ``{`` at EOL** (original behaviour):
       If after the full scan more ``{`` than ``}`` remain (ignoring ``()``
       and ``[]`` which legitimately span multiple lines), append the
       missing ``}`` before the trailing ``),`` / ``);`` / ``)``.

    String literals and escape sequences are skipped.
    """
    # -- Phase 1: walk the line, fix mid-line } missing before ) or ] --
    parts: list[str] = []
    stack: list[str] = []  # expected closers
    in_str: str | None = None
    i = 0
    n = len(line)
    changed = False

    while i < n:
        ch = line[i]

        if in_str:
            if ch == "\\" and i + 1 < n:
                parts.append(line[i : i + 2])
                i += 2
                continue
            if ch == in_str:
                in_str = None
            parts.append(ch)
            i += 1
            continue

        if ch in ('"', "'", "`"):
            in_str = ch
            parts.append(ch)
            i += 1
            continue

        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            parts.append(line[i:])
            i = n
            break

        if ch in _OPEN_TO_CLOSE:
            stack.append(_OPEN_TO_CLOSE[ch])
            parts.append(ch)
            i += 1
            continue

        if ch in _CLOSE_SET:
            if stack and stack[-1] == ch:
                stack.pop()
                parts.append(ch)
                i += 1
                continue

            # Mismatch: e.g. stack top is "}" but we got ")".
            # Only insert missing "}" (braces), not ")" or "]".
            # Insert one "}" at a time, re-check after each.
            if stack and stack[-1] == "}" and ch in (")", "]"):
                inserted = 0
                while stack and stack[-1] == "}":
                    stack.pop()
                    inserted += 1
                    if stack and stack[-1] == ch:
                        break
                if stack and stack[-1] == ch:
                    stack.pop()
                    parts.append(" " + "} " * inserted + ch)
                    changed = True
                    i += 1
                    continue
                # Didn't find a match — restore stack and leave as-is
                for _ in range(inserted):
                    stack.append("}")

            parts.append(ch)
            i += 1
            continue

        parts.append(ch)
        i += 1

    # -- Phase 2: leftover unmatched { → append } before trailing ), --
    # Only count { vs } imbalance; ignore ( and [ (they span lines).
    brace_deficit = sum(1 for s in stack if s == "}")
    if brace_deficit <= 0:
        if changed:
            return "".join(parts)
        return line

    result = "".join(parts)
    rstripped = result.rstrip()

    # If the line ends with an opener, comma, or arrow (`=>`), the braces
    # are intentionally unclosed (multi-line structure) — don't touch.
    # `=>` means a multi-line arrow function body on the next line, e.g.:
    #   cols.map((c, i) =>
    #     new TableCell({ ... })
    #   )
    if rstripped and (
        rstripped[-1] in ("{", "[", "(", ",")
        or rstripped.endswith("=>")
    ):
        if changed:
            return result
        return line

    trail = result[len(rstripped):]
    insertion = " }" * brace_deficit

    for suffix in ["),", ");", ")", "],", "];", "]"]:
        if rstripped.endswith(suffix):
            insert_pos = len(rstripped) - len(suffix)
            return rstripped[:insert_pos] + insertion + suffix + trail

    return rstripped + insertion + trail


def _fix_unclosed_brackets_at_line(script: Path, error_line: int) -> str | None:
    """Scan from file start to *error_line* tracking ``(``, ``[``, ``{`` nesting.

    When the existing single-line fixers all fail, the error is often caused by
    a missing ``)`` or ``]`` far from where they were opened — e.g. the LLM
    writes ``refs.bibliography([...];`` instead of ``refs.bibliography([...]);``.

    Strategy:
      1. Walk the source up to (and including) the error line, maintaining a
         bracket stack (with line numbers) that skips string literals and
         comments.
      2. Look at the error line and the *next* non-empty line.  If the next
         line starts with a closer (``]``, ``)``, ``}``) that doesn't match
         the current stack top, there are missing closers in between.
      3. Collect the closers needed to bridge from the stack top down to the
         opener that matches the next line's closer, and insert them on the
         error line before the trailing ``;`` / ``,``.

    This avoids the false-positive of closing *all* unclosed brackets (which
    would close legitimately multi-line ``function {`` / ``return [`` etc.).

    Returns the fixed full source if a repair was made, or ``None``.
    """
    source = script.read_text(encoding="utf-8")
    lines = source.splitlines()
    if not (0 < error_line <= len(lines)):
        return None

    target_idx = error_line - 1
    scan_end = sum(len(lines[i]) + 1 for i in range(error_line))

    # (opener_char, line_number_1based)
    stack: list[tuple[str, int]] = []
    open_to_close = {"(": ")", "[": "]", "{": "}"}
    close_to_open = {")": "(", "]": "[", "}": "{"}
    in_str: str | None = None
    in_line_comment = False
    in_block_comment = False
    i = 0
    current_line = 1

    while i < scan_end and i < len(source):
        ch = source[i]

        if ch == "\n":
            in_line_comment = False
            current_line += 1
            i += 1
            continue

        if in_line_comment:
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and i + 1 < len(source) and source[i + 1] == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_str:
            if ch == "\\" and i + 1 < len(source):
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue

        if ch in ("'", '"', "`"):
            in_str = ch
            i += 1
            continue

        if ch == "/" and i + 1 < len(source):
            if source[i + 1] == "/":
                in_line_comment = True
                i += 2
                continue
            if source[i + 1] == "*":
                in_block_comment = True
                i += 2
                continue

        if ch in open_to_close:
            stack.append((ch, current_line))
        elif ch in close_to_open:
            if stack and stack[-1][0] == close_to_open[ch]:
                stack.pop()

        i += 1

    if not stack:
        return None

    # Determine what the *next* non-empty line expects to close.
    # e.g. if error line is `    ];` and next line is `}`, V8 chokes because
    # it expected `)` (for `bibliography(`) before seeing `}`.
    next_closer: str | None = None
    for li in range(error_line, len(lines)):
        stripped = lines[li].lstrip()
        if not stripped:
            continue
        if stripped[0] in close_to_open:
            next_closer = stripped[0]
        break

    needed_closers: list[str] = []

    if next_closer:
        # Pop from stack top until we find the opener matching next_closer.
        # Everything popped along the way needs a closer inserted at error_line.
        target_opener = close_to_open[next_closer]
        for opener, _ln in reversed(stack):
            if opener == target_opener:
                break
            needed_closers.append(open_to_close[opener])
    else:
        # No next-line closer hint: fall back to closing unclosed ( and [
        # that were opened on the *same line* as the error — safest scope.
        for opener, ln in reversed(stack):
            if ln == error_line and opener in ("(", "["):
                needed_closers.append(open_to_close[opener])

    if not needed_closers:
        return None

    closers_str = "".join(needed_closers)

    line = lines[target_idx]
    rstripped = line.rstrip()

    if rstripped.endswith(";"):
        new_line = rstripped[:-1] + closers_str + ";"
    elif rstripped.endswith(","):
        new_line = rstripped[:-1] + closers_str + ","
    else:
        new_line = rstripped + closers_str

    if new_line == line:
        return None

    lines[target_idx] = new_line
    return "\n".join(lines) + "\n"


def _auto_fix_output_dirs(script: Path) -> list[str]:
    """Ensure output directories for writeFileSync exist.

    If a writeFileSync target's parent directory doesn't exist, create it
    and inject mkdirSync at the top of the script.
    """
    source = script.read_text(encoding="utf-8")
    dirs_to_create: dict[str, int] = {}  # dir_path → line_no

    for m in re.finditer(r"""writeFileSync\s*\(\s*['"]([^'"]+)['"]\s*""", source):
        fpath = m.group(1)
        parent = str(Path(fpath).parent)
        if parent and not Path(parent).exists():
            line_no = source[:m.start()].count("\n") + 1
            dirs_to_create[parent] = line_no

    if not dirs_to_create:
        return []

    fixes = []
    for d, line_no in dirs_to_create.items():
        Path(d).mkdir(parents=True, exist_ok=True)
        fixes.append(f"自动创建输出目录: {d} (writeFileSync 第 {line_no} 行)")

    return fixes


def _auto_fix_placeholders(script: Path) -> list[str]:
    """Replace ``<SKILL_DIR>`` placeholder left by the LLM.

    ``<SKILL_DIR>`` → ``path.join(process.env.SKILL_PATH, ...)``
    """
    source = script.read_text(encoding="utf-8")
    fixes: list[str] = []

    skill_re = re.compile(
        r"""require\s*\(\s*['"]<SKILL_DIR>/([^'"]+)['"]\s*\)""",
    )
    if skill_re.search(source):
        def _repl_skill(m: re.Match) -> str:
            segments = m.group(1).replace("\\", "/").split("/")
            joined = ", ".join(f"'{s}'" for s in segments)
            return f"require(path.join(process.env.SKILL_PATH, {joined}))"
        source = skill_re.sub(_repl_skill, source)
        if "const path = require('path')" not in source and 'const path = require("path")' not in source:
            source = "const path = require('path');\n" + source
        fixes.append("<SKILL_DIR> 占位符 → process.env.SKILL_PATH + path.join")

    if fixes:
        script.write_text(source, encoding="utf-8")

    return fixes


def _auto_fix_fake_env_vars(script: Path) -> list[str]:
    """Replace non-existent process.env directory variables with __dirname.

    LLMs often invent env vars like ``process.env.workspace_dir`` or
    ``process.env.OUTPUT_DIR`` that don't exist at runtime.  The script
    always runs from its own directory, so ``__dirname`` is the correct
    replacement.

    Special case: ``path.join(process.env.workspace_dir, 'output')`` →
    ``__dirname`` because the script is already inside the output folder.
    """
    source = script.read_text(encoding="utf-8")
    fixes: list[str] = []

    _fake_env_re = re.compile(
        r"process\.env\."
        r"(?:workspace_dir|output_dir|OUTPUT_DIR|work_dir|WORK_DIR"
        r"|project_dir|PROJECT_DIR|working_dir|WORKING_DIR"
        r"|base_dir|BASE_DIR|root_dir|ROOT_DIR)"
    )
    if not _fake_env_re.search(source):
        return fixes

    _join_output_re = re.compile(
        r"path\.join\s*\(\s*" + _fake_env_re.pattern + r"\s*,\s*['\"]output['\"]\s*\)"
    )
    new_source = _join_output_re.sub("__dirname", source)

    new_source = _fake_env_re.sub("__dirname", new_source)

    if new_source != source:
        script.write_text(new_source, encoding="utf-8")
        fixes.append("不存在的 process.env 目录变量 → __dirname")

    return fixes


def _auto_fix_python_raw_strings(script: Path) -> list[str]:
    """Fix Python-style r'...' raw strings that LLMs sometimes write in JS.

    ``r'C:\\Users\\...'`` → ``'C:\\\\Users\\\\...'``
    """
    source = script.read_text(encoding="utf-8")
    fixes: list[str] = []

    _py_raw_re = re.compile(r"(?<![a-zA-Z_$0-9])r(['\"])(.+?)\1")

    def _repl(m: re.Match) -> str:
        q = m.group(1)
        content = m.group(2).replace("\\", "\\\\")
        return f"{q}{content}{q}"

    new_source = _py_raw_re.sub(_repl, source)
    if new_source != source:
        script.write_text(new_source, encoding="utf-8")
        fixes.append("Python r'...' 原始字符串语法 → JS 转义字符串")

    return fixes


# ── Auto-fix pipeline ────────────────────────────────────────────

def auto_fix_pipeline(script: Path, env: dict[str, str]) -> list[str]:
    """Run all auto-fix stages in order, return combined fix descriptions.

    Stage 1 — Normalization (text-level, no syntax awareness needed):
      - Placeholder replacement (<SKILL_DIR> → process.env)
      - Fake env vars (process.env.workspace_dir etc.) → __dirname
      - Python r'...' raw strings → JS escaped strings
      - Mismatched quote delimiters (backtick open / single close)
      - Fullwidth punctuation outside strings → ASCII
      - Broken \\uXXXX escapes from streaming truncation
      - \\uXXXX inside strings → raw characters

    Stage 2 — Syntax repair (line-level and AST-aware):
      - Unclosed string literals
      - Missing call parentheses: body'...' → body('...')
      - Nested quotes, TS assertions, ESM→CJS
      - Unbalanced/surplus brackets
      - Enum typos (BorderStyle.NONE → NIL, etc.)
      - node --check loop for remaining edge cases

    Stage 3 — Environment (filesystem):
      - Create missing output directories for writeFileSync
    """
    fixes: list[str] = []

    # ── Stage 1: Normalization ──
    fixes.extend(_auto_fix_placeholders(script))
    fixes.extend(_auto_fix_fake_env_vars(script))
    fixes.extend(_auto_fix_python_raw_strings(script))
    fixes.extend(_auto_fix_mismatched_quotes(script))
    fixes.extend(_auto_fix_unicode(script))
    fixes.extend(_auto_fix_broken_unicode_escape(script))
    fixes.extend(_auto_fix_unicode_escapes(script))

    # ── Stage 2: Syntax repair ──
    fixes.extend(_auto_fix_unclosed_strings(script))
    fixes.extend(_auto_fix_syntax(script, env))
    fixes.extend(_auto_fix_surplus_brackets(script, env))

    # ── Stage 3: Environment ──
    fixes.extend(_auto_fix_output_dirs(script))

    return fixes


_SURPLUS_BRACKET_RE = re.compile(r"(['\"`])\s*\)\s*\]\s*\)\s*[,;]?\s*$")


def _auto_fix_surplus_brackets(script: Path, env: dict[str, str]) -> list[str]:
    """Remove surplus ] or ) that cause 'Unexpected token' errors.

    Common LLM pattern: body('text')]),  →  body('text'),
    The model confuses string-argument body() with array-argument body([...]).

    Only triggers when node --check reports 'Unexpected token' on a specific
    line, to avoid false positives.
    """
    fixes: list[str] = []
    already_tried: set[int] = set()

    for _attempt in range(10):
        r = subprocess.run(
            ["node", "--check", str(script)],
            capture_output=True, text=True, env=env,
            encoding="utf-8",
        )
        if r.returncode == 0:
            break

        if "Unexpected token" not in r.stderr:
            break

        match = re.search(re.escape(str(script)) + r":(\d+)", r.stderr)
        if not match:
            match = re.search(re.escape(script.name) + r":(\d+)", r.stderr)
        if not match:
            break

        line_no = int(match.group(1))
        if line_no in already_tried:
            break
        already_tried.add(line_no)

        lines = script.read_text(encoding="utf-8").splitlines()
        if not (0 < line_no <= len(lines)):
            break

        line = lines[line_no - 1]
        new_line = _fix_surplus_close(line)
        if new_line == line:
            break

        lines[line_no - 1] = new_line
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fixes.append(f"第 {line_no} 行: 移除多余闭合符")

    return fixes


def _fix_surplus_close(line: str) -> str:
    """Fix body('...')]), → body('...'), by removing surplus ]).

    Skips lines where the function takes an array argument (contains '([')
    because body([...]), is a valid pattern.
    """
    stripped = line.rstrip()

    # Skip lines with array arguments: body([...]), is valid
    if "([" in stripped:
        return line

    # Pattern: body('text')]),  → the ]) between ) and , is surplus
    m = re.search(r"""(['"` ])\)\]\)(\s*[,;]?\s*)$""", stripped)
    if m:
        idx = m.start(0) + len(m.group(1))
        return stripped[:idx] + ")" + m.group(2)

    # Pattern: body('text']),  → the ] between ' and ) is surplus
    m2 = re.search(r"""(['"` ])\]\)(\s*[,;]?\s*)$""", stripped)
    if m2:
        idx = m2.start(0) + len(m2.group(1))
        return stripped[:idx] + ")" + m2.group(2)

    return line


# ── Pre-flight checks (all run BEFORE node executes) ─────────────

def _check_syntax(script: Path, env: dict[str, str]) -> list[str]:
    """node --check + regex pre-scan for common LLM code-gen mistakes.

    node --check only reports ONE SyntaxError at a time (V8 limitation).
    We supplement it with regex-based scanning that catches multiple
    instances of frequent LLM mistakes in a single pass.
    """
    errors: list[str] = []
    source = script.read_text(encoding="utf-8")
    lines = source.splitlines()

    # --- Regex pre-scan: catch common LLM syntax mistakes in bulk ---
    _DECL_RE = re.compile(r"^\s*(?:const|let|var)\s")

    _LLM_SYNTAX_PATTERNS: list[tuple[re.Pattern, str, bool]] = [
        # cell="foo", width) instead of cell("foo", width)
        # Skip lines that are normal variable declarations (const/let/var)
        (re.compile(r'\b(\w+)\s*=\s*"[^"]*"\s*,\s*(?:\w+|\d+)'),
         "疑似函数调用写成了赋值（如 `cell=\"x\", w` → `cell(\"x\", w)`）",
         True),  # needs declaration filter
        # doubled opening brackets: arr[[0], func(("x", obj({{
        (re.compile(r'\w+\[\[(?=\d+\])'),
         "双方括号（如 `arr[[0]` → `arr[0]`）",
         False),
        (re.compile(r'\w+\(\((?=["\'])'),
         "双圆括号（如 `func((\"x\"` → `func(\"x\"`）",
         False),
        (re.compile(r'\w+\(\{\{'),
         "双大括号（如 `Table({{` → `Table({`）",
         False),
    ]
    for pat, desc, filter_decl in _LLM_SYNTAX_PATTERNS:
        for m in pat.finditer(source):
            line_no = source[:m.start()].count("\n") + 1
            line_text = lines[line_no - 1]
            if filter_decl and _DECL_RE.match(line_text):
                continue
            errors.append(f"第 {line_no} 行: {desc}\n    {line_text.strip()}")

    # --- node --check: authoritative syntax validation ---
    r = subprocess.run(
        ["node", "--check", str(script)],
        capture_output=True, text=True, env=env,
        encoding="utf-8",
    )
    if r.returncode != 0:
        errors.append(_extract_error_context(script, r.stderr.strip()))

    return errors


def _check_modules(script: Path, env: dict[str, str]) -> list[str]:
    """Verify all require()'d modules can be resolved."""
    source = script.read_text(encoding="utf-8")
    modules = set(re.findall(r"""require\s*\(\s*['"]([^'"./][^'"]*)['"]\s*\)""", source))
    if not modules:
        return []

    checks = "; ".join(
        f'try {{ require.resolve("{m}"); }} catch(e) {{ bad.push("{m}"); }}'
        for m in sorted(modules)
    )
    code = f'const bad = []; {checks} if (bad.length) {{ console.log(JSON.stringify(bad)); process.exit(1); }}'
    r = subprocess.run(
        ["node", "-e", code],
        capture_output=True, text=True, env=env,
        encoding="utf-8",
    )
    if r.returncode != 0:
        try:
            missing = ", ".join(f"`{m}`" for m in __import__("json").loads(r.stdout.strip()))
        except Exception:
            missing = r.stdout.strip() or "unknown"
        return [f"模块未安装: {missing}\n  → 执行 `npm install -g {' '.join(modules)}` 安装"]
    return []


def _check_file_paths(script: Path) -> list[str]:
    """Verify files referenced in readFileSync/writeFileSync actually exist or are writable."""
    source = script.read_text(encoding="utf-8")
    errors = []

    for m in re.finditer(r"""readFileSync\s*\(\s*['"]([^'"]+)['"]\s*\)""", source):
        fpath = m.group(1)
        if not Path(fpath).exists():
            line_no = source[:m.start()].count("\n") + 1
            errors.append(f"第 {line_no} 行: readFileSync 引用的文件不存在: {fpath}")

    for m in re.finditer(r"""writeFileSync\s*\(\s*['"]([^'"]+)['"]\s*""", source):
        fpath = m.group(1)
        parent = Path(fpath).parent
        if not parent.exists():
            line_no = source[:m.start()].count("\n") + 1
            errors.append(
                f"第 {line_no} 行: writeFileSync 的目标目录不存在: {parent}\n"
                f"  → 在 JS 开头加: require('fs').mkdirSync('{parent}', {{ recursive: true }})"
            )

    return errors


_BAD_PATTERNS: list[tuple[str, str, str]] = [
    # Patterns NOT auto-fixed (require human/model decision)
    (r"new\s+Document\s*\(\s*\)", "Document() 缺少参数", "至少传 { sections: [...] }"),
    (r'writeFileSync\s*\([^)]*,\s*doc\s*[,)]', "不能直接写 Document 对象", "用 Packer.toBuffer(doc) 转为 Buffer 再写"),
    # Note: BorderStyle.NONE, ShadingType.SOLID, HeadingLevel.HEADING1, AlignmentType.JUSTIFY
    # are now auto-fixed by _fix_bad_enums() and no longer checked here.
]


def _check_patterns(script: Path) -> list[str]:
    """Detect common docx-js mistakes via pattern matching."""
    source = script.read_text(encoding="utf-8")
    errors = []
    for pattern, desc, fix in _BAD_PATTERNS:
        if not desc:
            continue
        for m in re.finditer(pattern, source):
            line_no = source[:m.start()].count("\n") + 1
            errors.append(f"第 {line_no} 行: {desc} → {fix}")
    return errors


def _check_table_widths(script: Path) -> list[str]:
    """Check if columnWidths arrays have wildly inconsistent sums.

    Tolerance is 1000 twips (~1.7cm). Small overflows are harmless.
    Searches for the table ``width`` declaration within the same
    ``new Table({`` constructor to avoid confusing cell widths or
    outer-table widths with the current table's width.
    """
    source = script.read_text(encoding="utf-8")
    errors = []

    page_cfg_match = re.search(
        r"page\s*:\s*\{[^}]*width\s*:\s*(\d+)", source
    )
    default_content_width = 9360
    if page_cfg_match:
        page_width = int(page_cfg_match.group(1))
        margins_match = re.search(
            r"margins\s*:\s*\{[^}]*(?:left|right)\s*:\s*(\d+)", source
        )
        margin = int(margins_match.group(1)) if margins_match else 1440
        default_content_width = page_width - margin * 2

    for m in re.finditer(r"columnWidths\s*:\s*\[([^\]]+)\]", source):
        try:
            widths = [int(x.strip()) for x in m.group(1).split(",") if x.strip().isdigit()]
            if not widths:
                continue
            total = sum(widths)
            line_no = source[:m.start()].count("\n") + 1

            window_start = max(0, m.start() - 400)
            window = source[window_start:m.start()]

            table_start = None
            for tm in re.finditer(r"new\s+Table\s*\(\s*\{", window):
                table_start = tm.start()

            if table_start is not None:
                table_window = window[table_start:]
                w_match = re.search(
                    r"width\s*:\s*\{\s*size\s*:\s*(\d+)", table_window
                )
                if w_match:
                    table_width = int(w_match.group(1))
                elif re.search(r"width\s*:\s*\{[^}]*contentWidth", table_window):
                    table_width = default_content_width
                elif re.search(r"width\s*:\s*\{", table_window):
                    continue
                else:
                    table_width = default_content_width
            else:
                table_width = default_content_width

            if abs(total - table_width) > 1000:
                errors.append(
                    f"第 {line_no} 行: columnWidths 之和 ({total}) 与表格宽度 ({table_width}) 差距过大"
                )
        except (ValueError, IndexError):
            pass
    return errors


def _check_table_row_cells(script: Path) -> list[str]:
    """Detect rows where cell count (incl. columnSpan) doesn't match columnWidths.

    Pure-Python regex approach targeting the most common LLM mistake:
    using verticalMerge + .map() where the data array has one element too many.

    Handles:
      - Inline columnWidths: ``columnWidths: [w1, w2, ...]``
      - Variable references: ``columnWidths: compColW`` (resolves ``const compColW = [...]``)
      - columnSpan in any argument object: ``cell("x", w, {columnSpan: 5})``
      - .map() data rows: ``...([["a","b"], ...].map((row) => new TableRow({...})))``
    """
    source = script.read_text(encoding="utf-8")
    lines = source.splitlines()
    errors: list[str] = []

    # ① Resolve variable → array element count
    var_counts: dict[str, int] = {}
    for m in re.finditer(r"(?:const|let|var)\s+(\w+)\s*=\s*\[([^\]]*)\]", source):
        items = [x.strip() for x in m.group(2).split(",") if x.strip()]
        var_counts[m.group(1)] = len(items)

    # ② Collect columnWidths with line number + column count
    cw_list: list[tuple[int, int]] = []
    for m in re.finditer(r"columnWidths\s*:\s*(?:\[([^\]]+)\]|(\w+))", source):
        line_no = source[: m.start()].count("\n") + 1
        if m.group(1):
            n = len([x.strip() for x in m.group(1).split(",") if x.strip()])
            cw_list.append((line_no, n))
        elif m.group(2) in var_counts:
            cw_list.append((line_no, var_counts[m.group(2)]))

    if not cw_list:
        return errors

    # ③ Find .map() blocks that create TableRow from data arrays
    #    Supports:  [["a","b"], ...].map(   and   ...([["a","b"], ...].map(
    map_re = re.compile(
        r"(?:\.\.\.\()?\s*\[\s*\n"
        r"(?P<rows>(?:[ \t]*\[[^\n\[\]]*\],?\n)+)"
        r"[ \t]*\]\.map\(",
    )

    for dm in map_re.finditer(source):
        map_line = source[: dm.start()].count("\n") + 1

        # Count elements in the first sub-array
        first = re.search(r"\[([^\[\]]+)\]", dm.group("rows"))
        if not first:
            continue
        data_cols = len([x.strip() for x in first.group(1).split(",") if x.strip()])

        # Scan the children block after .map( for explicit cells + spread
        block = source[dm.end() : dm.end() + 1200]
        explicit = 0
        has_spread = False
        col_span_total = 0
        for bline in block.split("\n"):
            s = bline.strip()
            if s.startswith("...") and ".map(" in s:
                has_spread = True
                break
            if any(kw in s for kw in ("new TableCell(", "makeCell(", "headCell(", "cell(")):
                # Check for columnSpan in this line
                cs_m = re.search(r"columnSpan\s*:\s*(\d+)", s)
                if cs_m:
                    col_span_total += int(cs_m.group(1))
                else:
                    explicit += 1
            if re.match(r"\s*\]\s*[,})\]]", bline):
                break

        if not has_spread:
            continue

        total = explicit + col_span_total + data_cols

        # Find the nearest preceding columnWidths
        col_count = None
        cw_line = None
        for cw_l, cw_n in reversed(cw_list):
            if cw_l < map_line:
                col_count = cw_n
                cw_line = cw_l
                break

        if col_count is None:
            continue

        if total != col_count:
            errors.append(
                f"第 {map_line} 行: .map() 生成的 TableRow 有 {total} 个 cell"
                f"（{explicit} 个显式 + {col_span_total} 跨列 + {data_cols} 个来自数组），"
                f"但表格声明了 {col_count} 列 (columnWidths 第 {cw_line} 行)\n"
                f"    常见原因：使用 verticalMerge 时数据数组多了一个元素，或缺少 columnSpan 抵消"
            )

    return errors


def _check_raw_table_with_helper_params(script: Path) -> list[str]:
    """Detect ``new Table({...header:...})`` — mixing raw Table constructor with h.table() params.

    The raw ``Table`` constructor expects ``rows: [TableRow(...), ...]`` whereas
    ``h.table()`` accepts ``header: [...]`` / ``rows: [['a','b'], ...]``.  Using
    ``new Table`` with helper-style params causes runtime ``TypeError``.
    """
    source = script.read_text(encoding="utf-8")
    errors: list[str] = []

    for m in re.finditer(r"new\s+Table\s*\(\s*\{", source):
        line_no = source[: m.start()].count("\n") + 1
        block = source[m.end(): m.end() + 600]
        brace_depth = 1
        end_idx = 0
        for i, ch in enumerate(block):
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth == 0:
                    end_idx = i
                    break
        top_block = block[:end_idx]

        helper_keys = re.findall(r"^\s*(header|headerColor|altColor|widths)\s*:", top_block, re.MULTILINE)
        if helper_keys:
            keys_str = ", ".join(sorted(set(helper_keys)))
            errors.append(
                f"{script.name}:{line_no}\n"
                f"    new Table({{...}}) 中出现了 h.table() 风格的参数: {keys_str}\n"
                f"    new Table 是 docx-js 底层构造器，参数格式不同。"
                f"请改用 h.table({{widths: [...], header: [...], rows: [...]}}) 替代"
            )
    return errors



def preflight(script_path: str | Path) -> list[str]:
    """Run all pre-flight checks on a JS file. Returns list of error strings (empty = all good)."""
    script = Path(script_path).expanduser().resolve()
    if not script.exists():
        return [f"JS 文件不存在: {script}"]

    env = _with_global_node_path()
    errors: list[str] = []

    # Phase 1: syntax
    syntax_errors = _check_syntax(script, env)
    errors.extend(syntax_errors)

    # Phase 2: modules, files, patterns (all independent, run all)
    # Module check needs node to import — skip when syntax is broken
    if not syntax_errors:
        errors.extend(_check_modules(script, env))
    errors.extend(_check_table_row_cells(script))
    errors.extend(_check_raw_table_with_helper_params(script))
    # Regex-based checks work regardless of syntax validity
    errors.extend(_check_file_paths(script))
    errors.extend(_check_patterns(script))
    errors.extend(_check_table_widths(script))

    return errors


# ── Post-processing: fix docx.js bugs in generated files ─────────

def _fix_bookmark_ids_in_xml(content: str) -> tuple[str, int]:
    """Fix duplicate w:id on bookmarkStart/bookmarkEnd (docx.js v9.x bug).

    docx.js assigns w:id="1" to every Bookmark.  This reassigns unique
    incremental IDs while preserving start/end pairing via document order.

    Returns (fixed_content, num_unique_bookmarks).
    """
    start_tag_re = re.compile(r"<w:bookmarkStart\b[^/]*?/>")
    id_re = re.compile(r'w:id="(\d+)"')
    name_re = re.compile(r'w:name="([^"]*)"')

    starts = list(start_tag_re.finditer(content))
    if len(starts) <= 1:
        return content, 0

    old_ids = []
    for m in starts:
        id_m = id_re.search(m.group())
        if id_m:
            old_ids.append(id_m.group(1))
    if len(set(old_ids)) == len(old_ids):
        return content, 0

    name_to_id: dict[str, str] = {}
    counter = 0
    for m in starts:
        name_m = name_re.search(m.group())
        name = name_m.group(1) if name_m else f"_bm{counter}"
        if name not in name_to_id:
            name_to_id[name] = str(counter)
            counter += 1

    all_tags = list(re.finditer(
        r"<w:bookmarkStart\b[^/]*?/>|<w:bookmarkEnd\b[^/]*?/>", content,
    ))

    replacements: list[tuple[int, int, str]] = []
    stack: list[str] = []
    for tag_m in all_tags:
        tag = tag_m.group()
        if "bookmarkStart" in tag:
            nm = name_re.search(tag)
            name = nm.group(1) if nm else f"_bm{len(replacements)}"
            new_id = name_to_id.get(name, str(counter))
            replacements.append((tag_m.start(), tag_m.end(), id_re.sub(f'w:id="{new_id}"', tag)))
            stack.append(new_id)
        else:
            new_id = stack.pop() if stack else "0"
            replacements.append((tag_m.start(), tag_m.end(), id_re.sub(f'w:id="{new_id}"', tag)))

    result = content
    for start, end, new_tag in reversed(replacements):
        result = result[:start] + new_tag + result[end:]

    return result, len(name_to_id)


def _fix_docx_bookmark_ids(docx_path: Path) -> int:
    """Fix duplicate bookmark IDs in a DOCX file in-place. Returns count of unique bookmarks fixed."""
    import tempfile
    import zipfile

    modified: dict[str, str] = {}
    total = 0

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            if not name.endswith(".xml"):
                continue
            raw = zin.read(name).decode("utf-8")
            if "bookmarkStart" not in raw:
                continue
            fixed, count = _fix_bookmark_ids_in_xml(raw)
            if count > 0:
                modified[name] = fixed
                total += count

    if not modified:
        return 0

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx")
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(docx_path, "r") as zin:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename in modified:
                        zout.writestr(item, modified[item.filename])
                    else:
                        zout.writestr(item, zin.read(item.filename))
        shutil.move(tmp_path, str(docx_path))
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return total


def _fix_docx_update_fields(docx_path: Path) -> bool:
    """Ensure <w:updateFields w:val="true"/> in settings.xml for documents with TOC fields.

    docx-js generates TOC field instructions but cannot pre-render entries.
    By setting updateFields w:val="true", Word/WPS will auto-refresh all
    fields (including TOC) when the document is opened.

    Also fixes a docx-js bug: ``features: { updateFields: true }`` generates
    a bare ``<w:updateFields/>`` tag without ``w:val="true"``, which WPS
    ignores.  This function replaces such bare tags with the correct form.

    Returns True if settings.xml was modified.
    """
    import zipfile

    CORRECT_TAG = '<w:updateFields w:val="true"/>'

    has_toc = False
    settings_name: str | None = None
    settings_raw: str | None = None

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            raw = zin.read(name).decode("utf-8", errors="replace")
            if "TOC " in raw or ("w:sdt" in raw and "TOC" in raw):
                has_toc = True
            if name.endswith("settings.xml"):
                settings_name = name
                settings_raw = raw

    if not has_toc or settings_name is None or settings_raw is None:
        return False

    if 'w:val="true"' in settings_raw and "updateFields" in settings_raw:
        return False

    bare_tag_re = re.compile(r"<w:updateFields\s*/?>")
    if bare_tag_re.search(settings_raw):
        new_raw = bare_tag_re.sub(CORRECT_TAG, settings_raw)
    else:
        insert_after = re.search(r"<w:settings\b[^>]*>", settings_raw)
        if not insert_after:
            return False
        pos = insert_after.end()
        new_raw = settings_raw[:pos] + CORRECT_TAG + settings_raw[pos:]

    if new_raw == settings_raw:
        return False

    tmp_path = str(docx_path) + ".tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == settings_name:
                    zout.writestr(item, new_raw.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
        shutil.move(tmp_path, str(docx_path))
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return True


def _remove_update_fields(docx_path: Path) -> bool:
    """Remove <w:updateFields .../> from settings.xml.

    Called after TOC cached entries are successfully populated — the cached
    content is sufficient for display and updateFields would cause WPS to
    clear the cache and attempt a live rebuild that often fails.
    """
    import zipfile

    settings_name: str | None = None
    settings_raw: str | None = None

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            if name.endswith("settings.xml"):
                settings_name = name
                settings_raw = zin.read(name).decode("utf-8", errors="replace")
                break

    if settings_name is None or settings_raw is None:
        return False

    tag_re = re.compile(r"<w:updateFields[^/>]*/?>")
    if not tag_re.search(settings_raw):
        return False

    new_raw = tag_re.sub("", settings_raw)
    if new_raw == settings_raw:
        return False

    tmp_path = str(docx_path) + ".tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == settings_name:
                    zout.writestr(item, new_raw.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
        shutil.move(tmp_path, str(docx_path))
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return True


_TOC_STYLES_XML = """\
<w:style w:type="paragraph" w:styleId="TOC1" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:name w:val="toc 1"/>
  <w:basedOn w:val="Normal"/>
  <w:uiPriority w:val="39"/>
  <w:pPr>
    <w:spacing w:before="120" w:after="0" w:line="360" w:lineRule="auto"/>
  </w:pPr>
  <w:rPr><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="TOC2" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:name w:val="toc 2"/>
  <w:basedOn w:val="Normal"/>
  <w:uiPriority w:val="39"/>
  <w:pPr>
    <w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/>
    <w:ind w:left="420"/>
  </w:pPr>
  <w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="TOC3" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:name w:val="toc 3"/>
  <w:basedOn w:val="Normal"/>
  <w:uiPriority w:val="39"/>
  <w:pPr>
    <w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/>
    <w:ind w:left="840"/>
  </w:pPr>
  <w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
</w:style>"""


def _fix_docx_toc_styles(docx_path: Path) -> bool:
    """Inject TOC 1/2/3 paragraph styles with indentation into styles.xml.

    docx-js generates TOC field instructions but does not include the
    ``TOC 1`` / ``TOC 2`` / ``TOC 3`` paragraph styles.  Word has built-in
    defaults with indentation, but WPS does not — causing all TOC levels
    to render at the same indent.  This injects explicit styles so that
    sub-headings are properly indented in all word processors.
    """
    import zipfile

    has_toc = False
    styles_name: str | None = None
    styles_raw: str | None = None

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            raw = zin.read(name).decode("utf-8", errors="replace")
            if "TOC " in raw or ("w:sdt" in raw and "TOC" in raw):
                has_toc = True
            if name.endswith("styles.xml"):
                styles_name = name
                styles_raw = raw

    if not has_toc or styles_name is None or styles_raw is None:
        return False

    if re.search(r'w:styleId="TOC[123]"', styles_raw):
        return False

    close_tag = "</w:styles>"
    if close_tag not in styles_raw:
        return False

    new_raw = styles_raw.replace(close_tag, _TOC_STYLES_XML + close_tag)

    tmp_path = str(docx_path) + ".tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == styles_name:
                    zout.writestr(item, new_raw.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
        shutil.move(tmp_path, str(docx_path))
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return True


def _fix_docx_heading_outline_levels(docx_path: Path) -> bool:
    """Add missing outlineLvl to Heading styles so TOC field evaluation works.

    docx-js defines Heading1–6 styles but omits ``<w:outlineLvl>`` in their
    ``<w:pPr>``.  The TOC ``\\o`` switch relies on outline levels to collect
    entries; without them WPS reports "未找到目录项" when the user manually
    updates the field.  This injects the correct outline levels.
    """
    import zipfile

    has_toc = False
    styles_name: str | None = None
    styles_raw: str | None = None

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            raw = zin.read(name).decode("utf-8", errors="replace")
            if "TOC " in raw or ("w:sdt" in raw and "TOC" in raw):
                has_toc = True
            if name.endswith("styles.xml"):
                styles_name = name
                styles_raw = raw

    if not has_toc or styles_name is None or styles_raw is None:
        return False

    heading_re = re.compile(
        r'(<w:style\b[^>]*w:styleId="Heading(\d)"[^>]*>)'
        r'(.*?)'
        r'(</w:style>)',
        re.DOTALL,
    )

    patched = False
    new_raw = styles_raw

    for m in heading_re.finditer(styles_raw):
        level = int(m.group(2))
        body = m.group(3)
        if "outlineLvl" in body:
            continue

        outline_tag = f'<w:outlineLvl w:val="{level - 1}"/>'

        ppr_match = re.search(r"(<w:pPr\b[^>]*>)(.*?)(</w:pPr>)", body, re.DOTALL)
        if ppr_match:
            new_body = body.replace(
                ppr_match.group(3),
                outline_tag + ppr_match.group(3),
                1,
            )
        else:
            new_body = f"<w:pPr>{outline_tag}</w:pPr>" + body

        old_block = m.group(0)
        new_block = m.group(1) + new_body + m.group(4)
        new_raw = new_raw.replace(old_block, new_block, 1)
        patched = True

    if not patched:
        return False

    tmp_path = str(docx_path) + ".tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == styles_name:
                    zout.writestr(item, new_raw.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
        shutil.move(tmp_path, str(docx_path))
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return True


_WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_XML_NS = "http://www.w3.org/XML/1998/namespace"
_HEADING_STYLE_RE = re.compile(r"Heading([1-9])$")
_TOC_RANGE_RE = re.compile(r'\\o\s+"(\d+)-(\d+)"')


def _w_tag(local_name: str) -> str:
    return f"{{{_WORD_NS}}}{local_name}"


_ILLEGAL_XML_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]"
)


def _strip_illegal_xml_chars(xml_text: str) -> str:
    """Remove characters illegal in XML 1.0 from a string.

    OMML generated from inline LaTeX math ($...$) may inject control characters
    like U+0008 (backspace) that cause ET.fromstring() to raise ParseError.
    """
    return _ILLEGAL_XML_CHARS_RE.sub("", xml_text)


def _register_xml_namespaces(xml_text: str) -> None:
    import io
    import xml.etree.ElementTree as ET

    for _, (prefix, uri) in ET.iterparse(
        io.BytesIO(xml_text.encode("utf-8")),
        events=("start-ns",),
    ):
        if prefix == "xml":
            continue
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            continue


def _get_heading_level(paragraph) -> int | None:
    ppr = paragraph.find(_w_tag("pPr"))
    if ppr is None:
        return None

    style = ppr.find(_w_tag("pStyle"))
    if style is None:
        return None

    val = style.get(_w_tag("val")) or style.get(f"{{{_WORD_NS}}}val") or style.get("w:val")
    if not val:
        return None

    match = _HEADING_STYLE_RE.fullmatch(val)
    if not match:
        return None
    return int(match.group(1))


def _paragraph_visible_text(paragraph) -> str:
    parts = []
    for text_node in paragraph.iter(_w_tag("t")):
        if text_node.text:
            parts.append(text_node.text)
    return "".join(parts).strip()


def _get_toc_heading_range(instr_text: str) -> tuple[int, int]:
    match = _TOC_RANGE_RE.search(instr_text)
    if not match:
        return 1, 9

    start = int(match.group(1))
    end = int(match.group(2))
    if start > end:
        start, end = end, start
    return max(start, 1), min(end, 9)


def _find_existing_bookmark_name(paragraph) -> str | None:
    for bookmark in paragraph.findall(_w_tag("bookmarkStart")):
        name = bookmark.get(_w_tag("name")) or bookmark.get(f"{{{_WORD_NS}}}name") or bookmark.get("w:name")
        if name and name != "_GoBack":
            return name
    return None


def _insert_heading_bookmark(paragraph, bookmark_name: str, bookmark_id: int) -> None:
    import xml.etree.ElementTree as ET

    start = ET.Element(
        _w_tag("bookmarkStart"),
        {
            _w_tag("name"): bookmark_name,
            _w_tag("id"): str(bookmark_id),
        },
    )
    end = ET.Element(_w_tag("bookmarkEnd"), {_w_tag("id"): str(bookmark_id)})

    insert_at = 0
    if len(paragraph) > 0 and paragraph[0].tag == _w_tag("pPr"):
        insert_at = 1
    paragraph.insert(insert_at, start)
    paragraph.append(end)


def _collect_toc_entries(root, min_level: int, max_level: int) -> list[dict[str, object]]:
    body = root.find(_w_tag("body"))
    if body is None:
        return []
    body_children = list(body)

    next_bookmark_id = 1
    for bookmark in root.iter(_w_tag("bookmarkStart")):
        raw_id = bookmark.get(_w_tag("id")) or bookmark.get(f"{{{_WORD_NS}}}id") or bookmark.get("w:id")
        try:
            next_bookmark_id = max(next_bookmark_id, int(raw_id) + 1)
        except (TypeError, ValueError):
            continue

    has_toc_sdt = any(
        "TOC " in "".join((i.text or "") for i in sdt.iter(_w_tag("instrText")))
        for sdt in root.iter(_w_tag("sdt"))
    )

    entries: list[dict[str, object]] = []

    for idx, child in enumerate(body_children):
        level = child.tag == _w_tag("p") and _get_heading_level(child) or None
        if isinstance(level, int) and min_level <= level <= max_level:
            title = _paragraph_visible_text(child)
            if title:
                title_compact = title.replace(" ", "").replace("\u3000", "")
                if has_toc_sdt and title_compact in {"目录", "TableofContents"}:
                    continue
                anchor = _find_existing_bookmark_name(child)
                if not anchor:
                    anchor = f"_toc_auto_{len(entries) + 1}"
                    _insert_heading_bookmark(child, anchor, next_bookmark_id)
                    next_bookmark_id += 1

                entries.append(
                    {
                        "title": title,
                        "level": level,
                        "anchor": anchor,
                    }
                )

    return entries


def _toc_has_visible_cache(sdt_content) -> bool:
    for text_node in sdt_content.iter(_w_tag("t")):
        if text_node.text and text_node.text.strip():
            return True
    return False


def _build_toc_paragraph(entry: dict[str, object], instr_text: str | None, hyperlink: bool, position: str):
    import xml.etree.ElementTree as ET

    level = int(entry["level"])
    anchor = str(entry["anchor"])
    title = str(entry["title"])

    paragraph = ET.Element(_w_tag("p"))

    ppr = ET.SubElement(paragraph, _w_tag("pPr"))
    ET.SubElement(ppr, _w_tag("pStyle"), {_w_tag("val"): f"TOC{level}"})
    indent_left = (level - 1) * 480
    if indent_left > 0:
        ET.SubElement(ppr, _w_tag("ind"), {_w_tag("left"): str(indent_left)})

    if position == "first":
        run = ET.SubElement(paragraph, _w_tag("r"))
        ET.SubElement(
            run,
            _w_tag("fldChar"),
            {
                _w_tag("fldCharType"): "begin",
                _w_tag("dirty"): "true",
            },
        )
        instr = ET.SubElement(run, _w_tag("instrText"))
        instr.set(f"{{{_XML_NS}}}space", "preserve")
        instr.text = instr_text or 'TOC \\h \\o "1-3"'
        ET.SubElement(run, _w_tag("fldChar"), {_w_tag("fldCharType"): "separate"})

    content_parent = paragraph
    if hyperlink and anchor:
        content_parent = ET.SubElement(
            paragraph,
            _w_tag("hyperlink"),
            {
                _w_tag("history"): "1",
                _w_tag("anchor"): anchor,
            },
        )

    entry_run = ET.SubElement(content_parent, _w_tag("r"))

    title_node = ET.SubElement(entry_run, _w_tag("t"))
    title_node.set(f"{{{_XML_NS}}}space", "default")
    title_node.text = title

    if position == "last":
        end_run = ET.SubElement(paragraph, _w_tag("r"))
        ET.SubElement(end_run, _w_tag("fldChar"), {_w_tag("fldCharType"): "end"})

    return paragraph


def _build_toc_end_paragraph():
    import xml.etree.ElementTree as ET

    paragraph = ET.Element(_w_tag("p"))
    run = ET.SubElement(paragraph, _w_tag("r"))
    ET.SubElement(run, _w_tag("fldChar"), {_w_tag("fldCharType"): "end"})
    return paragraph


def _fix_docx_toc_cached_entries(docx_path: Path) -> bool:
    """Populate visible TOC entries from Heading paragraphs when the TOC is empty.

    Unlike Word's normal TOC cache, this backfill writes only structure and
    dotted leaders. It intentionally omits page numbers so stale pagination is
    never shown when the document opens before a field refresh.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    document_name: str | None = None
    document_raw: str | None = None

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            if name.endswith("document.xml"):
                document_name = name
                document_raw = zin.read(name).decode("utf-8", errors="replace")
                break

    if document_name is None or document_raw is None:
        return False
    if "TOC " not in document_raw or "Heading" not in document_raw:
        return False

    document_raw = _strip_illegal_xml_chars(document_raw)
    _register_xml_namespaces(document_raw)
    root = ET.fromstring(document_raw)
    body = root.find(_w_tag("body"))

    patched = False
    for sdt in list(root.iter(_w_tag("sdt"))):
        instr_parts = [
            (instr.text or "")
            for instr in sdt.iter(_w_tag("instrText"))
        ]
        instr_text = "".join(instr_parts).strip()
        if "TOC " not in instr_text:
            continue

        sdt_content = sdt.find(_w_tag("sdtContent"))
        if sdt_content is None:
            continue

        min_level, max_level = _get_toc_heading_range(instr_text)
        entries = _collect_toc_entries(root, min_level, max_level)
        if not entries:
            continue

        hyperlink = "\\h" in instr_text
        new_children = []
        for index, entry in enumerate(entries):
            if len(entries) == 1:
                position = "first"
            elif index == 0:
                position = "first"
            elif index == len(entries) - 1:
                position = "last"
            else:
                position = "middle"
            new_children.append(_build_toc_paragraph(entry, instr_text, hyperlink, position))

        if len(entries) == 1:
            new_children.append(_build_toc_end_paragraph())

        sdt_content[:] = new_children
        patched = True

        # docx-js wraps TableOfContents inside a <w:p> when the model uses
        # h.p([new TableOfContents(...)]).  A block-level SDT (containing <w:p>
        # children) nested inside another <w:p> is invalid OOXML — WPS silently
        # ignores the whole TOC.  Hoist the SDT to be a direct body child.
        if body is not None:
            for bi, body_child in enumerate(list(body)):
                if body_child.tag == _w_tag("p") and sdt in list(body_child):
                    body_child.remove(sdt)
                    body.insert(bi + 1, sdt)
                    remaining = [c for c in body_child if c.tag != _w_tag("pPr")]
                    if not remaining:
                        body.remove(body_child)
                    break

    if not patched:
        return False

    new_raw = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    tmp_path = str(docx_path) + ".tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == document_name:
                    zout.writestr(item, new_raw.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
        shutil.move(tmp_path, str(docx_path))
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return True


def _fix_docx_toc_dot_leaders(docx_path: Path) -> bool:
    """Fix pre-populated TOC entries to match real TOC styling.

    1. Remove dot leaders and trailing ``<w:tab/>`` from cached entries
       (no page numbers → dots trail into empty space).
    2. Assign ``TOC1``/``TOC2``/``TOC3`` paragraph styles to cached entries
       so font, indent, spacing match the real TOC after field update.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    document_name: str | None = None
    document_raw: str | None = None

    with zipfile.ZipFile(docx_path, "r") as zin:
        for name in zin.namelist():
            if name.endswith("document.xml"):
                document_name = name
                document_raw = zin.read(name).decode("utf-8", errors="replace")
                break

    if document_name is None or document_raw is None:
        return False

    document_raw = _strip_illegal_xml_chars(document_raw)
    _register_xml_namespaces(document_raw)
    root = ET.fromstring(document_raw)

    changed = False
    tab_tag = _w_tag("tab")
    tabs_tag = _w_tag("tabs")
    ppr_tag = _w_tag("pPr")
    pstyle_tag = _w_tag("pStyle")
    val_attr = _w_tag("val")
    ind_tag = _w_tag("ind")
    left_attr = _w_tag("left")
    p_tag = _w_tag("p")
    fld_char_tag = _w_tag("fldChar")

    for sdt in root.iter(_w_tag("sdt")):
        instr_parts = [
            (instr.text or "") for instr in sdt.iter(_w_tag("instrText"))
        ]
        if "TOC " not in "".join(instr_parts):
            continue

        sdt_content = sdt.find(_w_tag("sdtContent"))
        if sdt_content is None:
            continue

        for para in list(sdt_content.iter(p_tag)):
            if para.find(f".//{fld_char_tag}") is not None:
                has_text = False
                for t_el in para.iter(_w_tag("t")):
                    if t_el.text and t_el.text.strip():
                        has_text = True
                        break
                if not has_text:
                    continue

            ppr = para.find(ppr_tag)

            # Determine level from existing pStyle or indent
            level = 1
            if ppr is not None:
                ps = ppr.find(pstyle_tag)
                if ps is not None:
                    sval = ps.get(val_attr, "")
                    if sval.startswith("TOC") and sval[3:].isdigit():
                        level = int(sval[3:])
                    elif sval.startswith("TOCHeading"):
                        level = 1
                ind = ppr.find(ind_tag)
                if ind is not None and level == 1:
                    left = int(ind.get(left_attr, "0") or "0")
                    if left >= 800:
                        level = 3
                    elif left >= 400:
                        level = 2

            toc_style = f"TOC{level}"

            # Set/update pStyle to TOC{level}
            if ppr is None:
                ppr = ET.SubElement(para, ppr_tag)
                para.insert(0, ppr)
            ps = ppr.find(pstyle_tag)
            if ps is None:
                ps = ET.SubElement(ppr, pstyle_tag)
                ppr.insert(0, ps)
            if ps.get(val_attr) != toc_style:
                ps.set(val_attr, toc_style)
                changed = True

            # Remove inline tabs definition (style handles indentation)
            for tabs_el in list(ppr.iter(tabs_tag)):
                ppr.remove(tabs_el)
                changed = True

            # Remove inline indent (style handles it)
            for ind_el in list(ppr.findall(ind_tag)):
                ppr.remove(ind_el)
                changed = True

            # Remove <w:tab/> elements from runs
            for run in list(para.iter(_w_tag("r"))):
                for tab_el in list(run):
                    if tab_el.tag == tab_tag:
                        run.remove(tab_el)
                        changed = True

    if not changed:
        return False

    new_xml = ET.tostring(root, encoding="unicode", xml_declaration=True)
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(docx_path, "r") as zin:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == document_name:
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
    docx_path.write_bytes(buf.getvalue())
    return True


def _post_fix_generated_docx(script: Path, working_dir: Path, output_path: Path | None = None) -> list[str]:
    """Find DOCX files generated by the script and fix docx.js bugs."""
    source = script.read_text(encoding="utf-8")
    fixes: list[str] = []

    docx_paths: set[Path] = set()

    # Strategy 0: use explicitly passed output_path (most reliable)
    if output_path and output_path.exists():
        docx_paths.add(output_path.resolve())

    # Strategy 1: literal string paths in writeFileSync('xxx.docx')
    for m in re.finditer(r"""writeFileSync\s*\(\s*['"]([^'"]+\.docx)['"]\s*""", source):
        p = Path(m.group(1))
        if not p.is_absolute():
            p = working_dir / p
        p = p.resolve()
        if p.exists():
            docx_paths.add(p)

    # Strategy 2: resolve variable-based paths like OUTPUT_DIR + '/xxx.docx'
    for m in re.finditer(
        r"""writeFileSync\s*\(\s*(\w+)\s*\+\s*['"]([^'"]*\.docx)['"]\s*""", source,
    ):
        var_name = m.group(1)
        suffix = m.group(2)
        var_match = re.search(
            rf"""{re.escape(var_name)}\s*=\s*['"]([^'"]+)['"]\s*;""", source,
        )
        if var_match:
            p = Path(var_match.group(1) + suffix).resolve()
            if p.exists():
                docx_paths.add(p)

    # Strategy 3: resolve variable-based outputPath in writeFileSync(outputPath, ...)
    for m in re.finditer(
        r"""writeFileSync\s*\(\s*(\w+)\s*,\s*""", source,
    ):
        var_name = m.group(1)
        if var_name == 'outputPath':
            # outputPath is set from process.argv[2] in docx-helper.js
            continue
        # Try to resolve from source
        var_match = re.search(
            rf"""{re.escape(var_name)}\s*=\s*['"]([^'"]+\.docx)['"]\s*""", source,
        )
        if var_match:
            p = Path(var_match.group(1)).resolve()
            if p.exists():
                docx_paths.add(p)

    # Strategy 4: fallback — scan working_dir for any .docx files
    if not docx_paths:
        for p in working_dir.rglob("*.docx"):
            docx_paths.add(p.resolve())

    for p in sorted(docx_paths):
        try:
            _fix_docx_toc_styles(p)
        except Exception:
            pass

        try:
            _fix_docx_heading_outline_levels(p)
        except Exception:
            pass

        try:
            _fix_docx_toc_cached_entries(p)
        except Exception:
            pass

        try:
            _fix_docx_toc_dot_leaders(p)
        except Exception:
            pass

        try:
            _remove_update_fields(p)
        except Exception:
            pass

        try:
            count = _fix_docx_bookmark_ids(p)
            if count:
                fixes.append(f"修复 {count} 个重复 bookmark ID: {p.name}")
        except Exception:
            pass

        qc_warnings = _check_docx_quality(p)
        if qc_warnings:
            print(f"\n[quality-check] 检测到 {len(qc_warnings)} 个质量问题 ({p.name}):")
            for w in qc_warnings:
                print(f"  ⚠ {w}")

    return fixes


# ── Post-generation quality checks ────────────────────────────────

_DOUBLE_NUM_AT_START_RE = re.compile(r"^\s*\[(\d+)\]\s*\[(\d+)\]")


def _check_docx_quality(docx_path: Path) -> list[str]:
    """Scan generated DOCX for known quality issues and return warnings.

    Currently checks:
      - Double numbering in reference entries: [1] [2] Author... indicates
        that bibliography() auto-numbered [1] but entry.text also started
        with [2], producing duplicate labels.
        Only triggers when [N] [M] appears at the start of a paragraph
        (not inline citations like 研究[2][3]).
    """
    import zipfile
    import xml.etree.ElementTree as ET

    warnings: list[str] = []

    try:
        with zipfile.ZipFile(docx_path, "r") as zin:
            for name in zin.namelist():
                if not name.endswith("document.xml"):
                    continue
                raw = zin.read(name).decode("utf-8", errors="replace")
                raw = _strip_illegal_xml_chars(raw)
                _register_xml_namespaces(raw)
                root = ET.fromstring(raw)

                for para in root.iter(_w_tag("p")):
                    text = _paragraph_visible_text(para)
                    if not text:
                        continue
                    m = _DOUBLE_NUM_AT_START_RE.search(text)
                    if m:
                        preview = text[:100] + ("..." if len(text) > 100 else "")
                        warnings.append(
                            f"参考文献双重编号: \"{preview}\"\n"
                            f"    bibliography() 已自动编号 [{m.group(1)}]，"
                            f"entry.text 不要再包含 [{m.group(2)}]，请去掉 text 开头的 \"[数字] \""
                        )
    except Exception:
        pass

    return warnings


# ── Citation cleanup: remove hallucinated [@key] ─────────────────

_AUTO_BIB_JSON_RE = re.compile(r"""autoBibliography\s*\(\s*(['"])([^'"]+\.json)\1""")
_AUTO_BIB_VAR_RE = re.compile(r"""autoBibliography\s*\(\s*([A-Za-z_$][\w$]*)\s*(?:,|\))""")
_AUTO_BIB_JOIN_RE = re.compile(r"""autoBibliography\s*\(\s*path\.join\s*\(([^;\n]*)\)\s*\)""")
_JS_STR_ASSIGN_RE = re.compile(
    r"""(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(['"`])([^'"`]+)\2\s*;?"""
)
_JS_ALIAS_ASSIGN_RE = re.compile(
    r"""(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([A-Za-z_$][\w$]*)\s*;?"""
)
_JS_PATH_JOIN_ASSIGN_RE = re.compile(
    r"""(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*path\.join\s*\(([^;\n]*)\)\s*;?"""
)
_TMPL_VAR_RE = re.compile(r"""\$\{([A-Za-z_$][\w$]*)\}""")
_INLINE_CITE_KEY_RE = re.compile(r"""\[@([^\]\s@;]+)\]""")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _extract_auto_bibliography_json_paths(source: str) -> list[str]:
    paths = [m.group(2).strip() for m in _AUTO_BIB_JSON_RE.finditer(source)]

    var_values: dict[str, str] = {}
    alias_values: dict[str, str] = {}
    for m in _JS_STR_ASSIGN_RE.finditer(source):
        name = m.group(1).strip()
        value = m.group(3).strip()
        if value:
            var_values[name] = value

    for m in _JS_ALIAS_ASSIGN_RE.finditer(source):
        left = m.group(1).strip()
        right = m.group(2).strip()
        if left and right:
            alias_values[left] = right

    def _resolve_template(expr: str) -> str | None:
        if "${" not in expr:
            return expr

        def _replace(m: re.Match[str]) -> str:
            key = m.group(1).strip()
            resolved = _resolve_var(key)
            return resolved if resolved is not None else m.group(0)

        out = _TMPL_VAR_RE.sub(_replace, expr)
        return out if "${" not in out else None

    def _split_join_args(arg_text: str) -> list[str]:
        parts: list[str] = []
        cur = []
        quote: str | None = None
        for ch in arg_text:
            if quote:
                cur.append(ch)
                if ch == quote:
                    quote = None
                continue
            if ch in ("'", '"', "`"):
                quote = ch
                cur.append(ch)
                continue
            if ch == ",":
                token = "".join(cur).strip()
                if token:
                    parts.append(token)
                cur = []
                continue
            cur.append(ch)
        token = "".join(cur).strip()
        if token:
            parts.append(token)
        return parts

    def _token_to_path_part(token: str) -> str | None:
        token = token.strip()
        if not token or token in {"__dirname", "process.cwd()"}:
            return ""
        if (token[0] == token[-1]) and token[0] in ("'", '"', "`"):
            inner = token[1:-1]
            return _resolve_template(inner) or inner
        if re.fullmatch(r"[A-Za-z_$][\w$]*", token):
            return _resolve_var(token)
        return None

    def _resolve_join_expr(arg_text: str) -> str | None:
        parts = []
        for tok in _split_join_args(arg_text):
            part = _token_to_path_part(tok)
            if part is None:
                return None
            if part:
                parts.append(part)
        if not parts:
            return None
        return str(Path(*parts)).replace("\\", "/")

    def _resolve_var(name: str) -> str | None:
        seen = set()
        cur = name
        for _ in range(8):
            if cur in seen:
                return None
            seen.add(cur)
            if cur in var_values:
                return _resolve_template(var_values[cur]) or var_values[cur]
            nxt = alias_values.get(cur)
            if not nxt:
                return None
            cur = nxt
        return None

    for m in _JS_PATH_JOIN_ASSIGN_RE.finditer(source):
        name = m.group(1).strip()
        arg_text = m.group(2).strip()
        resolved = _resolve_join_expr(arg_text)
        if name and resolved:
            var_values[name] = resolved

    for m in _AUTO_BIB_VAR_RE.finditer(source):
        var_name = m.group(1).strip()
        resolved = _resolve_var(var_name)
        if resolved:
            paths.append(resolved)

    for m in _AUTO_BIB_JOIN_RE.finditer(source):
        arg_text = m.group(1).strip()
        resolved = _resolve_join_expr(arg_text)
        if resolved:
            paths.append(resolved)

    deduped: list[str] = []
    seen = set()
    for p in paths:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped


def _is_mixed_zh_author_en_title(authors: str, title: str) -> bool:
    """Heuristic for mixed-language references we want to suppress in CN output."""
    a = (authors or "").strip()
    t = (title or "").strip()
    if not a or not t:
        return False
    return bool(_CJK_RE.search(a)) and bool(_LATIN_RE.search(t)) and not bool(_CJK_RE.search(t))


def _load_reference_meta(json_file: Path) -> tuple[set[str], set[str]]:
    raw = json_file.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        return set(), set()
    keys = set()
    mixed_keys = set()
    for item in data:
        if isinstance(item, dict):
            key = str(item.get("key", "")).strip()
            if key:
                keys.add(key)
                if _is_mixed_zh_author_en_title(
                    str(item.get("authors", "") or ""),
                    str(item.get("title", "") or ""),
                ):
                    mixed_keys.add(key)
    return keys, mixed_keys


def _clean_missing_citation_keys(script: Path, base_dir: Path) -> list[str]:
    """Remove inline citations [@key] whose key does not exist in references.json."""
    source = script.read_text(encoding="utf-8")
    raw_paths = _extract_auto_bibliography_json_paths(source)
    if not raw_paths:
        return []

    ref_keys: set[str] = set()
    mixed_ref_keys: set[str] = set()
    used_json_paths: list[Path] = []
    for raw_path in raw_paths:
        p = Path(raw_path).expanduser()
        if not p.is_absolute():
            p = (base_dir / p).resolve()
        if not p.exists():
            continue
        try:
            keys, mixed_keys = _load_reference_meta(p)
            ref_keys |= keys
            mixed_ref_keys |= mixed_keys
            used_json_paths.append(p)
        except Exception:
            continue

    if not ref_keys:
        return []

    missing_counts: dict[str, int] = {}
    mixed_counts: dict[str, int] = {}
    for m in _INLINE_CITE_KEY_RE.finditer(source):
        key = m.group(1).strip()
        if not key:
            continue
        if key not in ref_keys:
            missing_counts[key] = missing_counts.get(key, 0) + 1
        elif key in mixed_ref_keys:
            mixed_counts[key] = mixed_counts.get(key, 0) + 1

    if not missing_counts and not mixed_counts:
        return []

    def _replace_missing(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key in missing_counts or key in mixed_counts:
            return ""
        return match.group(0)

    cleaned = _INLINE_CITE_KEY_RE.sub(_replace_missing, source)
    if cleaned != source:
        script.write_text(cleaned, encoding="utf-8")

    notes: list[str] = []
    if missing_counts:
        notes.append(
            f"引用清理: 已自动忽略不存在的 [@key] 共 {sum(missing_counts.values())} 处，涉及 {len(missing_counts)} 个 key"
        )
    if mixed_counts:
        notes.append(
            f"引用清理: 已自动忽略中英混搭条目 [@key] 共 {sum(mixed_counts.values())} 处，涉及 {len(mixed_counts)} 个 key"
        )
    notes.append(
        "  强制规则: 严禁补写/改写 references.json，严禁手写参考文献条目；缺失/混搭引用已被清理且必须保持清理状态。"
    )
    return notes


# ── Main entry point ─────────────────────────────────────────────

def run_node_docx(
    script_path: str | Path,
    output: str | Path | None = None,
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess:
    """Execute a docx-generating JS script with comprehensive pre-flight checks and auto-backup.

    Args:
        script_path: JS 脚本路径。
        output: DOCX 输出路径。传入后作为 process.argv[2] 传给 node，
                JS 侧 h.build() 无需再传 outputPath。
        cwd: 工作目录，默认为脚本所在目录。

    Pre-flight (before execution):
      1. Syntax check (node --check)
      2. Module resolution (require.resolve)
      3. File path verification (readFileSync targets)
      4. Common mistake detection (ShadingType.SOLID, wrong enums, etc.)
      5. Table width consistency

    Runtime:
      - Auto-backup on first run, update backup on each success
      - Rich error context with source line annotations on failure
    """
    script = Path(script_path).expanduser().resolve()
    if not script.exists():
        raise FileNotFoundError(f"JS 文件不存在: {script}")

    output_resolved = str(Path(output).expanduser().resolve()) if output else None
    if output_resolved and os.path.isdir(output_resolved):
        raise ValueError(
            f"output 参数是目录而非文件路径: {output_resolved}\n"
            f"  → 请传入完整文件路径，如: {output_resolved}/文档.docx"
        )

    # ⓪ Auto-fix pipeline (3 stages)
    env = _with_global_node_path()
    fixes = auto_fix_pipeline(script, env)
    if fixes:
        print(f"[auto-fix] 已自动修正 {len(fixes)} 个问题:")
        for f in fixes:
            print(f"  ✓ {f}")

    # ⓪.1 Citation cleanup: remove hallucinated [@key] not present in references.json
    cleanup_base = Path(cwd).expanduser().resolve() if cwd else script.parent
    citation_cleanup_notes = _clean_missing_citation_keys(script, cleanup_base)
    if citation_cleanup_notes:
        print("[citation-cleanup] 已执行引用清理:")
        for note in citation_cleanup_notes:
            print(f"  ✓ {note}")

    # ① Auto-backup (before preflight so restore_backup works even if preflight fails)
    backup = _backup_path(script)
    if not backup.exists():
        shutil.copy2(script, backup)

    # ② Pre-flight: catch everything we can before executing
    errors = preflight(script)
    if errors:
        sep = "\n  • "
        raise ValueError(
            f"预检发现 {len(errors)} 个问题（未执行脚本，请修复后重试）:{sep}{sep.join(errors)}"
        )

    working_dir = Path(cwd).expanduser().resolve() if cwd else script.parent

    # ③ Execute — output path passed as argv[2] so h.build() can read it
    cmd = ["node", str(script)]
    if output_resolved:
        cmd.append(output_resolved)

    result = subprocess.run(
        cmd,
        capture_output=True, text=True,
        cwd=str(working_dir), env=env,
        encoding="utf-8",
    )

    if result.returncode != 0:
        error_detail = _extract_error_context(
            script, result.stderr.strip() or result.stdout.strip()
        )
        hint = ""
        if backup.exists():
            hint = (
                f"\n\n💡 上次成功版本已备份在: {backup}\n"
                f"   可调用 restore_backup(\"{script_path}\") 恢复后再做定点修改。"
            )
        raise RuntimeError(f"运行时错误:\n{error_detail}{hint}")

    # ④ Success → update backup
    shutil.copy2(script, backup)

    # ⑤ Verify output exists
    if output_resolved and not os.path.isfile(output_resolved):
        print(f"[warn] 脚本执行成功但未找到输出文件: {output_resolved}")

    # ⑥ Post-process: fix docx.js bugs in generated files
    post_fixes = _post_fix_generated_docx(script, working_dir, Path(output_resolved) if output_resolved else None)
    if post_fixes:
        print(f"[post-fix] 已修复生成文件中的问题:")
        for f in post_fixes:
            print(f"  ✓ {f}")

    if result.stderr.strip():
        print(result.stderr.strip())
    if result.stdout.strip():
        print(result.stdout.strip())

    return result


def restore_backup(script_path: str | Path) -> str:
    """Restore the JS file from its last-known-good backup (.js.bak)."""
    script = Path(script_path).expanduser().resolve()
    backup = _backup_path(script)
    if not backup.exists():
        raise FileNotFoundError(f"没有可用的备份: {backup}")
    shutil.copy2(backup, script)
    print(f"已恢复: {backup} → {script}")
    return str(script)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("用法: python run_node_docx.py <script.js>")
    run_node_docx(sys.argv[1])


if __name__ == "__main__":
    main()
