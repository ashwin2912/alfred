import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commit_analyzer import CommitAnalyzer
from issue_analyzer import IssueAnalyzer


if __name__ == "__main__":
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    commit_analyzer = CommitAnalyzer(github_token=github_token)
    issue_analyzer = IssueAnalyzer(github_token=github_token)
    # Perform analysis
    result = commit_analyzer.analyze_repository("ashwin2912/fetch-tailored-reviews")
    print(result)

    result = issue_analyzer.analyze_repository("ashwin2912/fetch-tailored-reviews")
    print(result)