import requests
import json
from datetime import datetime

# Linear API Configuration
API_URL = "https://api.linear.app/graphql"
API_KEY = "lin_api_8b9SoXx2FNXK0cbVhNSUIHRU4RG6rwl4k6V9RtgY"  # Replace with your Linear API Key

# GraphQL Query to fetch user ID dynamically
USER_QUERY = """
query GetUserByEmail($email: String!) {
    users(filter: {email: {eq: $email}}) {
        nodes {
            id
            name
            email
        }
    }
}
"""

# GraphQL Query to fetch issues associated with a user
ACTIVITIES_QUERY = """
query UserActivities($userId: ID!) {
    issues(filter: {assignee: {id: {eq: $userId}}}) {
        nodes {
            id
            title
            updatedAt
            createdAt
            state {
                name
            }
            comments {
                nodes {
                    body
                    createdAt
                }
            }
        }
    }
}
"""

def fetch_user_id(email):
    # Set up headers
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    # Variables for the query
    variables = {
        "email": email
    }

    # Make the request
    response = requests.post(API_URL, headers=headers, json={"query": USER_QUERY, "variables": variables})

    # Check for errors
    if response.status_code != 200:
        print(f"Error fetching user ID: {response.status_code}, {response.text}")
        return None

    data = response.json()
    users = data.get("data", {}).get("users", {}).get("nodes", [])
    if not users:
        print("No user found with the provided email.")
        return None

    return users[0]["id"]  # Return the first user's ID

def fetch_user_activities(user_id):
    # Set up headers
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    # Variables for the query
    variables = {
        "userId": user_id
    }

    # Make the request
    response = requests.post(API_URL, headers=headers, json={"query": ACTIVITIES_QUERY, "variables": variables})

    # Check for errors
    if response.status_code != 200:
        print(f"Error fetching user activities: {response.status_code}, {response.text}")
        return None

    data = response.json()
    return data

def fetch_github_events(username: str, target_date: str) -> str:  
    """  
    Fetch GitHub events for the user on the given date and return them as a human-readable string.  
    """    
    url = f"https://api.github.com/users/{username}/events/public"  
    response = requests.get(url)  
    if response.status_code != 200:  
        print(f"Error: Received status code {response.status_code}")  
        raise ValueError(f"Error: Received status code {response.status_code}")  
  
    events = response.json() 
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
                Body: {pr_details['body']}  
            """  
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
                Ref: {event['payload']['ref']}  
            """  
        elif event_type == "IssueCommentEvent":  
            comment_details = event['payload']['comment']  
            details += f"""  
                Action: {event['payload']['action']}  
                Issue URL: {event['payload']['issue']['html_url']}  
                Comment: {comment_details['body']}  
            """  
        elif event_type == "IssuesEvent":  
            issue_details = event['payload']['issue']  
            details += f"""  
                Action: {event['payload']['action']}  
                Issue URL: {issue_details['html_url']}  
                Title: {issue_details['title']}  
                Body: {issue_details['body']}  
            """  
        elif event_type == "CreateEvent":  
            details += f"""  
                Ref Type: {event['payload']['ref_type']}  
                Ref: {event['payload'].get('ref', "N/A")}  
            """  
  
        event_details.append(details)  
  
    # Combine all events into a single formatted string  
    return "\n\n".join(event_details)

if __name__ == "__main__":
    # Replace with your Linear email
    USER_EMAIL = "jha.ashish.kj@gmail.com"  # Replace with your email

    # Fetch user ID
    user_id = fetch_user_id(USER_EMAIL)
    if not user_id:
        print("Failed to retrieve user ID. Exiting.")
        exit(1)

    print(f"User ID: {user_id}")

    # Fetch and print activities
    activities = fetch_user_activities(user_id)
    if activities:
        print(json.dumps(activities, indent=2))

    # Example usage of fetch_github_events
    GITHUB_USERNAME = "octocat"  # Replace with the GitHub username
    TARGET_DATE = "2023-10-01"  # Replace with the target date

    github_events = fetch_github_events(GITHUB_USERNAME, TARGET_DATE)
    print(github_events)