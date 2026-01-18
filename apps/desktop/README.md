# Desktop UI (Tauri + React)

Tauri + React-based user interface for X-HIVE.

## Overview
- Worker'a localhost API ile bağlanır
- Seed accounts yönetimi
- Draft review ve approval workflow
- Telegram onay entegrasyonu (SEND / EDIT / SKIP)

## Architecture
- **Framework**: Tauri (Rust backend) + React (TypeScript frontend)
- **API Client**: Fetch API (http://localhost:8765)
- **State Management**: React hooks
- **Styling**: Inline CSS / Tailwind CSS

## Features
- Real-time worker status monitoring
- Post approval interface
- Telegram notification integration
