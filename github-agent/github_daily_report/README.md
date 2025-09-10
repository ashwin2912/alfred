# GitHub Daily Report

Analyzes GitHub repositories to generate daily activity reports including commits and issues.

## Architecture

```mermaid
flowchart TD
    A[main.py] --> B[GitHub Client]
    A --> C[Commit Analyzer]
    A --> D[Issue Analyzer]
    
    B --> E[GitHub API]
    C --> F[Commit Data]
    D --> G[Issue Data]
    
    F --> H[Daily Report]
    G --> H
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style H fill:#fce4ec
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure GitHub token in `main.py`

3. Run analysis:
   ```bash
   python main.py
   ```

## Components

- `commit_analyzer.py` - Analyzes repository commits
- `issue_analyzer.py` - Analyzes repository issues
- `github_client.py` - GitHub API client
- `main.py` - Entry point