import requests
from datetime import datetime, timedelta
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

class GitHubClient:
    """Handles GitHub API requests using GraphQL and REST"""
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.graphql_url = "https://api.github.com/graphql"

    def execute_query(self, query: str, variables: dict) -> dict:
        """Executes a GraphQL query"""
        response = requests.post(self.graphql_url, json={"query": query, "variables": variables}, headers=self.headers)
        return response.json()

    def get_commit_details(self, owner: str, repo: str, since: str) -> list:
        """Fetches recent commits using GraphQL"""
        query = """
        query RecentCommits($owner: String!, $repo: String!, $since: GitTimestamp!) {
            repository(owner: $owner, name: $repo) {
                ref(qualifiedName: "refs/heads/github-client") {
                    target {
                        ... on Commit {
                            history(since: $since, first: 10) {
                                edges {
                                    node {
                                        oid
                                        message
                                        committedDate
                                        author { name email }
                                        url
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"owner": owner, "repo": repo, "since": since}
        data = self.execute_query(query, variables)
        commits = data.get("data", {}).get("repository", {}).get("ref", {}).get("target", {}).get("history", {}).get("edges", [])
        
        commit_list = []
        for commit in commits:
            commit_data = commit["node"]
            commit_details = {
                "sha": commit_data["oid"],
                "message": commit_data["message"],
                "author": commit_data["author"]["name"],
                "email": commit_data["author"]["email"],
                "date": commit_data["committedDate"],
                "url": commit_data["url"],
                "files": self.get_commit_files(owner, repo, commit_data["oid"])  # Fetch file changes
            }
            commit_list.append(commit_details)

        return commit_list

    def get_issues(self, owner: str, repo: str) -> dict:
        """Fetches issue data from GitHub"""
        query = """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                issues(first: 10) {
                    nodes {
                        title
                        state
                        number
                        createdAt
                        author { login }
                        comments(first: 50) {
                            nodes {
                                body
                                createdAt
                                author { login }
                            }
                        }
                        labels(first: 10) {
                            nodes { name }
                        }
                    }
                }
            }
        }
        """
        return self.execute_query(query, {"owner": owner, "repo": repo})
            


    def get_commit_files(self, owner: str, repo: str, commit_sha: str) -> list:
        """Fetches changed files for a commit using GitHub REST API"""
        commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
        response = requests.get(commit_url, headers=self.headers)
        commit_data = response.json()

        files = []
        for file in commit_data.get("files", []):
            files.append({
                "filename": file["filename"],
                "changes": file["changes"],
                "additions": file["additions"],
                "deletions": file["deletions"],
                "patch": file.get("patch", "No patch available")
            })
        return files


