from typing import Optional, Type  
import os  
from sqlalchemy.engine.url import URL  
from langchain.pydantic_v1 import BaseModel, Field, Extra  
from langchain.tools import BaseTool  
from langchain.sql_database import SQLDatabase  
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent  
from langchain_openai import AzureChatOpenAI  
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun  
import requests  
from datetime import datetime, timedelta  
  
try:  
    from .prompts import MSSQL_AGENT_PREFIX  
except ImportError as e:  
    print(e)  
    from prompts import MSSQL_AGENT_PREFIX  
  
####################################################################################################################################  
# AGENTS AND TOOL CLASSES  
####################################################################################################################################  
  
class SearchInput(BaseModel):  
    query: str = Field(description="should be a search query")  
    return_direct: bool = Field(  
        description="Whether or the result of this should be returned directly to the user without you seeing what it is",  
        default=False,  
    )  
  
class SQLSearchAgent(BaseTool):  
    """Agent to interact with SQL database"""  
  
    name = "sqlsearch"  
    description = "useful when the questions includes the term: sqlsearch.\n"  
    args_schema: Type[BaseModel] = SearchInput  
    llm: AzureChatOpenAI  
    k: int = 10  
  
    class Config:  
        extra = Extra.allow  # Allows setting attributes not declared in the model  
  
    def __init__(self, **data):  
        super().__init__(**data)  
        db_config = self.get_db_config()  
        db_url = URL.create(**db_config)  
        db = SQLDatabase.from_uri(db_url, schema="public", view_support=True)  
        toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)  
        self.agent_executor = create_sql_agent(  
            prefix=MSSQL_AGENT_PREFIX,  
            llm=self.llm,  
            toolkit=toolkit,  
            top_k=self.k,  
            agent_type="openai-tools",  
            callback_manager=self.callbacks,  
            verbose=self.verbose,  
        )  
  
    def get_db_config(self):  
        """Returns the database configuration."""  
        return {  
            'drivername': 'postgresql+psycopg2',  
            'username': os.environ["SQL_SERVER_USERNAME"],  
            'password': os.environ["SQL_SERVER_PASSWORD"],  
            'host': os.environ["SQL_SERVER_NAME"],  
            'port': 5432,  
            'database': os.environ["SQL_SERVER_DATABASE"]  
        }  
  
    def _run(self, query: str, return_direct=False, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:  
        try:  
            # Use the initialized agent_executor to invoke the query  
            result = self.agent_executor.invoke(query)  
            return result['output']  
        except Exception as e:  
            print(e)  
            return str(e)  # Return an error indicator  
  
    async def _arun(self, query: str, return_direct=False, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:  
        # Note: Implementation assumes the agent_executor and its methods support async operations  
        try:  
            # Use the initialized agent_executor to asynchronously invoke the query  
            result = await self.agent_executor.ainvoke(query)  
            return result['output']  
        except Exception as e:  
            print(e)  
            return str(e)  # Return an error indicator  
  
class GithubUpdateTool(BaseTool):  
    name = "github_update"  
    description = "Fetches GitHub updates for the given username from the environment variable for yesterday's date"  
  
    def _run(self) -> str:  
        """Use the tool."""  
        print("Running GithubUpdateTool")  
        username = os.getenv("GITHUB_USERNAME")  
        if not username:  
            print("Error: GITHUB_USERNAME environment variable is not set")  
            raise ValueError("GITHUB_USERNAME environment variable is not set")  
  
        # yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  
        yesterday = "2025-01-10"
        print(f"Fetching GitHub events for user: {username} on date: {yesterday}")  
        events = fetch_github_events(username, yesterday)  
        print(f"Fetched events: {events}")  
        return events  
  
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