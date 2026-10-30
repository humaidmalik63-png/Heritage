Environment facts for Hermes agent sessions.

Project directory: C:\Users\humai\AI

Python environment: .venv312\Scripts\python.exe (Python 3.12.10, torch 2.6.0+cpu, transformers 5.20.1, NumPy 2.5.4)

Key artifact paths (always verify before risky operations):
- data/processed/index/clip_index.faiss — SHA-256: de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6
- data/processed/index/mapping.json — SHA-256: dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c
- data/processed/index/candidate/phase6ab_validation.faiss — SHA-256: 4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98
- data/processed/index/candidate/phase6ab_validation_mapping.json — SHA-256: e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7

Tool quirks and gotchas:
- Terminal is CLI-only; Markdown does NOT render — asterisks, headers, and fences appear as literal characters; write plain text (indentation and blank lines are the only layout tools)
- Aversion to filler: 'Great question,' 'I'd be happy to' — never use these
- Does not restate the request back, re-summarize what already said, or narrate tool calls
- Aversion to drive-by cleanup or reformatting of code
- Values concise, direct responses over verbose narration
- When answering: lead with the change or answer, not a preamble
- Output is auto-truncated with the full text saved to a file; never pipe through head/tail to shorten it
- Cron jobs: LOCAL-ONLY; output saved but NOT delivered back into session
- No live-delivery channel in this session
- If user wants notification when job runs, job's deliver must target gateway-connected messaging platform
- Path arguments for NATIVE Windows programs are NOT translated: MSYS path conversion is disabled; prefer C:/Users/x-style forward-slash native paths
- On Windows, the machine hostname is NOT the username; use 'User home directory' to construct paths under C:\Users\<user>\

Session state:
- Session started: Tuesday, October 27, 2026 (India Standard Time, UTC+05:30)
- Model: auto
- Provider: custom
- Platform: cli
- Host: Windows (11)
- User home directory: C:\Users\humai

Before any operation that might touch existing artifacts:
- Record SHA-256 hashes and sizes of the four protected artifacts
- Verify them again at the end
- If any artifact changes, stop and report the discrepancy without attempting restoration

Do NOT modify another profile's skills/plugins/cron/memories unless the user explicitly directs you.