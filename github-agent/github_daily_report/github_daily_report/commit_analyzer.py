import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_anthropic import ChatAnthropic
from datetime import datetime, timedelta
from github_client import GitHubClient

load_dotenv()

class CommitAnalyzer:
    """Manages commit analysis workflow using LangChain"""
    def __init__(self, github_token: str, llm_model: str = "gpt-4"):
        self.github_client = GitHubClient(github_token)
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            anthropic_api_key=anthropic_api_key
            )
        self.analysis_chain = self._create_analysis_chain()

    def fetch_commit_data(self, owner_and_repo: str) -> str:
        """Fetch commit data from GitHub"""
        owner, repo = owner_and_repo.split("/")
        since = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"  # Last 24 hours

        commits = self.github_client.get_commit_details(owner, repo, since)
        return str(commits)

    def _create_analysis_chain(self):
        """Create LangChain pipeline for summarizing commits"""
        prompt_template = self._get_prompt_template()
        prompt = PromptTemplate(template=prompt_template, input_variables=["commit_data"])

        def transform_input(input_data: dict) -> dict:
            commit_data = self.fetch_commit_data(input_data["owner_and_repo"])
            return {"commit_data": commit_data}

        chain = (
            {"commit_data": lambda x: transform_input(x)["commit_data"]}
            | prompt
            | self.llm
        )

        return chain

    def _get_prompt_template(self):
        """Returns prompt template for commit summarization"""
        return """
        Analyze the following commit history from GitHub and summarize the key changes:

        - Total number of commits
        - Most common contributors
        - Major code modifications (added/removed files)
        - Any significant bug fixes or new features

        Format the summary in markdown with clear sections.

        Data: {commit_data}
        """

    def analyze_repository(self, owner_and_repo: str) -> str:
        """Execute the commit analysis workflow"""
        result = self.analysis_chain.invoke({"owner_and_repo": owner_and_repo})
        return result.content
