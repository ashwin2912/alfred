from issue_analyzer import IssueAnalyzer
from commit_analyzer import CommitAnalyzer

class GitHubTools:
    """Wrapper for GitHub analysis tools"""
    def __init__(self, github_token: str):
        self.issue_analyzer = IssueAnalyzer(github_token)
        self.commit_analyzer = CommitAnalyzer(github_token)

    def analyze_issues(self, repo: str) -> str:
        """Fetch and analyze issues from a repository"""
        return self.issue_analyzer.analyze_repository(repo)

    def analyze_commits(self, repo: str) -> str:
        """Fetch and analyze commits from a repository"""
        return self.commit_analyzer.analyze_repository(repo)