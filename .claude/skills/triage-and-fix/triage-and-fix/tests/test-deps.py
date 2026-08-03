#!/usr/bin/env python3
"""Local test harness for ../bin/kwf-deps — no GitHub, no network.

Stubs the `gh` CLI with a python shim driven by a JSON fixture (PRs, labels).
The shim applies mutations (label add/remove/create) to the fixture so
multi-step flows (cascade, lift fixpoint) see evolving state, and logs every
mutating call for assertion.

Run:  python3 tests/test-deps.py
Exit: 0 all pass, 1 failures (prints each).
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_BIN = Path(__file__).resolve().parent.parent / "bin" / "kwf-deps"

SHIM = r'''#!/usr/bin/env python3
import json, os, re, sys

state_path = os.environ["KWF_FAKE_STATE"]
log_path = os.environ["KWF_FAKE_LOG"]
state = json.load(open(state_path))
args = sys.argv[1:]

def save():
    json.dump(state, open(state_path, "w"))

def log(line):
    open(log_path, "a").write(line + "\n")

def pr(n):
    for p in state["prs"]:
        if p["number"] == n:
            return p
    print(f"GraphQL: Could not resolve to a PullRequest with the number of {n}.", file=sys.stderr)
    sys.exit(1)

def label_names(p):
    return [l["name"] for l in p["labels"]]

# gh pr view N --repo R --json fields
if args[0] == "pr" and args[1] == "view":
    n = int(args[2])
    print(json.dumps(pr(n)))
# gh pr list --repo R --state open --json ... --limit N
elif args[0] == "pr" and args[1] == "list":
    print(json.dumps([p for p in state["prs"] if p["state"] == "OPEN"]))
# gh label list ...
elif args[0] == "label" and args[1] == "list":
    print(json.dumps([{"name": n} for n in state["labels"]]))
# gh label create NAME --repo R --color C --description D [--force]
elif args[0] == "label" and args[1] == "create":
    log(f"label create {args[2]}")
    if args[2] not in state["labels"]:
        state["labels"].append(args[2])
        save()
# gh pr edit N --repo R --add-label X / --remove-label X
elif args[0] == "pr" and args[1] == "edit":
    n = int(args[2])
    p = pr(n)
    if "--add-label" in args:
        lab = args[args.index("--add-label") + 1]
        log(f"pr {n} add-label {lab}")
        if lab not in label_names(p):
            p["labels"].append({"name": lab})
    if "--remove-label" in args:
        lab = args[args.index("--remove-label") + 1]
        log(f"pr {n} remove-label {lab}")
        p["labels"] = [l for l in p["labels"] if l["name"] != lab]
    save()
# gh pr comment N --repo R --body B
elif args[0] == "pr" and args[1] == "comment":
    log(f"pr {args[2]} comment")
# gh repo view --json nameWithOwner -q .nameWithOwner
elif args[0] == "repo" and args[1] == "view":
    print(state["repo"])
else:
    print(f"fake-gh: unhandled: {args}", file=sys.stderr)
    sys.exit(1)
'''

PR_FIELDS = "number,title,state,mergedAt,labels,url"


def make_pr(n, state="OPEN", merged=False, labels=()):
    return {
        "number": n,
        "title": f"PR {n}",
        "state": state,
        "mergedAt": "2026-08-01T00:00:00Z" if merged else None,
        "labels": [{"name": x} for x in labels],
        "url": f"https://example.test/pr/{n}",
    }


# The fixture graph:
#   #10 CLOSED unmerged (deferred by close)      #50 MERGED
#   #20 open, requires:10                        #60 open, requires:50 (merged req)
#   #30 open, requires:20 (transitive victim)    #70 open, requires:10+50, already deferred
#   #40 open, no requirements                    #80 open, requires:30 (third tier)
FIXTURE = {
    "repo": "test/repo",
    "labels": ["requires:10", "requires:20", "requires:30", "requires:50", "deferred"],
    "prs": [
        make_pr(10, state="CLOSED", merged=False),
        make_pr(20, labels=["requires:10"]),
        make_pr(30, labels=["requires:20"]),
        make_pr(40),
        make_pr(50, state="CLOSED", merged=True),
        make_pr(60, labels=["requires:50"]),
        make_pr(70, labels=["requires:10", "requires:50", "deferred"]),
        make_pr(80, labels=["requires:30"]),
    ],
}


class Harness:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="kwf-deps-test-"))
        self.state = self.dir / "state.json"
        self.log = self.dir / "gh.log"
        shim = self.dir / "gh"
        shim.write_text(SHIM)
        shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
        self.env = dict(os.environ)
        self.env["PATH"] = f"{self.dir}:{self.env['PATH']}"
        self.env["KWF_FAKE_STATE"] = str(self.state)
        self.env["KWF_FAKE_LOG"] = str(self.log)
        self.reset()

    def reset(self):
        self.state.write_text(json.dumps(FIXTURE))
        self.log.write_text("")

    def run(self, *argv):
        p = subprocess.run([sys.executable, str(SKILL_BIN), "--repo", "test/repo", *argv],
                           capture_output=True, text=True, env=self.env)
        return p.returncode, p.stdout + p.stderr

    def gh_log(self):
        return self.log.read_text().splitlines()

    def pr_labels(self, n):
        st = json.loads(self.state.read_text())
        for p in st["prs"]:
            if p["number"] == n:
                return [l["name"] for l in p["labels"]]
        raise AssertionError(f"PR {n} missing")


FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        FAILURES.append(name)


def main():
    h = Harness()

    print("— status / check (read-only)")
    rc, out = h.run("status", "20")
    check("status shows requirement chain", rc == 0 and "requires PR #10" in out, out)
    rc, out = h.run("check", "20")
    check("check unmet exits 2", rc == 2 and "unmet" in out, out)
    rc, out = h.run("check", "60")
    check("check merged req exits 0", rc == 0, out)
    rc, out = h.run("check", "40")
    check("check no-requirements exits 0", rc == 0 and "no requirements" in out, out)
    rc, out = h.run("status", "999")
    check("missing PR errors cleanly", rc == 1 and "Could not resolve" in out, out)

    print("— requires")
    h.reset()
    rc, out = h.run("requires", "40", "50")
    check("requires on merged req is noted no-op", rc == 0 and "no-op" in out, out)
    check("requires applied the label", "requires:50" in h.pr_labels(40))
    check("requires commented", any("pr 40 comment" in l for l in h.gh_log()))
    rc, out = h.run("requires", "10", "50")
    check("requires refuses closed PR", rc == 1 and "CLOSED" in out, out)
    rc, out = h.run("requires", "40", "40")
    check("requires refuses self-requirement", rc == 1 and "itself" in out, out)

    print("— cascade (the core feature)")
    h.reset()
    rc, out = h.run("cascade", "10")
    check("cascade defers direct dependent", "deferred" in h.pr_labels(20))
    check("cascade defers transitive (tier 2)", "deferred" in h.pr_labels(30))
    check("cascade defers transitive (tier 3)", "deferred" in h.pr_labels(80))
    check("cascade spares unrelated PR", "deferred" not in h.pr_labels(40))
    check("cascade spares merged-requirement PR", "deferred" not in h.pr_labels(60))
    check("cascade skips already-deferred relabel", rc == 0 and "already deferred" in out, out)
    check("cascade comments victims", any("pr 20 comment" in l for l in h.gh_log()))
    check("cascade counts only newly deferred", "3 PR(s) deferred, 1 already deferred." in out, out)
    check("cascade does not re-comment already-deferred",
          not any("pr 70 comment" in l for l in h.gh_log()))

    print("— cascade guards")
    h.reset()
    rc, out = h.run("cascade", "40")
    check("cascade refuses non-deferred root", rc == 1 and "nothing to cascade" in out, out)
    rc, out = h.run("cascade", "40", "--force")
    check("cascade --force overrides", rc == 0 and "cascade empty" in out, out)
    rc, out = h.run("cascade", "50")
    check("cascade refuses merged root", rc == 1 and "nothing to cascade" in out, out)

    print("— dry-run")
    h.reset()
    rc, out = h.run("--dry-run", "cascade", "10")
    check("dry-run mutates nothing", "deferred" not in h.pr_labels(20))
    check("dry-run prints plan", "would label PR #20" in out, out)

    print("— lift (merge-state semantics)")
    h.reset()
    rc, out = h.run("cascade", "10")
    st = json.loads(h.state.read_text())
    for p in st["prs"]:
        if p["number"] == 10:
            p["mergedAt"] = "2026-08-02T00:00:00Z"  # pretend it merged after all
    h.state.write_text(json.dumps(st))
    rc, out = h.run("lift", "10")
    check("lift clears PR whose reqs all merged (#20)", "deferred" not in h.pr_labels(20), out)
    check("lift clears multi-req PR when ALL merged (#70)", "deferred" not in h.pr_labels(70), out)
    check("lift keeps PR whose req is open-unmerged (#30 waits on #20)",
          "deferred" in h.pr_labels(30), out)
    check("lift keeps tier 3 (#80 waits on #30)", "deferred" in h.pr_labels(80), out)
    check("lift does not touch never-deferred", "deferred" not in h.pr_labels(40))
    # Stage the next merge: #20 lands → #30 becomes liftable, #80 still waits
    st = json.loads(h.state.read_text())
    for p in st["prs"]:
        if p["number"] == 20:
            p["state"] = "CLOSED"
            p["mergedAt"] = "2026-08-02T01:00:00Z"
    h.state.write_text(json.dumps(st))
    rc, out = h.run("lift", "20")
    check("second lift clears #30 after #20 merged", "deferred" not in h.pr_labels(30), out)
    check("second lift still holds #80", "deferred" in h.pr_labels(80), out)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {', '.join(FAILURES)}")
        sys.exit(1)
    print("all green")


if __name__ == "__main__":
    main()
