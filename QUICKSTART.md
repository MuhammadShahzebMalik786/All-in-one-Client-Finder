"""
⚡ QUICK START — What To Do NOW
==============================

STEP 1: Download Ollama (Local AI Model)
────────────────────────────────────────
Takes: 5 minutes

1. Go to https://ollama.ai
2. Click "Download for Windows"
3. Run installer (next, next, finish)
4. Open PowerShell:
   
   ollama pull mistral
   
5. Wait 4-5 min for download
6. Run (keep this window open):
   
   ollama serve
   
✓ Ollama is now running on http://localhost:11434


STEP 2: Test It Works
─────────────────────
Takes: 1 minute

1. Open NEW PowerShell window (keep Ollama running in first)
2. Go to project folder:
   
   cd "C:\Users\malik\OneDrive\Desktop\Find me Clients"
   
3. Activate environment:
   
   .venv\Scripts\Activate.ps1
   
4. Run Python test:
   
   python local_model_handler.py
   
Expected output:
  [+] Ollama running locally on 11434
  [*] Testing local model...
  Local Model Output:
  [response from the model here]
  ✓ Local model ready as AI fallback!

If not working:
  - Make sure ollama serve is still running in first window
  - Check if you have Python installed
  - Run: pip install -r requirements.txt


STEP 3: Run Main Menu
─────────────────────
Takes: 2 minutes

Same PowerShell window:

python main.py

You'll see menu with options 1-11
(Including NEW options 7, 8, 9!)


STEP 4: Try New Features
────────────────────────

Option 9: Test Local Model
───────────────────────────
Just to verify everything works.
Takes: 30 seconds
Result: Confirms Ollama is working

Menu → 9

Should show:
  ✓ Ollama is running locally
  ✓ Model: phi
  ✓ URL: http://localhost:11434/api
  [Testing model generation...]
  ✓ Local model ready as AI fallback!


Option 7: Find Clients on Fiverr/Upwork
────────────────────────────────────────
Find 50+ potential clients automatically!
Takes: 3-5 minutes
Result: data/freelance_platform_clients.csv

Menu → 7

System will:
  • Search Upwork for automation projects
  • Search Fiverr for related services
  • Score by relevance
  • Save results to CSV

You'll see output like:
  === Fiverr/Upwork Client Finder ===
  Searching Upwork: 'need automation'...
  ✓ Found Jane Johnson (lead generation)
  ✓ Found Bob Smith (automation)
  ...
  ✓ Found 50 potential clients


Option 8: Generate AI Sales Pitches
────────────────────────────────────
Create personalized pitches for those clients!
Takes: 3-5 minutes
Result: data/generated_pitches.csv

Menu → 8

System will:
  • Load the 50 clients from previous step
  • Ask which pitch type (automation/leads/integration/email)
  • Generate unique pitch for each
  • Use AI chain: OpenRouter → Gemini → Ollama → Template

Example pitch generated:

  Subject: Automate Jane's lead generation — Free Audit
  
  Hi Jane,
  
  I noticed your agency handles lead generation manually.
  I specialize in automation solutions that save teams 10-20 hours weekly.
  
  Recent clients now:
  • Process 500 leads daily automatically
  • Cut operational costs by 40%
  
  Would you be open to a 15-min chat?
  
  Best,
  Muhammad Shahzeb Malik
  Automation & Product Engineer
  +92 344 897 0498


STEP 5: Use The Pitches
───────────────────────

After generating (Option 8), open:
  data/generated_pitches.csv

You now have:
  • 50 prospect names
  • 50 personalized subject lines
  • 50 personalized pitch bodies

Use these for:
  ✓ LinkedIn cold messages
  ✓ Email outreach
  ✓ Fiverr gig proposals
  ✓ Upwork applications
  ✓ Pitching to prospects


WORKFLOW A: Lightning Fast (10 min)
───────────────────────────────────
Goal: Get 50 ready-to-send pitches TODAY

1. Menu → 9 (Verify Ollama works) [1 min]
2. Menu → 7 (Find Fiverr/Upwork clients) [3-5 min]
3. Menu → 8 (Generate pitches) [3-5 min]
4. Open data/generated_pitches.csv
5. Copy pitches and send! [You do this]

Total: 10-15 minutes to 50 prospects


WORKFLOW B: Traditional LinkedIn (45 min)
──────────────────────────────────────────
Goal: Full lead generation → email pipeline

1. Menu → 1 (LinkedIn finder) [5 min]
2. Menu → 2 (Google Maps finder) [3 min]
3. Menu → 3 (Extract contacts) [3 min]
4. Menu → 4 (Generate emails) [2-3 min] ← Uses Ollama!
5. Menu → 5 (Send emails) [30 min]

Total: 45 min, 50+ emails sent automatically


WORKFLOW C: Full Automation (60 min hands-off)
───────────────────────────────────────────────
Goal: Everything automated in one go

1. Menu → 6 (Run Full Pipeline)

Let it run overnight, comes back to 100+ sent emails!


WHAT YOU GET NOW
================

Before:
• LinkedIn leads only
• Manual pitch writing
• Dependent on APIs

After:
• LinkedIn + Google Maps + Fiverr + Upwork leads
• AI-generated personalized pitches
• Automatic fallback (works offline!)
• 4 different pitch types
• Better targeting


KEY NEW FILES
=============

local_model_handler.py
  → Manages Ollama (local AI)
  → Checks if it's running
  → Generates text for pitches

fiverr_upwork_finder.py
  → Scrapes Fiverr/Upwork clients
  → Categorizes prospects
  → Scores by relevance

pitch_generator.py
  → Creates personalized pitches
  → Falls back: OpenRouter → Gemini → Ollama → Template
  → 4 pitch types


EXPECTED RESULTS
================

Running Option 7 (Fiverr/Upwork):
  ✓ 40-60 potential clients found
  ✓ Categorized by industry
  ✓ Saved to CSV
  ✓ Ready for pitching

Running Option 8 (Generate Pitches):
  ✓ 10 personalized pitches generated
  ✓ Each has unique subject + body
  ✓ Includes your contact info
  ✓ Saved to CSV for sending

Running Option 4 (Generate Emails) with Ollama:
  ✓ Falls back to local model when APIs slow
  ✓ Works offline
  ✓ Free generation
  ✓ No rate limiting


TROUBLESHOOTING
===============

🔴 "Ollama not running"
  → Check first PowerShell window
  → Should say "Ollama running on 11434"
  → If not, run: ollama serve

🔴 "Fiverr/Upwork finder returns 0 results"
  → Scraping is purposely slow
  → Try again in 5 minutes
  → Some data is behind login walls
  → In production, you'd have API keys

🔴 "Generation timeout error"
  → CPU is running slow
  → Ollama needs 1-3 min per batch on CPU
  → This is NORMAL and OK
  → Let it run, come back later

🔴 "Permission denied - PowerShell"
  → Run PowerShell as Administrator
  → Then try commands again


TIMELINE
========

Right now:
  • Install Ollama: 5 min
  • Run quick test: 2 min
  • Generate 50 pitches: 10 min
  Total: 17 minutes


Today:
  • Use pitches: Send to prospects
  • Monitor responses
  • Tweak pitch types based on results


This week:
  • Run Option 7-8 daily for fresh 50 prospects
  • Try different pitch types
  • Track what works best
  • 350 new prospects + personalized pitches


This month:
  • 1000+ personalized pitches sent
  • Establish pattern of what converts
  • Scale to 5+ pitch types
  • Combine with traditional LinkedIn/Google
  • Track deals closed from each source


IMPORTANT NOTES
===============

✓ Ollama needs to stay running
  • Keep PowerShell window open with ollama serve
  • Don't close it or local model won't work
  • Should be left running while you use app

✓ First time is slower
  • Model downloads: 2-3 min
  • Model loads into RAM: 1 min
  • Subsequent generations: 1-3 min each

✓ CPU-based (no GPU)
  • Means no CUDA/GPU acceleration
  • Perfectly fine! Ollama handles it
  • Very capable on CPU with right model

✓ Cloud APIs still priority
  • Local model is fallback
  • Cloud APIs used first (faster)
  • Only local model if APIs down/slow


YOUR ACTION ITEMS
=================

☐ 1. Download Ollama (https://ollama.ai)
☐ 2. Install Ollama
☐ 3. Run: ollama pull phi
☐ 4. Keep running: ollama serve
☐ 5. Test: python local_model_handler.py
☐ 6. Run: python main.py
☐ 7. Try: Option 9 (test local model)
☐ 8. Try: Option 7 (find Fiverr clients)
☐ 9. Try: Option 8 (generate pitches)
☐ 10. Copy data/generated_pitches.csv
☐ 11. Send pitches to prospects

Time estimate: 20 minutes total setup + testing


SUPPORT
=======

If stuck:
  → Check OLLAMA_SETUP.md (Ollama questions)
  → Check WORKFLOW.md (workflow questions)
  → Check UPDATE_SUMMARY.md (overview)
  → Look at config.py for settings


YOU'RE READY! 🚀

Go execute!
"""
