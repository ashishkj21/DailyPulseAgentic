import requests
from datetime import datetime

def fetch_github_events(username, target_date):
    """
    Fetch all GitHub events for a specific user on a given date.

    Args:
        username (str): GitHub username.
        target_date (str): Date in YYYY-MM-DD format.

    Returns:
        list: A list of dictionaries containing event details.
    """
    url = f"https://api.github.com/users/{username}/events/public"
    
    # Fetch the events
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []

    events = response.json()

    # Filter events by target date
    filtered_events = [
        event for event in events
        if datetime.fromisoformat(event['created_at'].replace("Z", "+00:00")).date() == datetime.strptime(target_date, "%Y-%m-%d").date()
    ]

    # Process events and extract detailed information
    event_details = []
    for event in filtered_events:
        event_type = event['type']
        repo_name = event['repo']['name']
        event_date = datetime.fromisoformat(event['created_at'].replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S')

        # Base information
        details = {
            "Type": event_type,
            "Repository": repo_name,
            "Date": event_date,
            "Details": {}
        }

        # Add event-specific details
        if event_type == "PullRequestEvent":
            details["Details"] = {
                "Action": event['payload']['action'],
                "Pull Request URL": event['payload']['pull_request']['html_url'],
                "Title": event['payload']['pull_request']['title'],
                "Body": event['payload']['pull_request']['body']
            }

        elif event_type == "PushEvent":
            details["Details"] = {
                "Commits": [
                    {"Message": commit['message'], "URL": commit['url']}
                    for commit in event['payload']['commits']
                ]
            }

        elif event_type == "DeleteEvent":
            details["Details"] = {
                "Ref Type": event['payload']['ref_type'],
                "Ref": event['payload']['ref']
            }

        elif event_type == "IssueCommentEvent":
            details["Details"] = {
                "Action": event['payload']['action'],
                "Issue URL": event['payload']['issue']['html_url'],
                "Comment": event['payload']['comment']['body']
            }

        elif event_type == "IssuesEvent":
            details["Details"] = {
                "Action": event['payload']['action'],
                "Issue URL": event['payload']['issue']['html_url'],
                "Title": event['payload']['issue']['title'],
                "Body": event['payload']['issue']['body']
            }

        elif event_type == "CreateEvent":
            details["Details"] = {
                "Ref Type": event['payload']['ref_type'],
                "Ref": event['payload'].get('ref', "N/A")
            }

        # Append processed event
        event_details.append(details)

    return event_details

# Example usage:
username = "ashishkj21"
target_date = "2025-01-09"  # YYYY-MM-DD format
events = fetch_github_events(username, target_date)

# Print all events
for event in events:
    print(f"Event Type: {event['Type']}")
    print(f"Repository: {event['Repository']}")
    print(f"Date: {event['Date']}")
    print("Details:")
    for key, value in event['Details'].items():
        print(f"  {key}: {value}")
    print("-" * 40)