# Stage 3: AI Summarization Module

This module provides AI-powered summarization and analysis of ClickUp task data using Claude (Anthropic).

## Overview

The AI module consists of two main components:

1. **TaskSummarizer** (`task_summarizer.py`) - Main class that orchestrates AI summarization
2. **Prompt Templates** (`prompts.py`) - LangChain prompt templates for different summary types

## Architecture

This module follows the same architecture pattern as `github-agent/commit_analyzer.py`:

- Uses **LangChain** for prompt management and chain orchestration
- Uses **ChatAnthropic** for Claude API integration
- Implements multiple specialized prompt templates for different use cases
- Follows the chain pattern: `Prompt Template → LLM → Response`

## Features

### 1. Person-Level Summaries
Generate comprehensive summaries for individual team members showing:
- Active tasks and progress
- Blockers and risks
- Recommended priorities

```python
from ai.task_summarizer import TaskSummarizer
from processing.data_aggregator import DataAggregator

summarizer = TaskSummarizer()
aggregator = DataAggregator(tasks)

person_data = aggregator.get_person_summary("alice")
summary = summarizer.summarize_person("alice", person_data)
```

### 2. Team-Level Summaries
Generate team-wide visibility reports showing:
- Overall team progress
- Task distribution
- Critical items and blockers
- Key insights and recommendations

```python
team_data = aggregator.get_team_summary()
summary = summarizer.summarize_team(team_data)
```

### 3. Blocker Analysis
Analyze and prioritize blockers with:
- Root cause analysis
- Impact assessment
- Actionable recommendations

```python
from processing.blocker_detector import BlockerDetector

detector = BlockerDetector(tasks)
blocker_summary = detector.get_blocker_summary()
analysis = summarizer.analyze_blockers(blocker_summary["all_blockers"])
```

### 4. Project Summaries
Generate project-specific status reports:
- Progress overview
- Team involvement
- Risks and milestones

```python
project_tasks = [t for t in tasks if t.list_id == "project-123"]
summary = summarizer.summarize_project("Project Alpha", project_tasks)
```

### 5. Daily Standup Summaries
Generate quick standup-style summaries:
- What was worked on
- What's in progress
- Current blockers

```python
person_data = aggregator.get_person_summary("bob")
standup = summarizer.generate_daily_standup("bob", person_data)
```

### 6. Decision Extraction
Extract key decisions from task comments and descriptions:
- Technical decisions
- Scope changes
- Priority shifts

```python
decisions = summarizer.extract_decisions(tasks)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `langchain>=0.1.0`
- `langchain-anthropic>=0.1.0`
- `anthropic>=0.25.0`

### 2. Configure API Key

Add your Anthropic API key to `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

Get your API key from: https://console.anthropic.com/

### 3. Configure Model

By default, the summarizer uses `claude-3-5-sonnet-20241022`. You can modify this in `task_summarizer.py`:

```python
self.llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # Change model here
    anthropic_api_key=anthropic_api_key
)
```

Available models:
- `claude-3-5-sonnet-20241022` (recommended, best balance)
- `claude-3-opus-20240229` (highest quality, more expensive)
- `claude-3-haiku-20240307` (fastest, cheapest)

## Testing

Run the test suite to see all features in action:

```bash
python test_stage3.py
```

The test script includes:
1. Person summary for Alice
2. Team-wide summary
3. Blocker analysis
4. Daily standup for Bob
5. Decision extraction
6. Project summary for backend tasks

### Sample Output

**Person Summary:**
```markdown
## Alice's Summary

### Overview
- Total tasks assigned: 3
- In Progress: 2, To Do: 1
- Overall Progress: On track with high-priority work

### Active Work
- **Implement user authentication API** (High Priority)
  - In progress, due tomorrow
  - Good progress on JWT implementation
  ...
```

## Prompt Customization

All prompts are defined in `prompts.py` and can be customized:

```python
def get_person_summary_prompt() -> PromptTemplate:
    template = """
    You are an AI assistant...
    
    Generate a summary with the following sections:
    - Overview
    - Active Work
    - Blockers
    ...
    """
    return PromptTemplate(template=template, input_variables=["person", "person_data"])
```

### Customization Tips

1. **Adjust tone**: Change the system message to be more formal/casual
2. **Add sections**: Include additional analysis points
3. **Format output**: Specify different markdown structures
4. **Focus areas**: Emphasize specific metrics or insights

## Integration with Stages 1 & 2

This module integrates seamlessly with the data processing layers:

```python
# Stage 1: Fetch data
from clients.clickup_client import ClickUpClient
client = ClickUpClient()
tasks = client.fetch_tasks_from_list("list-123")

# Stage 2: Process data
from processing.data_aggregator import DataAggregator
from processing.blocker_detector import BlockerDetector

aggregator = DataAggregator(tasks)
detector = BlockerDetector(tasks)

# Stage 3: Generate AI summaries
from ai.task_summarizer import TaskSummarizer
summarizer = TaskSummarizer()

# Person summary
person_data = aggregator.get_person_summary("alice")
summary = summarizer.summarize_person("alice", person_data)
print(summary)

# Blocker analysis
blockers = detector.get_blocker_summary()
analysis = summarizer.analyze_blockers(blockers["all_blockers"])
print(analysis)
```

## Performance Considerations

### Cost
- Claude Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- Average summary: 500-2000 input tokens, 300-1000 output tokens
- Estimated cost: $0.005-0.02 per summary

### Latency
- Average response time: 2-5 seconds
- Depends on prompt complexity and response length
- Use Haiku model for faster responses if needed

### Optimization Tips
1. **Batch requests**: Group multiple summaries if possible
2. **Cache results**: Store summaries and regenerate only when data changes
3. **Streaming**: Use streaming responses for better UX (not implemented yet)
4. **Model selection**: Use Haiku for simple summaries, Sonnet for complex analysis

## Error Handling

The TaskSummarizer includes basic error handling:

```python
try:
    summary = summarizer.summarize_person("alice", person_data)
except ValueError as e:
    print(f"Missing API key: {e}")
except Exception as e:
    print(f"Error generating summary: {e}")
```

Common errors:
- Missing `ANTHROPIC_API_KEY` → Add to `.env`
- Rate limiting → Add retry logic or reduce request frequency
- Invalid model name → Check model availability in Anthropic docs

## Future Enhancements

Potential improvements for this module:

1. **Streaming responses** - Real-time summary generation
2. **Caching layer** - Avoid regenerating unchanged summaries
3. **Multi-language support** - Generate summaries in different languages
4. **Sentiment analysis** - Analyze team morale from comments
5. **Trend detection** - Identify patterns over time
6. **Slack/email integration** - Auto-send summaries to team channels
7. **Custom report templates** - User-defined summary formats
8. **Comparative analysis** - Compare week-over-week progress

## Architecture Reuse

This module reuses ~90% of the architecture from `github-agent/commit_analyzer.py`:

**Reused Components:**
- LangChain integration pattern
- ChatAnthropic setup
- Chain architecture (`prompt | llm`)
- Environment variable handling
- Error handling patterns

**New Components (20% new code):**
- 6 specialized prompt templates for ClickUp data
- Multiple summarization methods (person, team, blockers, etc.)
- Integration with Stage 2 data processors

## References

- [LangChain Documentation](https://python.langchain.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
