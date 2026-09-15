#!/usr/bin/env python3
"""Claude Code status line.

Line 1: directory, repo, branch, PR/MR ----- CPU/MEM
Line 2: model/effort, context window, rate limits, session cost

Detects GitHub or GitLab repos automatically:
- GitHub: Uses `gh` CLI to fetch PR information
- GitLab: Uses `glab` CLI to fetch MR information

PR/MR lookups are cached to avoid network delays. Self-hosted GitLab hosts that
aren't named "gitlab.*" can be listed in CLAUDE_STATUSLINE_GITLAB_HOSTS (comma-separated).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"
BLUE = "\033[38;5;75m"
MAGENTA = "\033[38;5;176m"
GREEN = "\033[38;5;114m"
YELLOW = "\033[38;5;179m"
RED = "\033[38;5;174m"
GREY = "\033[38;5;245m"
ORANGE = "\033[38;5;215m"
SEP = f"{GREY} │ {RESET}"
BLOCK = f"{GREY} ----- {RESET}"

PR_TTL = 90          # seconds a cached PR/MR answer stays fresh
PR_REFRESH_LOCK = 20  # min seconds between spawned refreshes
RES_TTL = 2          # seconds a cached resource snapshot stays fresh
CACHE_DIR = os.path.join(tempfile.gettempdir(), "claude-statusline")
RES_CACHE = os.path.join(CACHE_DIR, "resources.json")


def run(*args, cwd=None, timeout=1.5):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def git(cwd, *args):
    return run("git", "-C", cwd, *args)


def pct_color(pct):
    return GREEN if pct < 50 else YELLOW if pct < 80 else RED


def human(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def short_path(path, home):
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        path = "~" + path[len(home):]
    parts = path.split(os.sep)
    if len(parts) > 3:
        parts = ["…"] + parts[-2:]
    return os.sep.join(parts)


def time_until_short(ts):
    """Format time remaining for 5-hour window.
    Shows: Xh Ym if hours > 0, or just Xm if hours = 0.
    """
    secs = int(ts - time.time())
    if secs <= 0:
        return "now"

    hours = secs // 3600
    mins = (secs % 3600) // 60

    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"


def time_until_long(ts):
    """Format time remaining for 7-day window.
    Shows: Xh if days = 0, or Xd Yh if days > 0 (with special case for tomorrow).
    """
    secs = int(ts - time.time())
    if secs <= 0:
        return "now"

    days = secs // 86400
    hours = (secs % 86400) // 3600

    if days == 0:
        return f"{hours}h"
    elif days == 1:
        return f"tomorrow {hours}h" if hours > 0 else "tomorrow"
    else:
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"


def bar(pct, width=8):
    filled = int(round(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


def fetch_resources():
    """Fetch CPU and memory stats from system.
    Returns (cpu_pct, mem_pct, mem_used_mb, mem_total_mb) or (None, None, None, None).
    Uses sysctl for true total RAM to avoid top's accounting differences.
    """
    try:
        import psutil
        cpu_pct = int(psutil.cpu_percent(interval=0))
        vm = psutil.virtual_memory()
        mem_used_mb = int(vm.used / 1024 / 1024)
        mem_total_mb = int(vm.total / 1024 / 1024)
        return (cpu_pct, int(vm.percent), mem_used_mb, mem_total_mb)
    except (ImportError, Exception):
        pass

    out = run("top", "-l", "1", "-n", "0", timeout=2)
    if not out:
        return None, None, None, None

    # Get true physical RAM from sysctl (more reliable than top's total)
    total_bytes_str = run("sysctl", "-n", "hw.memsize")
    total_mb = None
    if total_bytes_str:
        try:
            total_mb = int(total_bytes_str) // (1024 * 1024)
        except Exception:
            pass

    cpu, mem_pct, mem_used_mb = None, None, None
    for line in out.splitlines():
        if "CPU usage:" in line:
            m = re.search(r"(\d+\.\d+)%\s+user", line)
            if m:
                cpu = int(float(m.group(1)))
        elif "PhysMem:" in line:
            m = re.search(r"(\d+)([MG])\s+used", line)
            if m:
                used_val, used_unit = int(m.group(1)), m.group(2)
                mem_used_mb = used_val * (1024 if used_unit == "G" else 1)

    if mem_used_mb is not None and total_mb is not None:
        mem_pct = int(round(mem_used_mb / total_mb * 100))
        return cpu, mem_pct, mem_used_mb, total_mb
    return cpu, None, None, None


def system_resources():
    """Return (cpu_pct, mem_pct, mem_used_mb, mem_total_mb) with caching."""
    cached, age = None, None
    try:
        with open(RES_CACHE) as f:
            blob = json.load(f)
        cached, age = blob.get("res"), time.time() - blob.get("ts", 0)
    except Exception:
        pass

    if cached and age and age <= RES_TTL:
        return cached
    res = fetch_resources()
    if res != (None, None, None, None):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            json.dump({"ts": time.time(), "res": res}, open(RES_CACHE, "w"))
        except Exception:
            pass
    return res



def git_state(cwd):
    """Branch, dirty flag and ahead/behind in a single git invocation."""
    out = git(cwd, "status", "--porcelain=v2", "--branch", "--untracked-files=no")
    if out is None:
        return None, False, 0, 0
    branch, dirty, ahead, behind = None, False, 0, 0
    for line in out.splitlines():
        if line.startswith("# branch.head "):
            branch = line[14:].strip()
        elif line.startswith("# branch.oid ") and branch is None:
            pass
        elif line.startswith("# branch.ab "):
            try:
                a, b = line[12:].split()
                ahead, behind = int(a), -int(b)
            except Exception:
                pass
        elif not line.startswith("#"):
            dirty = True
    if branch == "(detached)":
        branch = "@" + (git(cwd, "rev-parse", "--short", "HEAD") or "detached")
    return branch, dirty, ahead, behind


# --- GitHub/GitLab PR/MR detection and caching -----

def repo_host(repo, cwd):
    """Extract hostname from repo config."""
    host = (repo or {}).get("host") or ""
    if not host:
        url = git(cwd, "config", "--get", "remote.origin.url") or ""
        m = re.match(r"(?:git@|ssh://(?:git@)?|https?://(?:[^@/]*@)?)([^:/]+)", url)
        host = m.group(1) if m else ""
    return host.lower() if host else None


def github_host(repo, cwd):
    """Return host if repo is on GitHub."""
    host = repo_host(repo, cwd)
    return host if host and "github.com" in host else None


def gitlab_host(repo, cwd):
    """Return host if repo is on GitLab."""
    host = repo_host(repo, cwd)
    if not host:
        return None
    extra = [h.strip().lower() for h in
             os.environ.get("CLAUDE_STATUSLINE_GITLAB_HOSTS", "").split(",") if h.strip()]
    return host if ("gitlab" in host or host in extra) else None


def pr_cache_path(root, branch, prefix="pr"):
    key = hashlib.sha1(f"{root}\0{branch}".encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{prefix}-{key}.json")


def fetch_pr(cwd, cache_path, tool):
    """Detached child: fetch PR/MR info with glab or gh, write the cache."""
    pr = None
    if tool == "glab":
        out = run("glab", "mr", "view", "-F", "json", cwd=cwd, timeout=15)
        if out:
            try:
                d = json.loads(out)
                pr = {
                    "number": d.get("iid"),
                    "state": d.get("state"),
                    "draft": bool(d.get("draft") or d.get("work_in_progress")),
                    "check": ((d.get("head_pipeline") or d.get("pipeline") or {}) or {}).get("status"),
                }
                if not pr["number"]:
                    pr = None
            except Exception:
                pass
    elif tool == "gh":
        out = run("gh", "pr", "view", "--json", "number,state,isDraft,statusCheckRollup", cwd=cwd, timeout=15)
        if out:
            try:
                d = json.loads(out)
                checks = d.get("statusCheckRollup", [])
                check_state = None
                if checks:
                    states = [c.get("status") for c in checks if c.get("status")]
                    if "FAILURE" in states:
                        check_state = "failed"
                    elif "PENDING" in states:
                        check_state = "pending"
                    elif all(s == "SUCCESS" for s in states):
                        check_state = "success"
                pr = {
                    "number": d.get("number"),
                    "state": d.get("state", "").lower(),
                    "draft": d.get("isDraft", False),
                    "check": check_state,
                }
                if not pr["number"]:
                    pr = None
            except Exception:
                pass

    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp = cache_path + f".{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump({"ts": time.time(), "pr": pr}, f)
    os.replace(tmp, cache_path)


def pr_segment(repo, cwd, branch):
    """Display GitHub PR or GitLab MR info, auto-detecting repo type."""
    if not branch or branch.startswith("@"):
        return None

    is_github = bool(github_host(repo, cwd))
    is_gitlab = bool(gitlab_host(repo, cwd))

    if not is_github and not is_gitlab:
        return None

    root = git(cwd, "rev-parse", "--show-toplevel") or cwd
    tool = "gh" if is_github else "glab"
    cache_path = pr_cache_path(root, branch, prefix=("gh" if is_github else "mr"))

    cached, age = None, None
    try:
        with open(cache_path) as f:
            blob = json.load(f)
        cached, age = blob.get("pr"), time.time() - blob.get("ts", 0)
    except Exception:
        pass

    if age is None or age > PR_TTL:
        lock = cache_path + ".lock"
        try:
            fresh_lock = os.path.exists(lock) and time.time() - os.path.getmtime(lock) < PR_REFRESH_LOCK
            tool_available = run("which", tool)
            if not fresh_lock and tool_available:
                os.makedirs(CACHE_DIR, exist_ok=True)
                open(lock, "w").close()
                subprocess.Popen(
                    [sys.executable, os.path.abspath(__file__), "--refresh-pr", cwd, cache_path, tool],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL, start_new_session=True,
                )
        except Exception:
            pass

    if not cached:
        return None

    state = cached.get("state") or ""
    number = cached.get("number")
    if not number:
        return None

    label = f"#{number}" if is_github else f"!{number}"
    color = GREEN if state == "merged" else RED if state == "closed" else ORANGE
    bits = []
    if cached.get("draft"):
        bits.append("draft")
    if state and state != "open":
        bits.append(state)
    check = cached.get("check")
    if check in ("failed", "pending", "success"):
        bits.append(check)
    suffix = f" {DIM}{' · '.join(bits)}{RESET}" if bits else ""
    stale = f"{DIM}~{RESET}" if age and age > PR_TTL * 4 else ""
    return f"{color}{label}{RESET}{suffix}{stale}"


# --- segments ---------------------------------------------------------------

def model_segment(data):
    """Return model, effort, and mode info."""
    model = (data.get("model") or {}).get("display_name") or "?"
    bits = []
    effort = (data.get("effort") or {}).get("level")
    if effort:
        bits.append(effort)
    if data.get("fast_mode"):
        bits.append("fast")
    if (data.get("thinking") or {}).get("enabled"):
        bits.append("think")
    label = model + (f" {DIM}[{' · '.join(bits)}]{RESET}" if bits else "")
    return f"{GREEN}◆ {label}{RESET}"


def line_one(data):
    segs = []

    segs.append(model_segment(data))

    ctx = data.get("context_window") or {}
    used, size = ctx.get("total_input_tokens") or 0, ctx.get("context_window_size") or 0
    pct = ctx.get("used_percentage")
    if pct is None:
        pct = int(round(used / size * 100)) if size else 0
    detail = f" {DIM}{human(used)}/{human(size)}{RESET}" if size else ""
    long_ctx = f" {DIM}>200k{RESET}" if data.get("exceeds_200k_tokens") else ""
    segs.append(f"{pct_color(pct)}{bar(pct)} {pct}%{RESET}{detail}{long_ctx}")

    limits = data.get("rate_limits") or {}
    parts = []
    for key, name in (("five_hour", "5h"), ("seven_day", "7d")):
        b = limits.get(key)
        if not b:
            continue
        p = int(round(b.get("used_percentage") or 0))
        reset = b.get("resets_at")
        time_fmt = time_until_short(reset) if key == "five_hour" else time_until_long(reset)
        hint = f" {DIM}↻{time_fmt}{RESET}" if reset else ""
        parts.append(f"{DIM}{name}{RESET} {pct_color(p)}{p}%{RESET}{hint}")
    if parts:
        segs.append(f"{GREY}⏳{RESET} " + f" {DIM}·{RESET} ".join(parts))

    cost = (data.get("cost") or {}).get("total_cost_usd")
    if cost is not None:
        segs.append(f"{GREY}${cost:.2f}{RESET}")

    return SEP.join(segs)


def line_two(data, home):
    workspace = data.get("workspace") or {}
    cwd = workspace.get("current_dir") or data.get("cwd") or os.getcwd()
    segs = [f"{BLUE}{BOLD}{short_path(cwd, home)}{RESET}"]

    repo = workspace.get("repo")
    if repo and repo.get("owner") and repo.get("name"):
        host = repo.get("host") or "git"
        segs.append(f"{GREY}{host}/{repo['owner']}/{repo['name']}{RESET}")

    branch, dirty, ahead, behind = git_state(cwd)
    if branch:
        mark = f"{YELLOW}*{RESET}" if dirty else ""
        track = ""
        if ahead or behind:
            track = (f" {DIM}" + (f"↑{ahead}" if ahead else "") +
                     (f"↓{behind}" if behind else "") + RESET)
        segs.append(f"{MAGENTA}⎇ {branch}{RESET}{mark}{track}")

    pr = pr_segment(repo, cwd, branch)
    if pr:
        segs.append(pr)

    # Second half: resources only
    res = resources_segment()
    if res:
        return SEP.join(segs) + BLOCK + res
    return SEP.join(segs)


def format_mb(mb):
    """Format MB as human-readable (GB or MB)."""
    if mb >= 1024:
        return f"{mb / 1024:.1f}G"
    return f"{mb}M"


def resources_segment():
    """Return CPU and memory usage segment."""
    cpu, mem_pct, mem_used_mb, mem_total_mb = system_resources()
    if cpu is None and mem_pct is None:
        return None
    parts = []
    if cpu is not None:
        parts.append(f"{pct_color(cpu)}{cpu}% CPU{RESET}")
    if mem_pct is not None and mem_used_mb is not None and mem_total_mb is not None:
        mem_detail = f"({format_mb(mem_used_mb)}/{format_mb(mem_total_mb)})"
        parts.append(f"{pct_color(mem_pct)}{mem_pct}% MEM{RESET} {DIM}{mem_detail}{RESET}")
    return " ".join(parts) if parts else None


def main():
    if len(sys.argv) > 3 and sys.argv[1] == "--refresh-pr":
        tool = sys.argv[4] if len(sys.argv) > 4 else "glab"
        fetch_pr(sys.argv[2], sys.argv[3], tool)
        return
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    home = os.path.expanduser("~")
    sys.stdout.write(line_two(data, home) + "\n" + line_one(data))


if __name__ == "__main__":
    main()
