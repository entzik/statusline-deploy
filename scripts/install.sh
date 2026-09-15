#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Plugin root (will be passed by the skill)
PLUGIN_ROOT="$1"
RESOURCES_DIR="$PLUGIN_ROOT/skills/install-statusline/resources"

# Expand home directory
CLAUDE_DIR="${HOME}/.claude"
STATUSLINE_FILE="$CLAUDE_DIR/statusline.py"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Check Python3 availability
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 is not installed or not in PATH${NC}"
    exit 1
fi

# Create ~/.claude directory if it doesn't exist
if [ ! -d "$CLAUDE_DIR" ]; then
    mkdir -p "$CLAUDE_DIR"
    echo -e "${GREEN}✓${NC} Created directory: $CLAUDE_DIR"
fi

# Check if statusline.py already exists and ask for confirmation
if [ -f "$STATUSLINE_FILE" ]; then
    echo -e "${YELLOW}⚠${NC}  File already exists: $STATUSLINE_FILE"
    # This will be handled by the skill which calls this script
    # Return special exit code to signal file exists
    exit 2
fi

# Copy statusline.py
cp "$RESOURCES_DIR/statusline.py" "$STATUSLINE_FILE"
chmod +x "$STATUSLINE_FILE"
echo -e "${GREEN}✓${NC} Installed: $STATUSLINE_FILE"

# Function to merge JSON settings
merge_settings() {
    python3 << 'PYTHON_EOF'
import json
import sys
import os

settings_file = sys.argv[1]
snippet_file = sys.argv[2]

# Read the snippet
with open(snippet_file) as f:
    snippet = json.load(f)

# Read or create existing settings
if os.path.exists(settings_file):
    with open(settings_file) as f:
        settings = json.load(f)
else:
    settings = {}

# Merge the statusLine config
settings.update(snippet)

# Write back
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print(f"✓ Applied statusLine configuration to {settings_file}")
PYTHON_EOF
}

# Merge settings.json
merge_settings "$SETTINGS_FILE" "$RESOURCES_DIR/settings-snippet.json"

exit 0
