# Shared Contracts

Ortak JSON şemalar, TypeScript ve Python tipleri.

## Purpose
Desktop ve Worker arasında paylaşılan veri yapıları, API kontratları ve validasyon kuralları.

## Contents
- **JSON Schemas**: API request/response validation
- **TypeScript Interfaces**: Frontend type definitions
- **Python Dataclasses**: Backend type definitions
- **Constants**: Shared enums and configuration values

## Examples

### PostProposal (shared data structure)
```typescript
interface PostProposal {
  id: string;
  content: string;
  sources: string[];
  riskLevel: "low" | "medium" | "high";
  timestamp: string;
}
```

### ApprovalAction
```typescript
type ApprovalAction = "SEND" | "EDIT" | "SKIP";
```

## Usage
Import and validate data across Desktop and Worker services.
