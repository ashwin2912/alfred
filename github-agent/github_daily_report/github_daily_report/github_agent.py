import os
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate 
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langchain.tools import Tool
from github_tools import GitHubTools
from typing import TypedDict, Annotated

load_dotenv()

class AgentState(TypedDict):
   query: str
   repo: str
   result: str | None

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is required")
github_tools = GitHubTools(GITHUB_TOKEN)

# Tools
issue_tool = Tool(
   name="analyze_issues",
   func=github_tools.analyze_issues,
   description="Analyzes GitHub issues"
)

commit_tool = Tool(
   name="analyze_commits", 
   func=github_tools.analyze_commits,
   description="Analyzes GitHub commits"
)

tools = [issue_tool, commit_tool]
tool_node = ToolNode(tools=tools)

def process_query(state):
   query = state["query"].lower()
   if "issue" in query or "closed" in query:
       return {"analyze_issues": state}
   elif "commit" in query or "bug fix" in query or "feature" in query:
       return {"analyze_commits": state}
   return {"end": state}

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("process_query", process_query)
workflow.add_node("analyze_issues", tool_node)
workflow.add_node("analyze_commits", tool_node)

# Add edges
workflow.set_entry_point("process_query")
workflow.set_finish_point("end")

workflow.add_edge("analyze_issues", "end")
workflow.add_edge("analyze_commits", "end")

graph = workflow.compile()

def query_github(query: str, repo: str):
   return graph.invoke({"query": query, "repo": repo, "result": None})

if __name__ == "__main__":
   repo = "ashwin2912/fetch-tailored-reviews"
   
   print(query_github("Were there any bug fixes?", repo))
   print(query_github("How many issues closed?", repo))