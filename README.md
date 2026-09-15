# statusline-deploy

Install and deploy a custom Claude Code status line configuration to your machine.

## What it does

This plugin installs a sophisticated Claude Code status line that displays:

**Line 1** (Model & Usage):
- Active model and effort level
- Context window utilization
- Rate limits (5-hour and 7-day windows)
- Session cost

**Line 2** (Repository & Resources):
- Current directory
- Git repository info (owner/name)
- Git branch, dirty status, ahead/behind tracking
- GitLab MR status (if using GitLab)
- CPU and memory usage

## Installation

Run the install command:

```
/statusline-deploy:install
```

This will:
1. Check that Python3 is available
2. Create `~/.claude/` directory if needed
3. Copy `statusline.py` to `~/.claude/`
4. Apply the status line configuration to `~/.claude/settings.json`

## Features

### Git Integration
- Shows current branch with visual indicator (`⎇`)
- Displays dirty status (`*` when changes exist)
- Shows ahead/behind tracking with branch
- Works with detached HEAD states
- Branch name is a clickable link to its GitHub/GitLab branch page (terminals supporting OSC 8 hyperlinks)

### GitHub PR & GitLab MR Status
- **Auto-detection:** Automatically detects GitHub or GitLab repositories
- **GitHub:** Displays PR number (e.g., `#123`) with status, clickable to open the PR (terminals supporting OSC 8 hyperlinks)
- **GitLab:** Displays MR number (e.g., `!456`) with status, clickable to open the MR (terminals supporting OSC 8 hyperlinks)
- Shows draft status, approval state, and check counts (e.g. `3/4 checks pending`)
  - GitHub: review decision (approved/changes requested/review required) from `gh pr view`
  - GitLab: approval state (approved/review required) from `glab api .../approvals`, and per-job pipeline counts from `glab api .../pipelines/:id/jobs`
- Caches results to minimize API calls
- Supports self-hosted GitLab via `CLAUDE_STATUSLINE_GITLAB_HOSTS` env var

### Resource Monitoring
- CPU usage percentage with color coding
- Memory usage (requires `psutil` for accuracy)
- Color indicators: green (<50%), yellow (<80%), red (≥80%)

### Performance Optimized
- Caches resource snapshots (2-second TTL)
- Caches GitLab MR results (90-second TTL)
- Minimal polling and network overhead

## Optional Dependencies

### `psutil` (recommended)
Improves CPU/memory accuracy and speed. Install with:
```bash
pip3 install psutil
```

Without psutil, the script falls back to parsing `top` output, which is slower and less accurate on macOS.

### `glab` (optional)
Required only if using GitLab and want to see MR status. Install from:
https://gitlab.com/gitlab-org/cli/-/releases

### `gh` (optional)
Required only if using GitHub and want to see PR status. Install from:
https://github.com/cli/cli#installation

## Environment Variables

### `CLAUDE_STATUSLINE_GITLAB_HOSTS`
Comma-separated list of custom GitLab hosts to recognize (if not standard gitlab.* domain):

```bash
export CLAUDE_STATUSLINE_GITLAB_HOSTS="git.company.com,gitlab.internal"
```

## Color Scheme

The status line uses ANSI 256-color palette for better terminal compatibility:
- **Blue**: Directory path
- **Magenta**: Git branch
- **Green**: Model indicator, low resource usage (<50%)
- **Yellow**: Medium resource usage (<80%)
- **Red**: High resource usage (≥80%)
- **Orange**: GitLab MR status
- **Grey**: Separators and secondary info

## Troubleshooting

**Status line not appearing:**
1. Restart Claude Code after installation
2. Check that `~/.claude/statusline.py` exists and is executable
3. Verify settings.json contains the statusLine configuration
4. Test manually: `python3 ~/.claude/statusline.py < /dev/null`

**Missing resource metrics:**
- Ensure Python3 is available
- Install `psutil` for better accuracy: `pip3 install psutil`
- Check system resource availability (some CI systems limit this)

**GitHub PR not showing:**
- Verify `gh` is installed and configured: `gh auth status`
- Check repository has `remote.origin.url` pointing to GitHub
- Ensure current branch has an associated pull request
- Check network connectivity to GitHub

**GitLab MR not showing:**
- Verify `glab` is installed and configured: `glab auth status`
- Check repository has `remote.origin.url` configured
- For self-hosted GitLab, set `CLAUDE_STATUSLINE_GITLAB_HOSTS` env var
- Check network connectivity to GitLab instance

## Version History

### 0.1.0 (Initial Release)
- Initial plugin with status line installation
