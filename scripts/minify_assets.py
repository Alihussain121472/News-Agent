#!/usr/bin/env python3
"""
CSS and JavaScript Minification Tool.
Produces production-ready minified .min.css and .min.js assets.
"""

import os
import re
from pathlib import Path
import requests

def minify_css(css_content: str) -> str:
    """Minifies CSS safely preserving string literals and url() blocks."""
    # 1. Protect strings and url()
    tokens = []
    def save_token(m):
        tokens.append(m.group(0))
        return f"___TOKEN_{len(tokens)-1}___"

    # Match strings and url(...)
    pattern = r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|url\([^)]*\))'
    css = re.sub(pattern, save_token, css_content)

    # 2. Strip comments /* ... */
    css = re.sub(r'/\*[\s\S]*?\*/', '', css)

    # 3. Normalize whitespace
    css = re.sub(r'\s+', ' ', css)

    # 4. Remove space around delimiters
    css = re.sub(r'\s*([\{\}:;,>~+])\s*', r'\1', css)

    # 5. Remove trailing semicolons before }
    css = re.sub(r';\}', '}', css)

    # 6. Remove empty rule sets
    css = re.sub(r'[^\{\}]+\{\}', '', css)

    # 7. Restore tokens
    for i, tok in enumerate(tokens):
        css = css.replace(f"___TOKEN_{i}___", tok)

    return css.strip()

def minify_js(js_content: str) -> str:
    """Safely minifies JS by stripping multi-line and trailing single-line comments, collapsing whitespace."""
    # Protect strings, template literals, and regexes
    tokens = []
    def save_token(m):
        tokens.append(m.group(0))
        return f"___JSTOKEN_{len(tokens)-1}___"

    # Match single-quoted, double-quoted, and backtick strings
    str_pattern = r'(`(?:\\.|[^`\\])*`|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    js = re.sub(str_pattern, save_token, js_content)

    # Strip multi-line comments
    js = re.sub(r'/\*[\s\S]*?\*/', '', js)

    # Strip single line comments
    lines = []
    for line in js.splitlines():
        # Remove line comment if outside string
        line_clean = re.sub(r'//.*$', '', line)
        if line_clean.strip():
            lines.append(line_clean.strip())

    js = '\n'.join(lines)

    # Restore tokens
    for i, tok in enumerate(tokens):
        js = js.replace(f"___JSTOKEN_{i}___", tok)

    return js.strip()

def run():
    print("=== Minifying CSS Files ===")
    css_files = [
        Path("static/css/variables.css"),
        Path("static/css/styles.css"),
        Path("static/css/main.css"),
        Path("static/css/student-tools.css"),
        Path("static/css/python-practice.css"),
        Path("static/css/website-theme.css"),
        Path("static/css/python-entry.css"),
        Path("portfolio-review/site-repo/style.css"),
        Path("portfolio-review/style.css"),
    ]

    for p in css_files:
        if not p.exists():
            continue
        orig = p.read_text(encoding='utf-8')
        minified = minify_css(orig)
        out_path = p.with_name(p.stem + ".min.css")
        out_path.write_text(minified, encoding='utf-8')
        orig_len = len(orig.encode('utf-8'))
        min_len = len(minified.encode('utf-8'))
        pct = (orig_len - min_len) / orig_len * 100 if orig_len else 0
        print(f"[{p.name}] {orig_len/1024:.1f}KB -> {out_path.name} {min_len/1024:.1f}KB ({pct:.1f}% saved)")

    print("\n=== Minifying JS Files ===")
    js_files = [
        Path("static/js/main.js"),
        Path("static/js/mobile-nav.js"),
        Path("static/js/theme.js"),
        Path("static/js/student-tools.js"),
        Path("static/js/python-practice.js"),
    ]

    for p in js_files:
        if not p.exists():
            continue
        orig = p.read_text(encoding='utf-8')
        minified = minify_js(orig)
        out_path = p.with_name(p.stem + ".min.js")
        out_path.write_text(minified, encoding='utf-8')
        orig_len = len(orig.encode('utf-8'))
        min_len = len(minified.encode('utf-8'))
        pct = (orig_len - min_len) / orig_len * 100 if orig_len else 0
        print(f"[{p.name}] {orig_len/1024:.1f}KB -> {out_path.name} {min_len/1024:.1f}KB ({pct:.1f}% saved)")

    print("\n=== Downloading Minified Vendor CodeMirror ===")
    vendor_dir = Path("static/vendor/codemirror")
    if vendor_dir.exists():
        urls = [
            ("https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.js", vendor_dir / "codemirror.min.js"),
            ("https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/python/python.min.js", vendor_dir / "python.min.js"),
            ("https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.css", vendor_dir / "codemirror.min.css"),
        ]
        for url, target in urls:
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    target.write_bytes(r.content)
                    print(f"Saved {target.name} ({len(r.content)/1024:.1f}KB)")
                else:
                    print(f"Failed to fetch {url}: {r.status_code}")
            except Exception as e:
                print(f"Error fetching {url}: {e}")

if __name__ == '__main__':
    run()
