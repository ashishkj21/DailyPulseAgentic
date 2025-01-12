import requests
from datetime import datetime
from typing import Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

class GithubUpdateArgs(BaseModel):
    date: str = Field(description="Date to get the github update for")
    username: str = Field(description="Github username")

class GithubUpdateTool(BaseTool):
    name = "github_update"
    description = "useful for providing the github update for a given date and username"
    args_schema: Type[BaseModel] = GithubUpdateArgs

    def _run(
        self,
        date: str,
        username: str,
    ) -> str:
        """Use the tool."""
        events = fetch_github_events(username, date)
        return events

def fetch_github_events(username: str, target_date: str) -> str:
    """
    Fetch GitHub events for the user on the given date and return them as a human-readable string.
    """
    url = f"https://api.github.com/users/{username}/events/public"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Error: Received status code {response.status_code}")
    events = response.json()
    # Filter events by the target date
    filtered_events = [
        event for event in events
        if datetime.fromisoformat(event['created_at'].replace("Z", "+00:00")).date() == datetime.strptime(target_date, "%Y-%m-%d").date()
    ]

    # Process events and extract details
    event_details = []
    for event in filtered_events:
        event_type = event['type']
        repo_name = event['repo']['name']
        event_date = datetime.fromisoformat(event['created_at'].replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S')  

        details = f"Event Type: {event_type}\nRepository: {repo_name}\nDate: {event_date}"
        # Event-specific details
        if event_type == "PullRequestEvent":
            pr_details = event['payload']['pull_request']
            details += f"""
Action: {event['payload']['action']}
Pull Request URL: {pr_details['html_url']}
Title: {pr_details['title']}
Body: {pr_details['body']}"""
        elif event_type == "PushEvent":
            commits = event['payload']['commits']
            commit_details = "\n".join(
                f"  - Message: {commit['message']}\n    URL: {commit['url']}"
                for commit in commits
            )
            details += f"\nCommits:\n{commit_details}"
        elif event_type == "DeleteEvent":
            details += f"""
Ref Type: {event['payload']['ref_type']}
Ref: {event['payload']['ref']}"""
        elif event_type == "IssueCommentEvent":
            comment_details = event['payload']['comment']
            details += f"""
Action: {event['payload']['action']}
Issue URL: {event['payload']['issue']['html_url']}
Comment: {comment_details['body']}"""
        elif event_type == "IssuesEvent":
            issue_details = event['payload']['issue']
            details += f"""
Action: {event['payload']['action']}
Issue URL: {issue_details['html_url']}
Title: {issue_details['title']}
Body: {issue_details['body']}"""
        elif event_type == "CreateEvent":
            details += f"""
Ref Type: {event['payload']['ref_type']}
Ref: {event['payload'].get('ref', "N/A")}"""
  
        event_details.append(details)
  
    # Combine all events into a single formatted string
    return "\n\n".join(event_details) 