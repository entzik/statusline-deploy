# Testing Guide for statusline-deploy Plugin

This guide covers testing the statusline-deploy plugin to ensure it works correctly before distribution.

## Pre-Testing Checklist

Before running tests, verify:
- [ ] Plugin directory structure is complete
- [ ] All files are readable and executable
- [ ] Python3 is available (`which python3`)
- [ ] Claude Code is installed and accessible

## Manual Testing Steps

### Test 1: Plugin Installation and Loading

**Goal:** Verify plugin loads in Claude Code

**Steps:**
1. Open Claude Code terminal
2. Navigate to plugin directory: `cd /Users/thekirschners/work/ek-claude-prompt/statusline-deploy`
3. Test with plugin directory: `cc --plugin-dir .`
4. Verify skill loads by asking: `/help` or `/statusline-deploy:install`
5. Check that skill appears in help output

**Expected result:** Plugin loads without errors, skill is discoverable

### Test 2: Skill Triggering

**Goal:** Verify skill activates on trigger phrases

**Ask Claude with trigger phrases:**
- "install statusline"
- "deploy status line"
- "run /statusline-deploy:install"
- "set up my status line"

**Expected result:** Skill activates and provides relevant guidance

### Test 3: Installation on Fresh Machine Simulation

**Goal:** Test installation process in isolated environment

**Setup:**
1. Create test directory: `mkdir -p /tmp/test-status-line`
2. Ensure no existing `~/.claude/statusline.py` or custom settings
3. Or use separate user account for clean test

**Steps:**
1. Run: `/statusline-deploy:install`
2. Observe prompts and confirmations
3. Verify files created:
   - `ls -la ~/.claude/statusline.py` (should exist, be executable)
   - `grep statusLine ~/.claude/settings.json` (should have configuration)

**Expected result:**
- Script installed successfully
- Settings merged correctly
- No errors or warnings

### Test 4: Overwrite Handling

**Goal:** Verify confirmation prompt when file exists

**Setup:**
1. Ensure `~/.claude/statusline.py` exists from Test 3
2. Note current modification time

**Steps:**
1. Run: `/statusline-deploy:install` again
2. Should prompt asking before overwrite
3. Test both "yes" (overwrite) and "no" (cancel) paths

**Expected result:**
- File ask confirmation works
- "Yes" path overwrites successfully
- "No" path cancels without changes

### Test 5: Missing Dependencies

**Goal:** Verify Python3 check

**Setup:**
1. Temporarily move or hide python3: `mv /usr/bin/python3 /usr/bin/python3.bak`
2. Or test in environment without Python3

**Steps:**
1. Run: `/statusline-deploy:install`
2. Should fail with clear error message about Python3

**Expected result:**
- Clean error message about missing Python3
- No partial installation
- Clear guidance on how to fix

**Cleanup:** `mv /usr/bin/python3.bak /usr/bin/python3`

### Test 6: Settings.json Merge

**Goal:** Verify JSON settings merge works correctly

**Setup:**
1. Create custom settings file with other config:
   ```json
   {
     "model": "sonnet",
     "theme": "dark",
     "customField": "value"
   }
   ```
2. Place at `~/.claude/settings.json`

**Steps:**
1. Run: `/statusline-deploy:install`
2. Check merged result: `cat ~/.claude/settings.json`
3. Verify: existing fields preserved, statusLine added

**Expected result:**
- All existing settings preserved
- statusLine configuration added
- Valid JSON output

### Test 7: Status Line Runtime Test

**Goal:** Verify status line executes correctly

**Steps:**
1. After installation, restart Claude Code
2. Check status area — should show status line
3. Try in different contexts:
   - Inside git repository
   - Outside git repository
   - Different directories
4. Verify both lines appear and update

**Expected result:**
- Status line appears on restart
- Both lines render without errors
- Metrics update (CPU/MEM, git state)

### Test 8: Resource Metrics

**Goal:** Verify CPU and memory display

**Steps:**
1. While status line active, monitor CPU/MEM values
2. Open application or run CPU-intensive task
3. Verify CPU/MEM values change in status line
4. Kill background task and verify values decrease

**Expected result:**
- Metrics display and update
- Values are reasonable (0-100% range)
- Color coding works (green < yellow < red)

### Test 9: Documentation

**Goal:** Verify README and guide completeness

**Checks:**
1. README.md covers all features
2. Installation instructions are clear
3. Troubleshooting section is helpful
4. All dependencies documented
5. Environment variables explained
6. Code examples are accurate

**Expected result:** Documentation is complete and accurate

## Automated Testing

### JSON Validation

```bash
python3 -m json.tool .claude-plugin/plugin.json > /dev/null && echo "Valid"
python3 -m json.tool skills/install-statusline/resources/settings-snippet.json > /dev/null && echo "Valid"
```

### Script Validation

```bash
# Check if install.sh is valid bash
bash -n scripts/install.sh

# Check if statusline.py is valid Python
python3 -m py_compile skills/install-statusline/resources/statusline.py
```

### File Permissions

```bash
# Verify script is executable
test -x scripts/install.sh && echo "Executable" || echo "Not executable"
```

## Testing on Multiple Machines (If Applicable)

For distribution, test on:
- [ ] macOS (Sonoma, Sequoia)
- [ ] Linux (Ubuntu 22.04+, Fedora)
- [ ] Different Python 3 versions (3.8, 3.9, 3.10, 3.11)
- [ ] Both light and dark themes
- [ ] Different shell environments (bash, zsh, fish)

## Known Issues and Limitations

### Expected Behaviors

1. **psutil not installed**: Script falls back to `top` command parsing (slower but works)
2. **glab not installed**: GitLab MR info won't display (other info still shows)
3. **Not in git repo**: Git section shows nothing (other info still shows)
4. **CI/container environments**: Resource metrics may be limited by system

### Tested Environments

- [x] macOS 12.6+ (Sonoma)
- [x] Python 3.8, 3.9, 3.10, 3.11+
- [ ] Linux (Ubuntu, Fedora)
- [ ] Windows with WSL2

## Test Results Template

```markdown
## Test Results - [Date]

### Environment
- OS: [macOS/Linux/Windows]
- Python: [version]
- Claude Code: [version]
- psutil: [installed/not installed]
- glab: [installed/not installed]

### Test Summary
- [ ] Test 1: Plugin Loading
- [ ] Test 2: Skill Triggering
- [ ] Test 3: Fresh Installation
- [ ] Test 4: Overwrite Handling
- [ ] Test 5: Missing Dependencies
- [ ] Test 6: Settings Merge
- [ ] Test 7: Runtime Display
- [ ] Test 8: Resource Metrics
- [ ] Test 9: Documentation

### Issues Found
[List any issues discovered]

### Notes
[Additional observations]
```

## Reporting Issues

If issues are found during testing:
1. Note exact reproduction steps
2. Include environment details (OS, Python version, etc.)
3. Capture error messages and logs
4. Include settings.json configuration used
5. Note whether issue is blocking or non-blocking
