# Documentation

Operasyon prosedürleri, proje anayasası ve deployment notları.

## Contents

### Procedures
- Daily operational checklist
- Seed account management workflow
- Emergency response procedures

### Project Charter
- Mission: Viral X presence with 3 daily posts
- Approval workflow: Telegram-based (SEND/EDIT/SKIP)
- Risk management: High-risk content auto-SKIP rule

### Lock Standard
- **Path**: `C:\XHive\locks\x_session.lock`
- **Purpose**: Prevent concurrent execution with XiDeAI_Pro
- **Format**: Timestamp + process ID
- **TTL**: 24 hours (auto-cleanup)

### Deployment
- Desktop: Tauri build steps
- Worker: Docker/Python venv setup
- Monitoring: Log aggregation and alerting
- Backup: Data persistence strategy
