# Alfred

Digital butler to help run distributed teams through automation and integrations.

## Architecture

```mermaid
graph TB
    A[Alfred] --> B[click-up-agent]
    A --> C[github-agent]
    
    B --> D[ClickUp API]
    B --> E[Slack Webhook]
    
    C --> F[GitHub API]
    C --> G[Daily Reports]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
```

## Components

### click-up-agent
Syncs ClickUp task updates to Slack for team notifications.

### github-agent
Provides natural language interface for GitHub operations and generates daily reports.

## Setup

Each component has its own setup instructions. See individual README files in:
- `click-up-agent/README.md`
- `github-agent/README.md`