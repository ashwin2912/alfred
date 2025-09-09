from tools.clickup_fetcher import fetch_clickup_tasks
from tools.slack_notifier import post_to_slack

def format_tasks_for_slack(tasks) -> str:
    """
    Format raw task info into a Slack-readable message.
    """
    lines = ["*📝 ClickUp Tasks Update:*", ""]

    for task in tasks:
        assignees = ", ".join(task.assignees)
        lines.append(f"• *{task.name}* [{task.status}]")
        lines.append(f"   👤 {assignees} | 🔗 <{task.url}|View Task>")
        lines.append("")

    return "\n".join(lines)

def main():
    print("📥 Fetching tasks...")
    tasks = fetch_clickup_tasks()

    if not tasks:
        print("✅ No tasks to report.")
        return

    slack_msg = format_tasks_for_slack(tasks)
    print("📤 Sending to Slack:\n")
    print(slack_msg)

    post_to_slack(slack_msg)
    print("✅ Posted to Slack.")

if __name__ == "__main__":
    main()
