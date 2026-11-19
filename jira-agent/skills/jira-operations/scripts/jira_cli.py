#!/usr/bin/env python3
"""
jira_cli.py - compact Jira REST helper for the AI SDLC factory.

Standard library only (Python 3.8+). Works with Jira Cloud (REST v3, ADF) and
Jira Server / Data Center (REST v2, plain text). Prints compact JSON to stdout.

Environment
  JIRA_BASE_URL     e.g. https://jira.example.com  or  https://acme.atlassian.net
  JIRA_USER         Cloud: account email. DC with basic auth: username. Not needed for bearer.
  JIRA_API_TOKEN    Cloud: API token. DC: personal access token (PAT) or password.
  JIRA_AUTH_TYPE    basic (default) | bearer   (bearer = DC personal access token)
  JIRA_API_VERSION  2 | 3   (default: 3 for *.atlassian.net, otherwise 2)
  JIRA_DRY_RUN      1 = never send write requests, print them instead
  JIRA_AC_FIELD     optional name of the custom field that holds acceptance criteria
  JIRA_TIMEOUT      seconds per request (default 30)

Exit codes: 0 ok, 2 configuration, 3 HTTP error, 4 not found, 5 bad input.
Secrets are never printed.
"""
import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

CACHE_DEFAULT = ".sdlc/jira-fields.json"
READ_LIMIT_CHARS = 4000


# --------------------------------------------------------------------------- output
def out(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def fail(code, message, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.exit(code)


# --------------------------------------------------------------------------- client
class Jira:
    def __init__(self, dry_run=False):
        self.base = (os.environ.get("JIRA_BASE_URL") or "").rstrip("/")
        self.user = os.environ.get("JIRA_USER") or ""
        self.token = os.environ.get("JIRA_API_TOKEN") or ""
        self.auth_type = (os.environ.get("JIRA_AUTH_TYPE") or "basic").lower()
        if not self.base or not self.token:
            fail(2, "JIRA_BASE_URL and JIRA_API_TOKEN must be set")
        if self.auth_type == "basic" and not self.user:
            fail(2, "JIRA_USER must be set for basic auth (or set JIRA_AUTH_TYPE=bearer)")
        default_ver = "3" if "atlassian.net" in self.base else "2"
        self.ver = os.environ.get("JIRA_API_VERSION") or default_ver
        self.cloud = self.ver == "3"
        self.dry_run = dry_run or os.environ.get("JIRA_DRY_RUN") == "1"
        self.timeout = int(os.environ.get("JIRA_TIMEOUT") or "30")
        self._me = None

    # -- low level
    def _headers(self, extra=None):
        h = {"Accept": "application/json"}
        if self.auth_type == "bearer":
            h["Authorization"] = "Bearer " + self.token
        else:
            raw = ("%s:%s" % (self.user, self.token)).encode()
            h["Authorization"] = "Basic " + base64.b64encode(raw).decode()
        if extra:
            h.update(extra)
        return h

    def api(self, path):
        return "/rest/api/%s/%s" % (self.ver, path.lstrip("/"))

    def request(self, method, path, body=None, params=None, write=False, raw_body=None, headers=None):
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        if write and self.dry_run:
            return {"dry_run": True, "method": method, "path": path, "params": params, "body": body}
        data = raw_body
        hdrs = self._headers(headers)
        if body is not None:
            data = json.dumps(body).encode()
            hdrs["Content-Type"] = "application/json"
        for attempt in range(4):
            req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    text = resp.read().decode("utf-8") if resp.length != 0 else ""
                    return json.loads(text) if text.strip() else {}
            except urllib.error.HTTPError as e:
                retry = e.code in (429, 502, 503, 504) and attempt < 3
                if retry:
                    wait = e.headers.get("Retry-After")
                    time.sleep(min(int(wait), 30) if wait and wait.isdigit() else 2 ** attempt)
                    continue
                detail = ""
                try:
                    detail = json.loads(e.read().decode("utf-8"))
                    detail = {"messages": detail.get("errorMessages"), "fields": detail.get("errors")}
                except Exception:
                    pass
                fail(4 if e.code == 404 else 3, "HTTP %s on %s %s" % (e.code, method, path), detail=detail)
            except urllib.error.URLError as e:
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                fail(3, "Cannot reach Jira: %s" % e.reason)
        fail(3, "Request failed after retries")

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def browse(self, key):
        return "%s/browse/%s" % (self.base, key)

    # -- identity
    def me(self):
        if self._me is None:
            self._me = self.get(self.api("myself"))
        return self._me

    def user_ref(self, who):
        """Return the JSON reference for a user: Cloud {"accountId"}, DC {"name"}."""
        if who in (None, "", "none", "unassigned"):
            return None
        if who == "me":
            m = self.me()
            return {"accountId": m["accountId"]} if self.cloud else {"name": m.get("name")}
        if self.cloud:
            if re.fullmatch(r"[0-9a-f:\-]{20,}", who):
                return {"accountId": who}
            found = self.get(self.api("user/search"), {"query": who})
            if not found:
                fail(5, "No Jira user matches '%s'" % who)
            return {"accountId": found[0]["accountId"]}
        return {"name": who}

    # -- fields
    def fields(self, cache_path, refresh=False):
        if not refresh and os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
        raw = self.get(self.api("field"))
        mapping = {}
        for fld in raw:
            schema = fld.get("schema") or {}
            mapping[fld["name"].lower()] = {
                "id": fld["id"],
                "name": fld["name"],
                "type": schema.get("type"),
                "custom": schema.get("custom"),
            }
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=1)
        return mapping

    def field_id(self, name, cache_path):
        if re.fullmatch(r"customfield_\d+|[a-z]+", name):
            return name, None
        info = self.fields(cache_path).get(name.lower())
        if not info:
            info = self.fields(cache_path, refresh=True).get(name.lower())
        if not info:
            fail(5, "Unknown Jira field '%s'. Run: fields --refresh" % name)
        return info["id"], info


# --------------------------------------------------------------------------- text <-> ADF
def text_to_adf(text):
    """Convert simple markdown-like text into Atlassian Document Format (Cloud)."""
    content, para, bullets, ordered = [], [], None, None
    lines = (text or "").replace("\r\n", "\n").split("\n")

    def flush_para():
        if para:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": " ".join(para)}]})
            para.clear()

    def item(t):
        return {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": t}]}]}

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para()
            bullets = ordered = None
            lang = stripped[3:].strip() or None
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            node = {"type": "codeBlock", "content": [{"type": "text", "text": "\n".join(code) or " "}]}
            if lang:
                node["attrs"] = {"language": lang}
            content.append(node)
        elif re.match(r"^#{1,6} ", stripped):
            flush_para()
            bullets = ordered = None
            level = len(stripped.split(" ")[0])
            content.append({"type": "heading", "attrs": {"level": level},
                            "content": [{"type": "text", "text": stripped[level + 1:]}]})
        elif re.match(r"^[-*] ", stripped):
            flush_para()
            ordered = None
            if bullets is None:
                bullets = {"type": "bulletList", "content": []}
                content.append(bullets)
            bullets["content"].append(item(stripped[2:]))
        elif re.match(r"^\d+[.)] ", stripped):
            flush_para()
            bullets = None
            if ordered is None:
                ordered = {"type": "orderedList", "content": []}
                content.append(ordered)
            ordered["content"].append(item(re.sub(r"^\d+[.)] ", "", stripped)))
        elif not stripped:
            flush_para()
            bullets = ordered = None
        else:
            bullets = ordered = None
            para.append(stripped)
        i += 1
    flush_para()
    if not content:
        content = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": content}


def adf_to_text(node):
    """Flatten ADF (or a plain string) to readable text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    t = node.get("type")
    kids = node.get("content") or []
    if t == "text":
        return node.get("text", "")
    if t in ("hardBreak",):
        return "\n"
    if t == "mention":
        return "@" + (node.get("attrs", {}).get("text") or "user").lstrip("@")
    if t == "inlineCard":
        return node.get("attrs", {}).get("url", "")
    inner = "".join(adf_to_text(k) for k in kids)
    if t == "heading":
        return "#" * node.get("attrs", {}).get("level", 1) + " " + inner + "\n"
    if t == "paragraph":
        return inner + "\n"
    if t == "codeBlock":
        return "```\n" + inner + "\n```\n"
    if t == "listItem":
        return inner
    if t == "bulletList":
        return "".join("- " + adf_to_text(k).strip() + "\n" for k in kids)
    if t == "orderedList":
        return "".join("%d. %s\n" % (n + 1, adf_to_text(k).strip()) for n, k in enumerate(kids))
    if t == "doc":
        return inner.strip()
    return inner


def body_value(jira, text):
    return text_to_adf(text) if jira.cloud else text


def read_text(arg_text, arg_file):
    if arg_file:
        with open(arg_file, encoding="utf-8") as f:
            return f.read()
    return arg_text


def clip(text, limit):
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "\n...[truncated %d chars]" % (len(text) - limit)


def parse_value(raw):
    raw = raw.strip()
    if raw[:1] in "{[" or re.fullmatch(r"-?\d+(\.\d+)?|true|false|null", raw):
        try:
            return json.loads(raw)
        except ValueError:
            pass
    return raw


def extract_ac(text):
    """Pull an 'Acceptance Criteria' section out of a description."""
    m = re.search(r"(?im)^\s*#*\s*\**acceptance criteria\**\s*:?\s*$", text or "")
    if not m:
        return None
    rest = text[m.end():]
    stop = re.search(r"(?m)^\s*#{1,6} \S|^\s*\*\*[^*]+\*\*\s*:?\s*$", rest)
    return (rest[:stop.start()] if stop else rest).strip() or None


# --------------------------------------------------------------------------- shaping
def name_of(obj, *keys):
    if not obj:
        return None
    for k in keys:
        if obj.get(k):
            return obj[k]
    return None


def compact_issue(jira, issue, max_chars=READ_LIMIT_CHARS, ac_field_id=None, comments=None):
    f = issue.get("fields", {})
    desc = adf_to_text(f.get("description"))
    ac = None
    if ac_field_id and f.get(ac_field_id):
        ac = adf_to_text(f.get(ac_field_id))
    if not ac:
        ac = extract_ac(desc)
    sprint = None
    for k, v in f.items():
        if not (k.startswith("customfield_") and isinstance(v, list) and v):
            continue
        if isinstance(v[0], dict) and "state" in v[0] and "name" in v[0]:          # Cloud
            active = [s for s in v if s.get("state") == "active"] or v
            sprint = active[-1].get("name")
        elif isinstance(v[0], str) and "com.atlassian.greenhopper" in v[0]:          # Data Center
            names = re.findall(r"name=([^,\]]+)", v[-1])
            sprint = names[0] if names else None
    result = {
        "key": issue.get("key"),
        "url": jira.browse(issue.get("key")),
        "summary": f.get("summary"),
        "type": name_of(f.get("issuetype"), "name"),
        "status": name_of(f.get("status"), "name"),
        "priority": name_of(f.get("priority"), "name"),
        "assignee": name_of(f.get("assignee"), "displayName", "name"),
        "reporter": name_of(f.get("reporter"), "displayName", "name"),
        "labels": f.get("labels") or [],
        "components": [c.get("name") for c in f.get("components") or []],
        "fix_versions": [v.get("name") for v in f.get("fixVersions") or []],
        "parent": (f.get("parent") or {}).get("key"),
        "sprint": sprint,
        "created": f.get("created"),
        "updated": f.get("updated"),
        "description": clip(desc, max_chars) if desc else None,
        "acceptance_criteria": clip(ac, max_chars) if ac else None,
        "subtasks": [{"key": s.get("key"), "summary": s.get("fields", {}).get("summary"),
                      "status": name_of(s.get("fields", {}).get("status"), "name")} for s in f.get("subtasks") or []],
        "links": [],
        "attachments": [a.get("filename") for a in f.get("attachment") or []],
    }
    for link in f.get("issuelinks") or []:
        other = link.get("outwardIssue") or link.get("inwardIssue") or {}
        rel = (link.get("type") or {}).get("outward" if link.get("outwardIssue") else "inward")
        result["links"].append({"relation": rel, "key": other.get("key"),
                                "summary": (other.get("fields") or {}).get("summary")})
    if comments is not None:
        result["comments"] = comments
    return {k: v for k, v in result.items() if v not in (None, [], "")}


def compact_comment(c, max_chars=800):
    return {"id": c.get("id"), "author": name_of(c.get("author"), "displayName", "name"),
            "created": c.get("created"), "body": clip(adf_to_text(c.get("body")), max_chars)}


# --------------------------------------------------------------------------- field building
def build_fields(jira, args, cache, creating=False):
    fields = {}
    if creating:
        fields["project"] = {"key": args.project}
        fields["issuetype"] = {"name": args.type}
    if getattr(args, "summary", None):
        fields["summary"] = args.summary
    desc = read_text(getattr(args, "description", None), getattr(args, "description_file", None))
    if desc is not None:
        fields["description"] = body_value(jira, desc)
    if getattr(args, "priority", None):
        fields["priority"] = {"name": args.priority}
    if creating and getattr(args, "labels", None):
        labels = [l for l in args.labels.split(",") if l]
        if labels:
            fields["labels"] = labels
    if getattr(args, "components", None):
        fields["components"] = [{"name": c.strip()} for c in args.components.split(",") if c.strip()]
    if getattr(args, "fix_versions", None):
        fields["fixVersions"] = [{"name": v.strip()} for v in args.fix_versions.split(",") if v.strip()]
    if getattr(args, "assignee", None):
        fields["assignee"] = jira.user_ref(args.assignee)
    if getattr(args, "parent", None):
        fields["parent"] = {"key": args.parent}
    for pair in getattr(args, "field", None) or []:
        if "=" not in pair:
            fail(5, "--field needs NAME=VALUE, got '%s'" % pair)
        name, raw = pair.split("=", 1)
        fid, info = jira.field_id(name.strip(), cache)
        value = parse_value(raw)
        if info and info.get("type") == "number" and isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                fail(5, "Field '%s' needs a number" % name)
        if info and info.get("type") in ("string",) and jira.cloud and (info.get("custom") or "").endswith("textarea"):
            value = text_to_adf(str(value))
        fields[fid] = value
    return fields


# --------------------------------------------------------------------------- commands
def cmd_whoami(j, a):
    m = j.me()
    out({"ok": True, "user": name_of(m, "displayName", "name"), "account": m.get("accountId") or m.get("name"),
         "api_version": j.ver, "base_url": j.base})


def cmd_get(j, a):
    ac_id = None
    if a.ac_field or os.environ.get("JIRA_AC_FIELD"):
        ac_id, _ = j.field_id(a.ac_field or os.environ["JIRA_AC_FIELD"], a.cache)
    issue = j.get(j.api("issue/%s" % a.key))
    comments = None
    if a.comments:
        raw = j.get(j.api("issue/%s/comment" % a.key), {"maxResults": a.comments, "orderBy": "-created"})
        comments = [compact_comment(c) for c in (raw.get("comments") or [])][-a.comments:]
    out({"ok": True, "issue": compact_issue(j, issue, a.max_chars, ac_id, comments)})


def cmd_search(j, a):
    fields = "summary,status,issuetype,priority,assignee,labels,parent,updated"
    if j.cloud:
        raw = j.request("POST", j.api("search/jql"),
                        body={"jql": a.jql, "maxResults": a.max, "fields": fields.split(",")})
    else:
        raw = j.get(j.api("search"), {"jql": a.jql, "maxResults": a.max, "fields": fields})
    issues = []
    for it in raw.get("issues") or []:
        f = it.get("fields", {})
        issues.append({k: v for k, v in {
            "key": it.get("key"), "summary": f.get("summary"),
            "type": name_of(f.get("issuetype"), "name"), "status": name_of(f.get("status"), "name"),
            "priority": name_of(f.get("priority"), "name"),
            "assignee": name_of(f.get("assignee"), "displayName", "name"),
            "labels": f.get("labels") or None, "parent": (f.get("parent") or {}).get("key"),
        }.items() if v is not None})
    out({"ok": True, "count": len(issues), "total": raw.get("total"), "issues": issues})


def find_existing(j, project, summary, label):
    safe = summary.replace('"', '\\"')
    jql = 'project = "%s" AND labels = "%s" AND summary ~ "\\"%s\\""' % (project, label, safe)
    if j.cloud:
        raw = j.request("POST", j.api("search/jql"), body={"jql": jql, "maxResults": 10, "fields": ["summary"]})
    else:
        raw = j.get(j.api("search"), {"jql": jql, "maxResults": 10, "fields": "summary"})
    for it in raw.get("issues") or []:
        if (it.get("fields") or {}).get("summary", "").strip().lower() == summary.strip().lower():
            return it.get("key")
    return None


def create_one(j, a, cache):
    if a.idempotency_label:
        labels = [l for l in (a.labels or "").split(",") if l]
        if a.idempotency_label not in labels:
            labels.append(a.idempotency_label)
        a.labels = ",".join(labels)
        if not j.dry_run:
            existing = find_existing(j, a.project, a.summary, a.idempotency_label)
            if existing:
                return {"key": existing, "url": j.browse(existing), "created": False, "reason": "already exists"}
    fields = build_fields(j, a, cache, creating=True)
    res = j.request("POST", j.api("issue"), body={"fields": fields}, write=True)
    if res.get("dry_run"):
        return res
    return {"key": res.get("key"), "url": j.browse(res.get("key")), "created": True}


def cmd_create(j, a):
    out({"ok": True, "result": create_one(j, a, a.cache)})


def cmd_subtask(j, a):
    parent = j.get(j.api("issue/%s" % a.parent), {"fields": "project"})
    a.project = parent["fields"]["project"]["key"]
    a.type = a.type or ("Subtask" if j.cloud else "Sub-task")
    out({"ok": True, "result": create_one(j, a, a.cache)})


def cmd_update(j, a):
    fields = build_fields(j, a, a.cache)
    update = {}
    if a.add_label or a.remove_label:
        update["labels"] = [{"add": l} for l in (a.add_label or [])] + [{"remove": l} for l in (a.remove_label or [])]
    if not fields and not update:
        fail(5, "Nothing to update")
    body = {}
    if fields:
        body["fields"] = fields
    if update:
        body["update"] = update
    res = j.request("PUT", j.api("issue/%s" % a.key), body=body, params={"notifyUsers": "false"} if a.quiet else None, write=True)
    out({"ok": True, "key": a.key, "updated": sorted(list(fields) + list(update)), **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_comment(j, a):
    text = read_text(a.body, a.body_file)
    if not text:
        fail(5, "Comment body is empty")
    res = j.request("POST", j.api("issue/%s/comment" % a.key), body={"body": body_value(j, text)}, write=True)
    out({"ok": True, "key": a.key, "comment_id": res.get("id"), **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_comment_list(j, a):
    raw = j.get(j.api("issue/%s/comment" % a.key), {"maxResults": 100})
    comments = [compact_comment(c, a.max_chars) for c in raw.get("comments") or []]
    out({"ok": True, "key": a.key, "count": len(comments), "comments": comments[-a.last:]})


def cmd_comment_edit(j, a):
    text = read_text(a.body, a.body_file)
    res = j.request("PUT", j.api("issue/%s/comment/%s" % (a.key, a.comment_id)), body={"body": body_value(j, text)}, write=True)
    out({"ok": True, "key": a.key, "comment_id": a.comment_id, **({"dry_run": res} if res.get("dry_run") else {})})


def list_transitions(j, key):
    raw = j.get(j.api("issue/%s/transitions" % key))
    return [{"id": t["id"], "name": t["name"], "to": (t.get("to") or {}).get("name")} for t in raw.get("transitions") or []]


def cmd_transitions(j, a):
    out({"ok": True, "key": a.key, "transitions": list_transitions(j, a.key)})


def cmd_transition(j, a):
    available = list_transitions(j, a.key)
    target = a.to.strip().lower()
    match = next((t for t in available if t["name"].lower() == target or (t["to"] or "").lower() == target), None)
    if not match:
        fail(5, "Transition '%s' not available for %s" % (a.to, a.key), available=available)
    body = {"transition": {"id": match["id"]}}
    if a.resolution:
        body["fields"] = {"resolution": {"name": a.resolution}}
    if a.comment:
        body["update"] = {"comment": [{"add": {"body": body_value(j, a.comment)}}]}
    res = j.request("POST", j.api("issue/%s/transitions" % a.key), body=body, write=True)
    out({"ok": True, "key": a.key, "transition": match["name"], "to": match["to"],
         **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_assign(j, a):
    ref = j.user_ref(a.user)
    body = ref if ref else ({"accountId": None} if j.cloud else {"name": None})
    res = j.request("PUT", j.api("issue/%s/assignee" % a.key), body=body, write=True)
    out({"ok": True, "key": a.key, "assignee": a.user, **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_link_types(j, a):
    raw = j.get(j.api("issueLinkType"))
    out({"ok": True, "types": [{"name": t["name"], "outward": t["outward"], "inward": t["inward"]}
                               for t in raw.get("issueLinkTypes") or []]})


def cmd_link(j, a):
    body = {"type": {"name": a.type}, "inwardIssue": {"key": a.key}, "outwardIssue": {"key": a.to}}
    if a.comment:
        body["comment"] = {"body": body_value(j, a.comment)}
    res = j.request("POST", j.api("issueLink"), body=body, write=True)
    out({"ok": True, "from": a.key, "to": a.to, "type": a.type, **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_remote_link(j, a):
    body = {"object": {"url": a.url, "title": a.title}}
    res = j.request("POST", j.api("issue/%s/remotelink" % a.key), body=body, write=True)
    out({"ok": True, "key": a.key, "url": a.url, **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_sprints(j, a):
    raw = j.get("/rest/agile/1.0/board/%s/sprint" % a.board, {"state": a.state})
    out({"ok": True, "sprints": [{"id": s["id"], "name": s["name"], "state": s["state"]} for s in raw.get("values") or []]})


def cmd_sprint_move(j, a):
    keys = [k.strip() for k in a.keys.split(",") if k.strip()]
    res = j.request("POST", "/rest/agile/1.0/sprint/%s/issue" % a.sprint_id, body={"issues": keys}, write=True)
    out({"ok": True, "sprint_id": a.sprint_id, "moved": keys, **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_fields(j, a):
    mapping = j.fields(a.cache, refresh=a.refresh)
    if a.match:
        mapping = {k: v for k, v in mapping.items() if a.match.lower() in k}
    out({"ok": True, "count": len(mapping), "fields": {v["name"]: v["id"] for v in mapping.values()}})


def cmd_create_meta(j, a):
    if True:  # same endpoints on Cloud and Data Center 8.4+
        types = j.get(j.api("issue/createmeta/%s/issuetypes" % a.project))
        values = types.get("values") or types.get("issueTypes") or []
        if not a.type:
            out({"ok": True, "project": a.project, "issue_types": [t.get("name") for t in values]})
            return
        it = next((t for t in values if t.get("name", "").lower() == a.type.lower()), None)
        if not it:
            fail(5, "Issue type '%s' not found in %s" % (a.type, a.project))
        raw = j.get(j.api("issue/createmeta/%s/issuetypes/%s" % (a.project, it["id"])), {"maxResults": 200})
        flds = raw.get("values") or raw.get("fields") or []
        out({"ok": True, "project": a.project, "type": it["name"],
             "required": [f.get("name") for f in flds if f.get("required")],
             "optional": [f.get("name") for f in flds if not f.get("required")]})


def cmd_attach(j, a):
    if not os.path.isfile(a.file):
        fail(5, "File not found: %s" % a.file)
    if j.dry_run:
        out({"ok": True, "dry_run": True, "key": a.key, "file": os.path.basename(a.file)})
        return
    boundary = uuid.uuid4().hex
    with open(a.file, "rb") as f:
        data = f.read()
    ctype = mimetypes.guess_type(a.file)[0] or "application/octet-stream"
    body = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
             % (boundary, os.path.basename(a.file), ctype)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode())
    res = j.request("POST", j.api("issue/%s/attachments" % a.key), raw_body=body, write=True,
                    headers={"X-Atlassian-Token": "no-check", "Content-Type": "multipart/form-data; boundary=" + boundary})
    out({"ok": True, "key": a.key, "attached": [x.get("filename") for x in res] if isinstance(res, list) else os.path.basename(a.file)})


def cmd_worklog(j, a):
    body = {"timeSpent": a.time}
    if a.comment:
        body["comment"] = body_value(j, a.comment)
    res = j.request("POST", j.api("issue/%s/worklog" % a.key), body=body, write=True)
    out({"ok": True, "key": a.key, "time": a.time, **({"dry_run": res} if res.get("dry_run") else {})})


def cmd_bulk_create(j, a):
    with open(a.file, encoding="utf-8") as f:
        specs = json.load(f)
    if not isinstance(specs, list):
        fail(5, "Bulk file must be a JSON list of issue specs")
    results = []
    created_keys = {}
    for n, spec in enumerate(specs):
        ns = argparse.Namespace(**{
            "project": spec.get("project") or a.project, "type": spec.get("type", "Task"),
            "summary": spec["summary"], "description": spec.get("description"), "description_file": None,
            "priority": spec.get("priority"), "labels": ",".join(spec.get("labels", [])),
            "components": ",".join(spec.get("components", [])) or None, "fix_versions": None,
            "assignee": spec.get("assignee"), "parent": spec.get("parent"),
            "field": ["%s=%s" % (k, json.dumps(v) if not isinstance(v, str) else v) for k, v in (spec.get("fields") or {}).items()],
            "idempotency_label": spec.get("idempotency_label") or a.idempotency_label,
        })
        if ns.parent and ns.parent.startswith("@"):
            ns.parent = created_keys.get(ns.parent[1:]) or ns.parent
        if not ns.project and ns.parent:
            ns.project = j.get(j.api("issue/%s" % ns.parent), {"fields": "project"})["fields"]["project"]["key"]
        if ns.parent and spec.get("type") is None:
            ns.type = "Subtask" if j.cloud else "Sub-task"
        res = create_one(j, ns, a.cache)
        if spec.get("ref") and res.get("key"):
            created_keys[spec["ref"]] = res["key"]
        results.append({"ref": spec.get("ref", n), **({k: v for k, v in res.items() if k != "body"} if not res.get("dry_run") else {"dry_run": True, "summary": spec["summary"]})})
    out({"ok": True, "count": len(results), "results": results})


# --------------------------------------------------------------------------- CLI
def main(argv=None):
    p = argparse.ArgumentParser(prog="jira_cli.py", description="Compact Jira REST helper (Cloud + Data Center)")
    p.add_argument("--dry-run", action="store_true", help="print write requests instead of sending them")
    p.add_argument("--cache", default=CACHE_DEFAULT, help="field-name cache path")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami")

    s = sub.add_parser("get"); s.add_argument("key")
    s.add_argument("--comments", type=int, default=0, help="include the last N comments")
    s.add_argument("--max-chars", type=int, default=READ_LIMIT_CHARS)
    s.add_argument("--ac-field", help="custom field name holding acceptance criteria")

    s = sub.add_parser("search"); s.add_argument("jql"); s.add_argument("--max", type=int, default=25)

    def add_issue_fields(s, creating):
        s.add_argument("--summary", required=creating)
        s.add_argument("--description"); s.add_argument("--description-file")
        s.add_argument("--priority"); s.add_argument("--components"); s.add_argument("--fix-versions")
        s.add_argument("--assignee", help="'me', 'none', account id, email or username")
        s.add_argument("--field", action="append", help="NAME=VALUE (custom fields by name); repeatable")

    s = sub.add_parser("create"); s.add_argument("--project", required=True); s.add_argument("--type", default="Task")
    add_issue_fields(s, True); s.add_argument("--labels", default=""); s.add_argument("--parent")
    s.add_argument("--idempotency-label", help="label used to detect an existing identical issue")

    s = sub.add_parser("subtask"); s.add_argument("parent"); s.add_argument("--type")
    add_issue_fields(s, True); s.add_argument("--labels", default=""); s.add_argument("--idempotency-label")

    s = sub.add_parser("update"); s.add_argument("key"); add_issue_fields(s, False)
    s.add_argument("--parent"); s.add_argument("--add-label", action="append"); s.add_argument("--remove-label", action="append")
    s.add_argument("--quiet", action="store_true", help="do not notify watchers (needs permission)")

    s = sub.add_parser("comment"); s.add_argument("key"); s.add_argument("--body"); s.add_argument("--body-file")
    s = sub.add_parser("comment-list"); s.add_argument("key"); s.add_argument("--last", type=int, default=10)
    s.add_argument("--max-chars", type=int, default=800)
    s = sub.add_parser("comment-edit"); s.add_argument("key"); s.add_argument("comment_id")
    s.add_argument("--body"); s.add_argument("--body-file")

    s = sub.add_parser("transitions"); s.add_argument("key")
    s = sub.add_parser("transition"); s.add_argument("key"); s.add_argument("--to", required=True)
    s.add_argument("--comment"); s.add_argument("--resolution")

    s = sub.add_parser("assign"); s.add_argument("key"); s.add_argument("--user", required=True)

    sub.add_parser("link-types")
    s = sub.add_parser("link"); s.add_argument("key"); s.add_argument("--to", required=True)
    s.add_argument("--type", default="Relates"); s.add_argument("--comment")
    s = sub.add_parser("remote-link"); s.add_argument("key"); s.add_argument("--url", required=True); s.add_argument("--title", required=True)

    s = sub.add_parser("sprints"); s.add_argument("--board", required=True); s.add_argument("--state", default="active,future")
    s = sub.add_parser("sprint-move"); s.add_argument("keys", help="comma-separated issue keys"); s.add_argument("--sprint-id", required=True)

    s = sub.add_parser("fields"); s.add_argument("--refresh", action="store_true"); s.add_argument("--match")
    s = sub.add_parser("create-meta"); s.add_argument("--project", required=True); s.add_argument("--type")

    s = sub.add_parser("attach"); s.add_argument("key"); s.add_argument("file")
    s = sub.add_parser("worklog"); s.add_argument("key"); s.add_argument("--time", required=True); s.add_argument("--comment")

    s = sub.add_parser("bulk-create"); s.add_argument("file", help="JSON list of issue specs")
    s.add_argument("--project"); s.add_argument("--idempotency-label")

    a = p.parse_args(argv)
    j = Jira(dry_run=a.dry_run)
    handler = globals()["cmd_" + a.cmd.replace("-", "_")]
    handler(j, a)


if __name__ == "__main__":
    main()
