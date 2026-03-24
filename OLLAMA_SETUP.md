"""
Ollama Setup Guide — Local AI Fallback
=====================================

Why Ollama?
-----------
• CPU-based (works without GPU)
• ~2GB download (phi model)
• Works completely offline
• Free & open-source
• Instant AI generation when APIs fail
• No API costs or rate limits


Quick Setup (Windows)
---------------------

1. Download Ollama
   Visit: https://ollama.ai
   Click "Download for Windows"

2. Install
   Run the installer, click "Install"

3. Download Model (one-time, ~5 min)
   Open PowerShell and run:
   
   ollama pull mistral
   
   (or try: phi for faster, neural-chat for balanced)

4. Start Ollama Service
   Run in background:
   
   ollama serve
   
   It will listen on http://localhost:11434

5. Test in Your App
   Go to option 9 in the menu to test


Model Recommendations
---------------------

For Your Use Case (Cold Outreach Emails):

┌─────────────────┬──────────┬────────┬──────────────┐
│ Model          │ Size     │ Speed  │ Quality      │
├─────────────────┼──────────┼────────┼──────────────┤
│ phi            │ 2.7GB    │ Very   │ Good          │
│                │          │ Fast   │               │
├─────────────────┼──────────┼────────┼──────────────┤
│ neural-chat    │ 4GB      │ Medium │ Very Good     │
│                │          │        │               │
├─────────────────┼──────────┼────────┼──────────────┤
│ mistral        │ 4GB      │ Medium │ Excellent     │ ← Recommended
│                │          │        │               │
└─────────────────┴──────────┴────────┴──────────────┘


Commands
--------

# Download a model (one-time)
ollama pull mistral

# Start Ollama service
ollama serve

# List installed models
ollama list

# Remove a model to free space
ollama rm mistral

# Run Ollama with GPU (if available)
set OLLAMA_NUM_GPU=1
ollama serve


How It Works in Your App
------------------------

When you generate emails or pitches:

1. Try OpenRouter (fast, cloud, expensive)
2. If fails → Try Gemini (cloud, free)
3. If fails → Use Local Model (Ollama, free, offline)
4. If fails → Use template

This means:
✓ Always works (offline backup)
✓ Saves API costs when local model works
✓ No internet required for fallback
✓ Never loses functionality


Troubleshooting
---------------

"Connection refused (tcp://localhost:11434)"
→ Ollama service not running
→ Open PowerShell and run: ollama serve

"Model generation timeout"
→ Your CPU is slow (or drive is slow)
→ Try smaller model: ollama pull phi
→ Or use: ollama pull neural-chat
→ Takes 1-3 min per email (vs seconds for cloud)

"Out of memory"
→ Your system doesn't have enough RAM
→ Close other apps or use cloud-only mode
→ (Edit config.py to disable local model)

"Ollama not working on corporate network"
→ Some networks block localhost connections
→ Use VPN or cloud-only mode
→ Contact IT to whitelist localhost:11434


Performance Tips
----------------

• First run downloads model (~2-5 min)
• Subsequent runs are instant
• Keep at least 2GB free disk space + 2GB RAM
• Close browser/heavy apps before generating
• On older systems, CPU generation takes 1-3 min per email

This is fine because you batch operations overnight!


Files Modified
--------------

config.py → Added OLLAMA settings
local_model_handler.py → New: Ollama integration
pitch_generator.py → Now tries: OpenRouter → Gemini → Ollama → Template
main.py → Option 9 tests local model setup
requirements.txt → No new requirements! (already have requests)


Next Steps
----------

1. Download & install Ollama from https://ollama.ai
2. Run: ollama pull phi
3. Run: ollama serve
4. Go to main menu option 9 to verify
5. Generate pitches and emails!


Questions?
----------

Ollama Docs: https://github.com/ollama/ollama
Local Model Guide: https://ollama.ai/library

For your use case (cold emails), mistral is the best choice:
• Excellent output quality for sales copy
• Fast enough for batch operations
• Smart enough to understand your offer
• Small enough to fit in limited resources
"""
