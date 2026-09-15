# Troubleshooting the Status Line

## Common Issues and Solutions

### Status Line Not Appearing After Restart

**Symptoms:** Restarted Claude Code but no status line appears in the status area.

**Troubleshooting steps:**

1. Verify the script exists and is executable:
   ```bash
   ls -la ~/.claude/statusline.py
   ```
   Should show: `-rwxr-xr-x` permissions

2. Verify settings.json contains the configuration:
   ```bash
   grep statusLine ~/.claude/settings.json
   ```
   Should output the statusLine configuration block

3. Test the script manually:
   ```bash
   echo '{}' | python3 ~/.claude/statusline.py
   ```
   Should output two lines of text without errors

4. Check Claude Code logs for errors (if available in your setup)

**If still not appearing:**
- Try restarting Claude Code completely (not just the window)
- Check that `~/.claude/settings.json` is valid JSON: `python3 -m json.tool ~/.claude/settings.json`
- Ensure the statusline command path is correct in settings.json

### Missing Resource Metrics (CPU/MEM Showing Blank)

**Symptoms:** Status line appears but CPU and MEM values are missing or show as "--"

**Causes and solutions:**

**Python3 version issue:**
- Verify Python3 is available: `which python3`
- Check version: `python3 --version` (should be 3.6+)
- If missing, install Python3 for your OS

**psutil not installed (most common):**
- The script falls back to parsing `top` output without psutil
- Install for better accuracy: `pip3 install psutil`
- Verify installation: `python3 -c "import psutil; print(psutil.__version__)"`

**System limitations:**
- Some CI/container environments restrict access to system resource APIs
- Check if running in restricted environment (Docker, CI system, etc.)
- Ask system administrator if resource monitoring is allowed

**macOS specific:**
- Older versions of macOS may have permission issues
- Try: `system_profiler SPHardwareDataType | grep Memory`
- If that fails, upgrade macOS or install psutil

**Test resource monitoring:**
```bash
python3 ~/.claude/statusline.py < /dev/null
```
If CPU/MEM are missing, psutil is likely not installed.

### GitHub PR Not Showing

**Symptoms:** Status line appears but GitHub PR information (e.g., "#123") is not displayed.

**Causes and solutions:**

**Repository not configured for GitHub:**
- Verify remote URL is GitHub: `git config remote.origin.url`
- Should contain "github.com" in the hostname
- PR status only shows when current branch has an associated PR

**gh tool not installed:**
- Check if gh is available: `which gh`
- Install from: https://github.com/cli/cli#installation
- After installing: `gh auth status`

**Not on a branch with a pull request:**
- PR status only shows when the current branch has an associated PR
- Create a pull request and push to that branch
- Or check a branch that already has a PR

**Network/authentication issues:**
- Verify network connectivity to GitHub: `ping github.com`
- Check gh authentication: `gh auth status`
- If not authenticated: `gh auth login`

**Test GitHub integration:**
```bash
gh pr view
```
If this fails, GitHub PR integration won't work in the status line.

### GitLab MR Not Showing

**Symptoms:** Status line appears but GitLab MR information (e.g., "!456") is not displayed.

**Causes and solutions:**

**Repository not configured for GitLab:**
- Verify remote URL is GitLab: `git config remote.origin.url`
- Should contain "gitlab" in the hostname
- If using self-hosted GitLab on custom domain, set environment variable:
  ```bash
  export CLAUDE_STATUSLINE_GITLAB_HOSTS="git.company.com,gitlab.internal"
  ```

**glab tool not installed:**
- Check if glab is available: `which glab`
- Install from: https://gitlab.com/gitlab-org/cli/-/releases
- After installing: `glab auth status` (if using self-hosted: `glab auth login --host git.company.com`)

**Not on a branch with a merge request:**
- MR status only shows when the current branch has an associated MR
- Create a merge request and push to that branch
- Or check a branch that already has an MR

**Network/authentication issues:**
- Verify network connectivity to GitLab: `ping gitlab.com` (or your GitLab host)
- Check glab authentication: `glab auth status`
- If using self-hosted GitLab: `glab auth login --host git.company.com`

**Test GitLab integration:**
```bash
glab mr view -F json
```
If this fails, GitLab integration won't work in the status line.

### Settings File Corruption

**Symptoms:** Status line installation fails or settings.json becomes invalid JSON.

**Prevention and recovery:**

**Prevent corruption:**
- Always backup settings.json before manual edits: `cp ~/.claude/settings.json ~/.claude/settings.json.backup`
- Use proper JSON editors (VS Code, etc.) not plain text editors

**Recover from corruption:**
1. Check if backup exists: `ls ~/.claude/settings.json.backup`
2. Restore from backup: `cp ~/.claude/settings.json.backup ~/.claude/settings.json`
3. Reinstall status line: `/statusline-deploy:install`

**Validate JSON:**
```bash
python3 -m json.tool ~/.claude/settings.json > /dev/null && echo "Valid" || echo "Invalid"
```

**Minimal recovery (start from scratch):**
```bash
# Remove corrupted file
rm ~/.claude/settings.json

# Reinstall - will create minimal settings.json
/statusline-deploy:install
```

### Performance Issues (Status Line Slow to Update)

**Symptoms:** Status line updates slowly or causes noticeable delays.

**Causes and solutions:**

**Network delays from GitLab MR lookup:**
- Normal: GitLab MR info is cached (90-second TTL), network calls happen in background
- If persistent: Check GitLab network connectivity
- Workaround: Set `export CLAUDE_STATUSLINE_GITLAB_HOSTS=""` to disable MR lookup

**Slow resource monitoring:**
- Without psutil: `top` command parsing can be slow
- Solution: Install psutil: `pip3 install psutil`
- This reduces resource check from ~100ms to ~10ms

**System under high load:**
- On heavily loaded systems, subprocess calls may be slower
- Normal behavior — wait for system to settle

**Test performance:**
```bash
time echo '{}' | python3 ~/.claude/statusline.py
```
Should complete in <200ms typically.

### Installation Fails on Permission Denied

**Symptoms:** Installation script fails with "Permission denied" error.

**Causes and solutions:**

**Directory not writable:**
- Verify ~/.claude/ is writable: `touch ~/.claude/test.txt && rm ~/.claude/test.txt`
- Fix permissions: `chmod 755 ~/.claude/`

**Home directory path issue:**
- Verify $HOME is set: `echo $HOME`
- Should be your home directory path (not /root in containers, etc.)

**Read-only filesystem:**
- Check if filesystem is read-only: `touch /tmp/test.txt`
- On containers/VMs, verify appropriate mount permissions
- Ask system administrator if ~/.claude/ can be made writable

### Python3 Not Found Error

**Symptoms:** Installation fails with "Error: Python3 is not installed or not in PATH"

**Solutions:**

**macOS:**
- Install via Homebrew: `brew install python3`
- Or download from https://www.python.org

**Linux (Ubuntu/Debian):**
- Install: `sudo apt-get install python3`

**Linux (Fedora/RHEL):**
- Install: `sudo dnf install python3`

**Windows (WSL2):**
- Inside WSL, run Ubuntu/Debian commands above

**Verify installation:**
```bash
python3 --version
which python3
python3 -c "print('Python works')"
```

All three commands should succeed.

### Status Line Shows Old Information

**Symptoms:** Status line displays outdated git branch or rate limit info.

**Causes and solutions:**

**Git state cache is stale:**
- Git status is fetched fresh each time (not cached)
- If showing old branch: working directory may not have updated
- Try: `git status` to refresh git state

**Rate limits cached for session:**
- Rate limit data comes from Claude Code's session info
- Updates when session state changes
- Not a status line issue — this is expected behavior

**MR info is stale:**
- MR info is cached for 90 seconds to minimize API calls
- Force refresh by restarting Claude Code
- Or wait 90 seconds for automatic refresh

**Resource metrics cached:**
- Resource metrics (CPU/MEM) cached for 2 seconds
- Normal optimization to avoid constant polling
- Wait 2 seconds or restart Claude Code to force immediate update

## Getting Help

If issues persist after troubleshooting:

1. Gather information:
   - OS and version: `uname -a` (or `system_profiler -SPSoftwareDataType` on macOS)
   - Python version: `python3 --version`
   - Claude Code version
   - Error messages from installation

2. Check logs:
   - Claude Code logs (location varies by OS)
   - Manual test output: `echo '{}' | python3 ~/.claude/statusline.py 2>&1`

3. Report with:
   - Exact reproduction steps
   - Environment details from above
   - Error messages (full text, not paraphrased)
   - What you've already tried
