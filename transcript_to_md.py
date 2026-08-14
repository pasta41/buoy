#!/usr/bin/env python3
"""Convert a Claude Code JSONL transcript into clean Markdown for PDF export.

Default: include user messages, assistant text, and a compact one-line note per
tool call/result. Internal 'thinking' blocks are excluded unless --thinking.
"""
import json, sys, argparse, datetime

def fmt_ts(ts):
    if not ts: return ""
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return ts

def truncate(s, n=200):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + " …"

def blocks(content):
    """Yield (kind, block) from a message content that may be str or list."""
    if isinstance(content, str):
        yield ("text", {"type": "text", "text": content})
    elif isinstance(content, list):
        for b in content:
            if isinstance(b, dict):
                yield (b.get("type", "?"), b)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("-o", "--out", default="-")
    ap.add_argument("--thinking", action="store_true", help="include internal thinking blocks")
    args = ap.parse_args()

    out = []
    out.append("# Session Transcript\n")
    out.append(f"*Source:* `{args.infile}`  \n")
    out.append(f"*Rendered:* {fmt_ts(datetime.datetime.utcnow().isoformat()+'Z')}\n")
    out.append("\n---\n")

    with open(args.infile) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            t = o.get("type")
            if t not in ("user", "assistant"):
                continue
            msg = o.get("message", {})
            content = msg.get("content")

            if t == "user":
                # Skip pure tool_result turns unless they carry text worth showing
                kinds = [k for k, _ in blocks(content)]
                if kinds and all(k == "tool_result" for k in kinds):
                    for _, b in blocks(content):
                        res = b.get("content", "")
                        if isinstance(res, list):
                            res = " ".join(x.get("text", "") for x in res if isinstance(x, dict))
                        out.append(f"> ↳ *tool result:* {truncate(res, 160)}\n\n")
                    continue
                out.append("## 🧑 Cooper\n\n")
                for _, b in blocks(content):
                    if b.get("type") == "text":
                        out.append(b.get("text", "") + "\n\n")

            elif t == "assistant":
                header_done = False
                for kind, b in blocks(content):
                    if kind == "thinking":
                        if args.thinking:
                            if not header_done:
                                out.append("## 🤖 Claude\n\n"); header_done = True
                            out.append("<details><summary>thinking</summary>\n\n")
                            out.append(b.get("thinking", "") + "\n\n</details>\n\n")
                    elif kind == "text":
                        if not header_done:
                            out.append("## 🤖 Claude\n\n"); header_done = True
                        out.append(b.get("text", "") + "\n\n")
                    elif kind == "tool_use":
                        if not header_done:
                            out.append("## 🤖 Claude\n\n"); header_done = True
                        name = b.get("name", "tool")
                        inp = b.get("input", {})
                        label = inp.get("description") or inp.get("command") or inp.get("file_path") or ""
                        out.append(f"> 🔧 *{name}* — {truncate(label, 140)}\n\n")

    text = "".join(out)
    if args.out == "-":
        sys.stdout.write(text)
    else:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"wrote {args.out} ({len(text)} chars)")

if __name__ == "__main__":
    main()
