#!/usr/bin/env python3
"""
research_cli.py - read-only research helper for the AI SDLC factory.

Standard library only (Python 3.8+). Prints compact JSON. Never writes to any remote system.

Commands
  versions   [--path .]                     Pinned dependency versions from pyproject.toml,
                                             requirements*.txt and package.json files.
  osv        [--path .] [--package ...]     Known vulnerabilities from the OSV database (api.osv.dev)
                                             for the repo's pinned versions or named packages.
  confluence-search "<text>" [--space KEY]  Search Confluence pages (title and text).
  confluence-page <id> [--max-chars N]      Read one Confluence page as plain text.
  allowed <url>                             Check a URL against the allow-list in .github/sdlc/config.yaml.

Environment (Confluence only)
  CONFLUENCE_BASE_URL   https://confluence.example.com  or  https://acme.atlassian.net/wiki
  CONFLUENCE_AUTH_TYPE  basic (default) | bearer (Data Center personal access token)
  CONFLUENCE_USER       Cloud: email. DC basic: username.
  CONFLUENCE_API_TOKEN  Cloud API token, or DC personal access token.
  RESEARCH_OSV_URL      override for the OSV endpoint (default https://api.osv.dev)

Exit codes: 0 ok, 2 configuration, 3 HTTP error, 4 not found, 5 bad input.
"""
import argparse
import base64
import glob
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SKIP_DIRS = {"node_modules", ".venv", "venv", ".git", "dist", "build", "__pycache__", ".tox", ".mypy_cache"}
CONFIG_PATH = ".github/sdlc/config.yaml"


def out(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def fail(code, message, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.exit(code)


def http_json(url, method="GET", body=None, headers=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"Accept": "application/json", "User-Agent": "ai-sdlc-researcher"}
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8")
                return json.loads(text) if text.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < 3:
                wait = e.headers.get("Retry-After")
                time.sleep(min(int(wait), 30) if wait and wait.isdigit() else 2 ** attempt)
                continue
            fail(4 if e.code == 404 else 3, "HTTP %s on %s" % (e.code, urllib.parse.urlsplit(url).path))
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            fail(3, "Cannot reach %s: %s" % (urllib.parse.urlsplit(url).netloc, e.reason))
    fail(3, "Request failed after retries")


# --------------------------------------------------------------------------- manifests
def walk(root, pattern):
    for path in glob.glob(os.path.join(root, "**", pattern), recursive=True):
        if not any(part in SKIP_DIRS for part in path.split(os.sep)):
            yield path


REQ_LINE = re.compile(r"^\s*([A-Za-z0-9_.\-\[\]]+)\s*(==|~=|>=|<=|>|<)\s*([A-Za-z0-9_.\-*+]+)")


def parse_requirements(path):
    deps = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            m = REQ_LINE.match(line)
            if m:
                deps.append({"name": re.sub(r"\[.*\]", "", m.group(1)).lower(), "op": m.group(2),
                             "version": m.group(3), "ecosystem": "PyPI", "file": path})
    return deps


def parse_pyproject(path):
    deps = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    # PEP 621: dependencies = ["fastapi>=0.110", ...]
    for block in re.findall(r"(?ms)^\s*(?:dependencies|[a-z\-]+)\s*=\s*\[(.*?)\]", text):
        for item in re.findall(r"['\"]([^'\"]+)['\"]", block):
            m = REQ_LINE.match(item)
            if m:
                deps.append({"name": re.sub(r"\[.*\]", "", m.group(1)).lower(), "op": m.group(2),
                             "version": m.group(3), "ecosystem": "PyPI", "file": path})
    # Poetry: [tool.poetry.dependencies] name = "^1.2"
    for section in re.findall(r"(?ms)^\[tool\.poetry\.(?:group\.\w+\.)?dependencies\]\s*(.*?)(?=^\[|\Z)", text):
        for name, ver in re.findall(r"(?m)^\s*([A-Za-z0-9_.\-]+)\s*=\s*['\"]([^'\"]+)['\"]", section):
            if name.lower() != "python":
                deps.append({"name": name.lower(), "op": ver[:1] if ver[:1] in "^~" else "==",
                             "version": ver.lstrip("^~=<>"), "ecosystem": "PyPI", "file": path})
    return deps


def parse_package_json(path):
    deps = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        try:
            data = json.load(f)
        except ValueError:
            return deps
    for section in ("dependencies", "devDependencies"):
        for name, ver in (data.get(section) or {}).items():
            if not isinstance(ver, str) or ver.startswith(("file:", "link:", "workspace:", "git", "http")):
                continue
            deps.append({"name": name, "op": ver[:1] if ver[:1] in "^~" else "==",
                         "version": ver.lstrip("^~=<>v "), "ecosystem": "npm", "file": path,
                         "dev": section == "devDependencies"})
    return deps


def collect(root):
    deps = []
    for p in walk(root, "requirements*.txt"):
        deps += parse_requirements(p)
    for p in walk(root, "pyproject.toml"):
        deps += parse_pyproject(p)
    for p in walk(root, "package.json"):
        deps += parse_package_json(p)
    seen, unique = set(), []
    for d in deps:
        key = (d["ecosystem"], d["name"], d["version"])
        if key not in seen:
            seen.add(key)
            d["file"] = os.path.relpath(d["file"], root)
            unique.append(d)
    return unique


def cmd_versions(a):
    deps = collect(a.path)
    if a.match:
        deps = [d for d in deps if a.match.lower() in d["name"].lower()]
    out({"ok": True, "count": len(deps), "dependencies": deps})


# --------------------------------------------------------------------------- OSV
def cmd_osv(a):
    base = os.environ.get("RESEARCH_OSV_URL", "https://api.osv.dev").rstrip("/")
    if a.package:
        deps = []
        for spec in a.package:
            m = re.match(r"^(PyPI|npm):([^@=]+)[@=]+(.+)$", spec)
            if not m:
                fail(5, "Use --package PyPI:name==version or npm:name@version")
            deps.append({"ecosystem": m.group(1), "name": m.group(2), "version": m.group(3)})
    else:
        deps = [d for d in collect(a.path) if d["op"] in ("==", "^", "~", "~=")]
        if not a.include_dev:
            deps = [d for d in deps if not d.get("dev")]
    if not deps:
        out({"ok": True, "checked": 0, "vulnerable": [], "note": "no pinned dependencies found"})
        return
    queries = [{"package": {"name": d["name"], "ecosystem": d["ecosystem"]}, "version": d["version"]} for d in deps]
    findings = []
    for start in range(0, len(queries), 500):
        chunk = queries[start:start + 500]
        res = http_json(base + "/v1/querybatch", "POST", {"queries": chunk})
        for dep, r in zip(deps[start:start + 500], res.get("results") or []):
            ids = [v.get("id") for v in r.get("vulns") or []]
            if ids:
                findings.append({"package": dep["name"], "ecosystem": dep["ecosystem"],
                                 "version": dep["version"], "ids": ids[:10]})
    details = []
    for f in findings[: a.details]:
        for vid in f["ids"][:3]:
            v = http_json(base + "/v1/vulns/" + urllib.parse.quote(vid))
            fixed = sorted({e.get("fixed") for af in v.get("affected") or [] for r in af.get("ranges") or []
                            for e in r.get("events") or [] if e.get("fixed")})
            sev = None
            for s in v.get("severity") or []:
                sev = s.get("score")
            dbsev = (v.get("database_specific") or {}).get("severity")
            details.append({"id": vid, "package": f["package"], "summary": (v.get("summary") or "")[:160],
                            "severity": dbsev or sev, "fixed_in": fixed[:5],
                            "url": "https://osv.dev/vulnerability/" + vid})
    out({"ok": True, "checked": len(deps), "vulnerable": findings, "details": details})


# --------------------------------------------------------------------------- Confluence
class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "table"}

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.parts.append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in ("td", "th"):
            self.parts.append(" | ")
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        t = html.unescape("".join(self.parts))
        t = re.sub(r"[ \t]+", " ", t)
        return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def html_to_text(markup):
    p = _Text()
    p.feed(markup or "")
    return p.text()


class Confluence:
    def __init__(self):
        self.base = (os.environ.get("CONFLUENCE_BASE_URL") or "").rstrip("/")
        self.token = os.environ.get("CONFLUENCE_API_TOKEN") or ""
        self.user = os.environ.get("CONFLUENCE_USER") or ""
        self.auth = (os.environ.get("CONFLUENCE_AUTH_TYPE") or "basic").lower()
        if not self.base or not self.token:
            fail(2, "CONFLUENCE_BASE_URL and CONFLUENCE_API_TOKEN must be set")
        if self.auth == "basic" and not self.user:
            fail(2, "CONFLUENCE_USER must be set for basic auth (or set CONFLUENCE_AUTH_TYPE=bearer)")

    def headers(self):
        if self.auth == "bearer":
            return {"Authorization": "Bearer " + self.token}
        raw = ("%s:%s" % (self.user, self.token)).encode()
        return {"Authorization": "Basic " + base64.b64encode(raw).decode()}

    def get(self, path, params=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return http_json(url, headers=self.headers())

    def link(self, webui):
        return self.base + webui if webui else None


def cmd_confluence_search(a):
    c = Confluence()
    text = a.text.replace('"', '\\"')
    cql = 'type = page AND (title ~ "%s" OR text ~ "%s")' % (text, text)
    if a.space:
        cql += ' AND space = "%s"' % a.space
    res = c.get("/rest/api/content/search", {"cql": cql, "limit": a.max, "expand": "space,version"})
    pages = [{"id": r.get("id"), "title": r.get("title"), "space": (r.get("space") or {}).get("key"),
              "updated": (r.get("version") or {}).get("when"),
              "url": c.link((r.get("_links") or {}).get("webui"))} for r in res.get("results") or []]
    out({"ok": True, "count": len(pages), "pages": pages})


def cmd_confluence_page(a):
    c = Confluence()
    r = c.get("/rest/api/content/%s" % a.page_id, {"expand": "body.storage,version,space"})
    text = html_to_text(((r.get("body") or {}).get("storage") or {}).get("value"))
    trimmed = text if len(text) <= a.max_chars else text[:a.max_chars] + "\n...[truncated %d chars]" % (len(text) - a.max_chars)
    out({"ok": True, "id": r.get("id"), "title": r.get("title"), "space": (r.get("space") or {}).get("key"),
         "version": (r.get("version") or {}).get("number"), "updated": (r.get("version") or {}).get("when"),
         "url": c.link((r.get("_links") or {}).get("webui")), "text": trimmed})


# --------------------------------------------------------------------------- allow-list
def load_allowed(config_path):
    """Read research.allowed_domains from the YAML config without a YAML library."""
    if not os.path.exists(config_path):
        return []
    with open(config_path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"(?ms)^research:\s*\n(.*?)(?=^\S|\Z)", text)
    if not m:
        return []
    block = m.group(1)
    inline = re.search(r"(?m)^[ \t]+allowed_domains:[ \t]*\[(.*?)\]", block)
    if inline:
        return [d.strip().strip("'\"") for d in inline.group(1).split(",") if d.strip()]
    listed = re.search(r"(?m)^[ \t]+allowed_domains:[ \t]*(?:#.*)?\n((?:[ \t]+-[ \t]+.*(?:\n|$))+)", block)
    if listed:
        return [re.sub(r"^\s*-\s*", "", l).split("#")[0].strip().strip("'\"") for l in listed.group(1).splitlines() if l.strip()]
    return []


def cmd_allowed(a):
    host = (urllib.parse.urlsplit(a.url).hostname or "").lower()
    domains = load_allowed(a.config)
    ok = any(host == d.lower() or host.endswith("." + d.lower()) for d in domains)
    out({"ok": True, "url": a.url, "host": host, "allowed": ok, "allow_list_size": len(domains)})


def main(argv=None):
    p = argparse.ArgumentParser(prog="research_cli.py", description="Read-only research helper")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("versions"); s.add_argument("--path", default="."); s.add_argument("--match")
    s = sub.add_parser("osv"); s.add_argument("--path", default=".")
    s.add_argument("--package", action="append", help="PyPI:name==1.2.3 or npm:name@1.2.3; repeatable")
    s.add_argument("--include-dev", action="store_true"); s.add_argument("--details", type=int, default=5)
    s = sub.add_parser("confluence-search"); s.add_argument("text"); s.add_argument("--space")
    s.add_argument("--max", type=int, default=10)
    s = sub.add_parser("confluence-page"); s.add_argument("page_id"); s.add_argument("--max-chars", type=int, default=12000)
    s = sub.add_parser("allowed"); s.add_argument("url"); s.add_argument("--config", default=CONFIG_PATH)
    a = p.parse_args(argv)
    globals()["cmd_" + a.cmd.replace("-", "_")](a)


if __name__ == "__main__":
    main()
