# GrokTerm Multi-Machine Setup

## How It Works

GrokTerm now includes a **smart wrapper script** that automatically configures itself on each machine. This means you can sync the project via iCloud Drive and it will work seamlessly on all your Macs.

## What Happens Automatically

### First Run on a New Machine
When you run `grokterm` for the first time on a new machine:
1. ✅ Detects that virtual environment is missing
2. ✅ Creates fresh venv with correct Python interpreter
3. ✅ Installs all dependencies from `requirements.txt`
4. ✅ Runs your query

### Subsequent Runs
- ⚡ Fast startup - no setup messages
- ⚡ Uses existing venv
- ⚡ Only reinstalls if dependencies change

### When Dependencies Change
If you update `requirements.txt`:
- 🔄 Automatically detects the change
- 🔄 Reinstalls updated dependencies
- 🔄 Continues working normally

## File Sync via iCloud

### What Gets Synced ✅
- `grokterm.py` - Main script
- `requirements.txt` - Dependencies list
- `.env` - Your API configuration
- `SETUP.md`, `README.md` - Documentation

### What Doesn't Get Synced ❌
- `venv/` - Virtual environment (machine-specific)
- `.gitignore` excludes it from version control

Each Mac maintains its own `venv/` directory that's automatically created/managed.

## Troubleshooting

### Command Not Found
If `grokterm` command doesn't work, make sure `~/bin` is in your PATH:

```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="$HOME/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bash_profile
```

### Dependencies Missing
If you get import errors, the wrapper will automatically reinstall:

```bash
# Or manually trigger reinstall:
cd ~/Documents/coding/cursor/grokterm
rm -rf venv
grokterm "test"  # Will auto-setup
```

### Wrong Python Version
The wrapper uses `python3` from your system. To use a specific version:

```bash
# Edit ~/bin/grokterm and change line:
python3 -m venv "$VENV_DIR"
# To:
/usr/local/bin/python3.11 -m venv "$VENV_DIR"
```

### iCloud Sync Conflicts
If you encounter sync conflicts on `venv/`:
1. The wrapper will detect it's broken
2. Automatically recreate it
3. Continue working

Or manually clean up:
```bash
cd ~/Documents/coding/cursor/grokterm
rm -rf venv
grokterm "test"  # Recreates automatically
```

## Manual Setup (If Needed)

You shouldn't need this, but if the wrapper isn't working:

```bash
cd ~/Documents/coding/cursor/grokterm

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test
./grokterm.py "test query"
```

## Architecture

```
~/bin/grokterm                           # Smart wrapper (synced via ~/bin)
  ↓
~/Documents/coding/cursor/grokterm/      # Project folder (synced via iCloud)
  ├── grokterm.py                        # Main script (synced)
  ├── requirements.txt                   # Dependencies (synced)
  ├── .env                               # Config (synced)
  ├── venv/                              # Virtual env (NOT synced, per-machine)
  │   ├── bin/python                     # Machine-specific Python
  │   ├── lib/                           # Machine-specific packages
  │   └── .version                       # Dependencies hash for updates
  └── SETUP.md                           # This file (synced)
```

## Adding to a New Mac

1. **Sync via iCloud** - Wait for folder to sync
2. **Copy wrapper** - If `~/bin/grokterm` doesn't exist:
   ```bash
   # On the new Mac, copy from the synced folder or recreate:
   cp ~/Documents/coding/cursor/grokterm/wrapper-script.sh ~/bin/grokterm
   chmod +x ~/bin/grokterm
   ```
3. **Run it** - Just use `grokterm "test"` - it auto-configures!

## Configuration

Your `.env` file is synced across machines. If you need machine-specific settings:

```bash
# In .env, use conditional logic or create .env.local (not synced)
```

Or use environment variables in your shell:
```bash
# In ~/.zshrc
export XAI_API_KEY="your-key-here"
```

## Updates

When you update grokterm code:
1. Edit on any machine
2. iCloud syncs to all machines automatically
3. Each machine uses its own venv
4. If dependencies change, wrapper auto-updates

## Benefits

✅ **Zero manual setup** on new machines
✅ **Automatic dependency management**
✅ **Fast execution** after initial setup
✅ **Sync-safe** - no venv conflicts
✅ **Self-healing** - recreates on errors
✅ **Version tracking** - updates when needed

## Technical Details

The wrapper script (`~/bin/grokterm`) performs these checks:

1. **Directory check** - Verifies project folder exists
2. **Script check** - Verifies grokterm.py exists
3. **venv check** - Tests if venv is valid
4. **Dependency check** - Imports core packages
5. **Version check** - Compares requirements.txt hash
6. **Auto-setup** - Runs setup if any check fails
7. **Execution** - Runs grokterm.py with arguments

This ensures it works reliably across all your machines!
