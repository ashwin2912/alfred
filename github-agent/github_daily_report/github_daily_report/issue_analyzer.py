import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_anthropic import ChatAnthropic
from github_client import GitHubClient

load_dotenv()

class IssueAnalyzer:
    """Manages the GitHub issue analysis workflow"""
    def __init__(self, github_token: str, llm_model: str = "gpt-4"):
        self.github_client = GitHubClient(github_token)
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        self.analysis_chain = self._create_analysis_chain()

    def fetch_issue_data(self, owner_and_repo: str) -> str:
        """Fetch issues and comments from GitHub repository"""
        owner, repo = owner_and_repo.split("/")
        issue_data = self.github_client.get_issues(owner, repo)
        return str(issue_data)

    def _create_analysis_chain(self):
        """Create LangChain processing chain"""
        prompt_template = self._get_prompt_template()
        prompt = PromptTemplate(template=prompt_template, input_variables=["issues_data"])

        def transform_input(input_data: dict) -> dict:
            issues_data = self.fetch_issue_data(input_data["owner_and_repo"])
            return {"issues_data": issues_data}

        chain = (
            {"issues_data": lambda x: transform_input(x)["issues_data"]}
            | prompt
            | self.llm
        )

        return chain

    def _get_prompt_template(self):
        """Returns a structured prompt for issue analysis"""
        return """
        Analyze the GitHub issues data and provide a structured summary including:
        - Total number of issues
        - Open vs closed ratio
        - Most active issue authors
        - Most commented issues
        - Common labels
        - Notable comment patterns

        Format the summary in markdown with clear sections.

        Data: {issues_data}
        """

    def analyze_repository(self, owner_and_repo: str) -> str:
        """Execute the full issue analysis workflow"""
        result = self.analysis_chain.invoke({"owner_and_repo": owner_and_repo})
        return result.content