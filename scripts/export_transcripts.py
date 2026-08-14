#!/usr/bin/env python3
"""Export Buoy debate transcripts from a SQLite DB into a folder of Markdown.

Stdlib only (`sqlite3`) so it runs anywhere — including a bare Render shell against
the production disk DB, with no app dependencies:

    python scripts/export_transcripts.py --db /var/data/buoy.db --out transcripts

To pull everything off a remote shell (Render) as ONE copy-pasteable blob:

    python scripts/export_transcripts.py --db /var/data/buoy.db --bundle
    # copy the base64 between the BEGIN/END markers; decode locally with:
    #   python scripts/export_transcripts.py --unbundle < blob.txt

Per session it writes `<session>.md` (the full message thread + the moderator's
decision log, INCLUDING silent no-ops — H1), plus `index.md` and
`all_sessions.json`.
"""
import argparse
import base64
import datetime
import io
import json
import os
import sqlite3
import sys
import tarfile


def rows(cur, sql, params=()):
    cur.execute(sql, params)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def jload(v):
    if not v:
        return {}
    try:
        return json.loads(v)
    except Exception:
        return {}


def ts(v):
    if not v:
        return "—"
    return str(v).split(".")[0].replace("T", " ")


def export(db_path, out_dir):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    topics = {t["id"]: t["question"] for t in rows(cur, "select id, question from topic")}
    users = {u["id"]: u["display_name"] for u in rows(cur, "select id, display_name from user")}
    mods = {m["id"]: m for m in rows(cur, "select id, model, config from moderator")}
    sessions = rows(cur, "select * from session order by created_at")

    os.makedirs(out_dir, exist_ok=True)
    index = [
        "# Buoy — debate transcripts",
        "",
        f"_Exported {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} "
        f"from `{os.path.basename(db_path)}`._",
        "",
        f"**{len(sessions)} session(s).** Each file has the full message thread plus the "
        "moderator's decision log — every decision, including the silent no-ops (H1: all "
        "decisions are logged).",
        "",
    ]
    all_json = []

    for s in sessions:
        sid = s["id"]
        parts = rows(cur, "select seat_no, user_id from sessionparticipant "
                          "where session_id=? order by seat_no", (sid,))
        seat_by_user = {p["user_id"]: p["seat_no"] for p in parts}
        name_by_seat = {p["seat_no"]: users.get(p["user_id"], "?") for p in parts}
        mod = mods.get(s["moderator_id"], {})
        cver = jload(mod.get("config")).get("constitution_version", "?")
        msgs = rows(cur, "select * from message where session_id=? order by id", (sid,))
        acts = rows(cur, "select * from moderatoraction where session_id=? "
                         "order by after_message_id, id", (sid,))

        def who(m):
            at = m["author_type"]
            if at == "participant":
                seat = seat_by_user.get(m["author_user_id"])
                return f"P{seat} — {users.get(m['author_user_id'], '?')}" if seat else "participant"
            if at == "moderator":
                return "Buoy (moderator)"
            return "system"

        L = [
            f"# Debate `{sid}`",
            "",
            f"- **Topic:** {topics.get(s['topic_id'], '?')}",
            f"- **Status:** {s['status']} · **Created:** {ts(s['created_at'])} · "
            f"**Ended:** {ts(s.get('ended_at'))}"
            + (f" (by {s['ended_by']})" if s.get("ended_by") else ""),
            f"- **Participants:** P1 = {name_by_seat.get(1, '—')} · P2 = {name_by_seat.get(2, '—')}",
            f"- **Moderator:** {mod.get('model', '?')} · constitution {cver}",
            "",
            "## Transcript",
            "",
        ]
        if not msgs:
            L.append("_(no messages)_")
            L.append("")
        for m in msgs:
            if m["author_type"] == "system":
                L.append(f"> *{m['content']}*  ")
                L.append(f"> <sub>{ts(m['created_at'])}</sub>")
                L.append("")
            else:
                L.append(f"**{who(m)}** · <sub>{ts(m['created_at'])}</sub>")
                L.append("")
                L.append(m["content"])
                L.append("")

        L.append("## Moderator decision log")
        L.append("")
        L.append("Every decision made after a participant message, including silent "
                 "no-ops (H1). `posted` = whether it produced a visible message.")
        L.append("")
        if not acts:
            L.append("_(no decisions logged)_")
            L.append("")
        else:
            L.append("| after msg | decision | type | target | crux | posted | rationale |")
            L.append("|---|---|---|---|---|---|---|")
            for a in acts:
                tgt = a.get("target_user_id")
                tgt_lbl = f"P{seat_by_user.get(tgt)}" if tgt and seat_by_user.get(tgt) else "—"
                snap = jload(a.get("state_snapshot"))
                err = snap.get("error", {}).get("type") if isinstance(snap, dict) else None
                rationale = (a.get("rationale") or "").replace("|", "\\|").replace("\n", " ")
                if err:
                    rationale += f" _[api error: {err}]_"
                posted = "yes" if a.get("message_id") else "no"
                L.append(f"| {a['after_message_id']} | {a['decision']} | "
                         f"{a.get('intervention_type') or '—'} | {tgt_lbl} | "
                         f"{a.get('crux_type') or '—'} | {posted} | {rationale} |")
            L.append("")

        with open(os.path.join(out_dir, f"{sid}.md"), "w") as f:
            f.write("\n".join(L) + "\n")

        index.append(f"- [`{sid}.md`]({sid}.md) — {name_by_seat.get(1, '—')} vs "
                     f"{name_by_seat.get(2, '—')} · {s['status']} · {len(msgs)} msgs · "
                     f"{len(acts)} decisions")
        all_json.append({"session": s, "participants": parts, "messages": msgs, "actions": acts})

    with open(os.path.join(out_dir, "index.md"), "w") as f:
        f.write("\n".join(index) + "\n")
    with open(os.path.join(out_dir, "all_sessions.json"), "w") as f:
        json.dump(all_json, f, indent=2, default=str)
    con.close()
    print(f"wrote {len(sessions)} transcript(s) to {out_dir}/", file=sys.stderr)
    return len(sessions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("DATABASE_PATH", "buoy.db"))
    ap.add_argument("--out", default="transcripts")
    ap.add_argument("--bundle", action="store_true",
                    help="also print a base64 tar.gz of --out to stdout (for remote shells)")
    ap.add_argument("--unbundle", action="store_true",
                    help="read a base64 bundle from stdin and unpack it into the CWD")
    args = ap.parse_args()

    if args.unbundle:
        data = sys.stdin.read()
        # tolerate the BEGIN/END markers and surrounding whitespace
        b64 = "".join(line for line in data.splitlines()
                      if line and "TRANSCRIPTS_BUNDLE" not in line)
        blob = base64.b64decode("".join(b64.split()))
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
            tf.extractall(".")
        print("unpacked bundle into ./transcripts/", file=sys.stderr)
        return

    export(args.db, args.out)

    if args.bundle:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            tf.add(args.out, arcname="transcripts")
        print("BEGIN_TRANSCRIPTS_BUNDLE_BASE64")
        print(base64.b64encode(buf.getvalue()).decode())
        print("END_TRANSCRIPTS_BUNDLE_BASE64")


if __name__ == "__main__":
    main()
