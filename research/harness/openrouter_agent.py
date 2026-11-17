"""A minimal coding-agent loop for a model on OpenRouter (Study E3: a model of a different supplier).

  python openrouter_agent.py RUNS_DIR RUN_ID --model MODEL [--max-turns 80] [--max-minutes 40]

The prompt is the exact text of RUNS_DIR/<RUN_ID>.prompt.txt. The agent gets four tools, close to the tools of the
Claude agents of Studies A to C: read_file, write_file, edit_file and bash (Git Bash on Windows, working directory =
the workspace). The transcript goes to RUNS_DIR/transcripts/<RUN_ID>.jsonl and the run record to
RUNS_DIR/records/<RUN_ID>.json (tokens, cost, turns, stop reason). Both are outside the workspace.

The OpenRouter key is read from ~/.openrouter_key and is sent only to openrouter.ai. It is never printed or written.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://openrouter.ai/api/v1/chat/completions"
BASH = "C:/Program Files/Git/bin/bash.exe"
OUT_LIMIT = 12000
SYSTEM = ("You are an autonomous software engineering agent. You work alone: nobody answers questions. Use the tools to "
          "read and change the code, then reply with your final answer when the task is done. Use forward slashes in paths.")
TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file. Returns numbered lines.",
     "parameters": {"type": "object", "properties": {
         "path": {"type": "string", "description": "Absolute path or path relative to the repository"},
         "offset": {"type": "integer", "description": "First line (1-based), optional"},
         "limit": {"type": "integer", "description": "Number of lines, optional (default 400)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create or overwrite a file with the given content.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file",
     "description": "Replace one exact, unique occurrence of old_string with new_string in a file.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_string": {"type": "string"},
                                                     "new_string": {"type": "string"}},
                    "required": ["path", "old_string", "new_string"]}}},
    {"type": "function", "function": {"name": "bash",
     "description": "Run a shell command (Git Bash) in the repository directory. Returns stdout and stderr (cut to 12000 characters).",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"},
                                                     "timeout": {"type": "integer", "description": "Seconds, default 600"}},
                    "required": ["command"]}}},
]


def resolve(ws, path):
    p = path.replace("\\", "/")
    return p if re.match(r"^[A-Za-z]:/|^/", p) else f"{ws}/{p}"


def tool(ws, name, args):
    try:
        if name == "read_file":
            p = resolve(ws, args["path"])
            lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
            start = max(1, int(args.get("offset") or 1))
            n = int(args.get("limit") or 400)
            out = "\n".join(f"{i}\t{lines[i - 1]}" for i in range(start, min(len(lines), start + n - 1) + 1))
            return out[:OUT_LIMIT * 2] or "(empty file or offset past the end)"
        if name == "write_file":
            p = resolve(ws, args["path"])
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(args["content"])
            return f"wrote {p}"
        if name == "edit_file":
            p = resolve(ws, args["path"])
            text = open(p, encoding="utf-8", newline="").read()
            old, new = args["old_string"], args["new_string"]
            if "\r\n" in text and "\r\n" not in old:  # the model writes \n; the file can have CRLF
                old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
            n = text.count(old)
            if n != 1:
                return f"error: old_string occurs {n} times; it must occur exactly once"
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(text.replace(old, new))
            return f"edited {p}"
        if name == "bash":
            t = min(int(args.get("timeout") or 600), 900)
            r = subprocess.run([BASH, "-c", args["command"]], cwd=ws, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=t)
            out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
            if len(out) > OUT_LIMIT:
                out = out[:OUT_LIMIT // 2] + "\n...[cut]...\n" + out[-OUT_LIMIT // 2:]
            return f"[exit code {r.returncode}]\n{out}"
        return f"error: unknown tool {name}"
    except subprocess.TimeoutExpired:
        return "error: the command timed out"
    except Exception as exc:  # the agent sees the error, as with any tool
        return f"error: {type(exc).__name__}: {exc}"


def call(key, body, tries=6):
    for i in range(tries):
        req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json", "X-Title": "research-harness"})
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            code = getattr(exc, "code", None)
            if code in (400, 401, 402, 403) or i == tries - 1:
                raise RuntimeError(f"request failed: {type(exc).__name__} {code}") from None
            time.sleep(10 * (i + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("run_id")
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-turns", type=int, default=80)
    ap.add_argument("--max-minutes", type=float, default=40)
    a = ap.parse_args()
    key = open(os.path.expanduser("~/.openrouter_key"), encoding="utf-8").read().strip()
    prompt = open(f"{a.runs_dir}/{a.run_id}.prompt.txt", encoding="utf-8").read()
    ws = re.search(r"repository at (\S+)", prompt).group(1).rstrip("/")
    for d in ("transcripts", "records"):
        os.makedirs(f"{a.runs_dir}/{d}", exist_ok=True)
    tpath = f"{a.runs_dir}/transcripts/{a.run_id}.jsonl"
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    rec = {"run": a.run_id, "model": a.model, "turns": 0, "tool_calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
           "cached_tokens": 0, "cost": 0.0, "stop": None, "models_seen": []}
    t0 = time.time()
    with open(tpath, "w", encoding="utf-8") as tf:
        tf.write(json.dumps({"role": "user", "content": prompt}) + "\n")
        while True:
            if rec["turns"] >= a.max_turns:
                rec["stop"] = "max_turns"
                break
            if time.time() - t0 > a.max_minutes * 60:
                rec["stop"] = "max_minutes"
                break
            try:
                r = call(key, {"model": a.model, "messages": msgs, "tools": TOOLS, "usage": {"include": True}})
            except RuntimeError as exc:
                rec["stop"] = f"error: {exc}"
                break
            rec["turns"] += 1
            u = r.get("usage") or {}
            rec["prompt_tokens"] += u.get("prompt_tokens", 0)
            rec["completion_tokens"] += u.get("completion_tokens", 0)
            rec["cached_tokens"] += (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
            rec["cost"] += float(u.get("cost") or 0)
            if r.get("model") and r["model"] not in rec["models_seen"]:
                rec["models_seen"].append(r["model"])
            if not r.get("choices"):
                rec["stop"] = f"error: no choices: {str(r)[:200]}"
                break
            m = r["choices"][0]["message"]
            msg = {"role": "assistant", "content": m.get("content") or ""}
            if m.get("tool_calls"):
                msg["tool_calls"] = m["tool_calls"]
            msgs.append(msg)
            tf.write(json.dumps(msg, ensure_ascii=False) + "\n")
            if not m.get("tool_calls"):
                rec["stop"] = "final"
                rec["final"] = (m.get("content") or "")[:2000]
                break
            for c in m["tool_calls"]:
                rec["tool_calls"] += 1
                try:
                    args = json.loads(c["function"].get("arguments") or "{}")
                except ValueError:
                    args = {}
                out = tool(ws, c["function"]["name"], args) if args else "error: the arguments are not valid JSON"
                tm = {"role": "tool", "tool_call_id": c["id"], "content": out}
                msgs.append(tm)
                tf.write(json.dumps({**tm, "name": c["function"]["name"], "args": args}, ensure_ascii=False) + "\n")
            tf.flush()
    rec["seconds"] = round(time.time() - t0, 1)
    json.dump(rec, open(f"{a.runs_dir}/records/{a.run_id}.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps({k: rec[k] for k in ("run", "stop", "turns", "tool_calls", "cost", "seconds")}))


if __name__ == "__main__":
    sys.exit(main())
