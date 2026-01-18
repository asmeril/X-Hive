# Worker Service (Python FastAPI + Playwright)

Python FastAPI-based background worker for X-HIVE.

## Overview
- Playwright ile X otomasyonu
- Scheduler ile periyodik görevler
- Telegram bot entegrasyonu
- Global lock: `C:\XHive\locks\x_session.lock` (XiDeAI_Pro ile paylaşılan)

## Architecture
- **API Framework**: FastAPI (async, modern)
- **Browser Automation**: Playwright (Chromium)
- **Scheduler**: APScheduler / background tasks
- **Data Storage**: SQLite / JSON
- **Concurrency Control**: File-based locks

## Features
- Intel gathering from multiple sources
- Post generation and queuing
- Automated X.com posting via Playwright
- Telegram approval workflow
- Daily 3-post target tracking
