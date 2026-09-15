---
name: Install Status Line
description: This skill should be used when the user asks to "install statusline", "run statusline-deploy:install", "deploy status line", "set up my status line", or "install the status line on this machine". Provides guidance for installing a custom Claude Code status line configuration.
version: 0.1.0
---

# Install Status Line Skill

This skill handles the installation and configuration of a custom Claude Code status line on the local machine.

## What Gets Installed

The installation adds a sophisticated two-line status display to Claude Code that shows:

**Line 1** — Model, Context, Rate Limits, Cost
- Active model name and effort level
- Context window usage with progress bar
- Rate limits (5-hour and 7-day windows) with reset times
- Session cost in USD

**Line 2** — Repository, Branch, and Resources
- Current working directory (shortened for readability)
- Git repository (owner/name)
- Git branch with dirty status and tracking info
- GitLab MR number and pipeline status (when available)
- System resources: CPU and memory usage

## Installation Process

Run the install command:

```
/statusline-deploy:install
```

The installation script will:

1. **Validate Python3 availability** — Fails if Python3 is not installed (required to run the status line)
2. **Create ~/.claude/ directory** — Creates directory structure if missing
3. **Copy statusline.py** — Places the status line script at `~/.claude/statusline.py` and makes it executable
4. **Confirm overwrite** — Asks before replacing an existing statusline.py file
5. **Merge settings.json** — Adds the statusLine configuration to `~/.claude/settings.json`, or creates a minimal settings file if one doesn't exist
6. **Report success** — Shows file paths and basic confirmation

After installation completes, restart Claude Code to activate the status line display.

## How It Works

The status line runs as a subprocess hook in Claude Code, executed via the `statusLine.command` setting in settings.json:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"$HOME/.claude/statusline.py\"",
    "padding": 0
  }
}
```

The Python script reads JSON data from Claude Code's context (model, workspace, rate limits) via stdin, processes it with Git operations and system calls, and outputs two formatted lines to stdout.

## Dependencies

### Required
- **Python3** — The status line script requires Python 3.x. Installation fails if Python3 is not available.

### Optional (Recommended)
- **psutil** — Python package for accurate CPU/memory metrics. Without it, the script falls back to parsing `top` output (slower and less accurate on macOS). Install with:
  ```bash
  pip3 install psutil
  ```

### Optional (Feature-Specific)
- **glab** — GitLab CLI tool to display MR status. Only needed if using GitLab and want to see merge request info in the status line. Install from: https://gitlab.com/gitlab-org/cli/-/releases
- **gh** — GitHub CLI tool to display PR status. Only needed if using GitHub and want to see pull request info in the status line. Install from: https://github.com/cli/cli#installation

## Configuration

### Environment Variables

**CLAUDE_STATUSLINE_GITLAB_HOSTS** — Define custom GitLab hosts if using self-hosted GitLab not on a standard gitlab.* domain:

```bash
export CLAUDE_STATUSLINE_GITLAB_HOSTS="git.company.com,gitlab.internal"
```

Multiple hosts can be specified as comma-separated values. This is useful for organizations running GitLab on internal domains.

### Manual Adjustments

After installation, the status line configuration lives in `~/.claude/settings.json` under the `statusLine` key. To customize:

- Adjust `padding` value (default 0) to add spacing
- Modify the command if the Python script location changes
- The script respects Claude Code's theme settings (light/dark mode)

## Features in Detail

### Git Integration
- Displays current branch name with visual indicator (`⎇`)
- Shows dirty status with asterisk (`*`) when uncommitted changes exist
- Displays ahead/behind counts relative to tracking branch (↑/↓)
- Handles detached HEAD states by showing short commit hash

### GitHub PR & GitLab MR Status
- **Auto-detection:** Automatically detects GitHub or GitLab repositories
- **GitHub:** Shows PR number (e.g., `#123`) when on a branch with an active PR
- **GitLab:** Shows MR number (e.g., `!456`) when on a branch with an active MR
- Displays PR/MR state (open, merged, closed) with color coding
- Indicates draft status and check/pipeline state (running, failed, pending)
- Uses intelligent caching (90-second TTL) to minimize network calls
- Spawns detached refresh process when cache expires, never blocking renders

### Resource Monitoring
- **CPU** — Shows percentage with real-time measurement
- **Memory** — Shows usage percentage and absolute values (e.g., `2.4G/16G`)
- **Color coding** — Green (<50%), Yellow (50-80%), Red (≥80%)
- **Performance** — Uses 2-second cache to avoid continuous polling

### Performance Optimizations
- Caches resource metrics for 2 seconds to minimize system load
- Caches GitHub PR and GitLab MR results for 90 seconds with automatic refresh
- Limits PR/MR refresh spawning to one per 20 seconds to avoid thundering herd
- Uses subprocess with timeouts for all external commands (git, gh, glab, top)
- Falls back gracefully when tools are unavailable

## After Installation

### Verify Installation

1. Restart Claude Code to load the new settings
2. Open Claude Code's status area — the custom status line should appear
3. Verify both lines display without errors
4. Check that resource metrics update (CPU/MEM values change)

### Quick Troubleshooting

**Status line not appearing:**
- Verify script exists: `ls -la ~/.claude/statusline.py`
- Test manually: `echo '{}' | python3 ~/.claude/statusline.py`
- See references/TROUBLESHOOTING.md for detailed solutions

**Missing metrics or features:**
- CPU/MEM blank: Install psutil (`pip3 install psutil`)
- PR/MR not showing: Ensure `gh` (GitHub) or `glab` (GitLab) is installed
- See references/TROUBLESHOOTING.md for detailed solutions

### Customizing

To customize the status line, edit `~/.claude/statusline.py` directly. Key customization points:
- **Colors:** Modify ANSI color constants (BLUE, RED, etc.) near the top
- **Format:** Adjust formatting in `line_one()` and `line_two()` functions
- **Thresholds:** Change resource usage thresholds in `pct_color()` function

## What Changed on Your Machine

**Files created:**
- `~/.claude/statusline.py` — The status line script (415 lines)
- `~/.claude/settings.json` — Claude Code configuration (created if missing, otherwise merged)

**Configuration added to settings.json:**
```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"$HOME/.claude/statusline.py\"",
    "padding": 0
  }
}
```

## Next Steps

1. **Test the status line** — Restart Claude Code and verify both lines display
2. **Install optional dependencies** — Run `pip3 install psutil` for better performance
3. **Share with team** — This plugin can be distributed to share the same status line setup on other machines
4. **Customize if desired** — Edit `~/.claude/statusline.py` for color or format changes

## Uninstallation

To remove the status line:

1. Delete the script: `rm ~/.claude/statusline.py`
2. Remove from settings: Edit `~/.claude/settings.json` and delete the `statusLine` key
3. Restart Claude Code

The installation is clean and non-invasive — removing these two changes completely uninstalls the status line.

## Supporting Files and References

The following files are included in this skill:

**Implementation Files:**
- **resources/statusline.py** — The complete Python implementation (~415 lines, with detailed comments)
- **resources/settings-snippet.json** — Example configuration structure that gets merged into settings.json
- **scripts/install.sh** — Installation helper script handling file copy and JSON merge operations

**Documentation Files:**
- **references/TROUBLESHOOTING.md** — Detailed troubleshooting guide for common issues and solutions
