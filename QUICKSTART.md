# GrokTerm Quick Start

## First Time on This Machine?

Just run:
```bash
grokterm "What is today's date?"
```

It will automatically:
- Create virtual environment
- Install dependencies
- Run your query

Takes ~10-30 seconds on first run, instant afterwards.

## Commands

```bash
# Single query
grokterm "your question here"

# Interactive mode
grokterm

# All tools enabled by default
grokterm "What's the weather?" # Uses web search
grokterm "What's trending on X?" # Uses X search  
grokterm "Calculate sqrt(2) to 100 digits" # Uses code interpreter
```

## Interactive Commands

```
/tools         - Show tools status
/tools on/off  - Toggle all tools
/models        - Switch models
/clear         - Clear conversation
/help          - Show help
/exit          - Exit
```

## Troubleshooting

### "command not found: grokterm"
Add to your PATH:
```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Import errors
Automatic fix:
```bash
cd ~/Documents/coding/cursor/grokterm
rm -rf venv
grokterm "test"  # Auto-rebuilds
```

### Multiple machines (iCloud)
Just run `grokterm` - it auto-configures per machine!

## Features

✅ Date awareness (knows current date)
✅ Web search (real-time internet)
✅ X search (Twitter/X posts)  
✅ Code interpreter (Python execution)
✅ Conversation history
✅ Model switching

## Configuration

Edit `~/Documents/coding/cursor/grokterm/.env`:
```bash
XAI_API_KEY=your-key-here
XAI_MODEL=grok-4-1-fast-reasoning
XAI_ENABLE_WEB_SEARCH=true
XAI_ENABLE_X_SEARCH=true
XAI_ENABLE_CODE_INTERPRETER=true
```

That's it! 🚀
