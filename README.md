# X-HIVE

Viral X presence automation: 3 daily posts with Telegram-based approval workflow.

## Mission
Automate social media content generation, curation, and posting to X (Twitter) with AI-powered decision making and human approval gates.

## Features

### Daily Posts
- **Target**: 3 posts per day
- **Approval**: Telegram bot (SEND / EDIT / SKIP)
- **Risk Management**: High-risk/controversial content → auto SKIP

### Intel Sources
- Telegram channels (Tele-Sentinel)
- Prediction markets
- X seed accounts (≥50 followers)

### Global Lock Standard
- **Path**: `C:\XHive\locks\x_session.lock`
- **Purpose**: Prevent concurrent execution with XiDeAI_Pro
- **TTL**: 24 hours (auto-cleanup)

## Architecture

```
X-HIVE Monorepo
├── apps/
│   ├── desktop/           # Tauri + React UI (approval interface)
│   └── worker/            # Python FastAPI + Playwright (automation)
├── packages/
│   └── contracts/         # Shared schemas & types
└── docs/                  # Procedures & documentation
```

### Desktop (Tauri + React)
- Seed account management
- Draft review interface
- Real-time worker status
- Telegram integration notifications

### Worker (Python FastAPI + Playwright)
- Intel gathering from multiple sources
- Post generation and queuing
- Automated X.com posting
- Telegram approval workflow
- Scheduler with daily 3-post target

## Getting Started

### Worker Setup
```bash
cd apps/worker
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

### Desktop Setup
```bash
cd apps/desktop
npm install
npm run tauri dev
```

## Modules

- **apps/desktop**: Tauri + React UI for approval interface
- **apps/worker**: Python FastAPI backend for automation
- **packages/contracts**: Shared data schemas and types
- **docs**: Operational procedures and deployment guides
