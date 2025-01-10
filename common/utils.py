import re
import os
import json
from io import BytesIO
from typing import Any, Dict, List, Optional, Awaitable, Callable, Tuple, Type, Union
import asyncio

from collections import OrderedDict
from sqlalchemy.engine.url import URL

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field, Extra
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import BaseOutputParser, OutputParserException
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.prompts import PromptTemplate
from langchain.sql_database import SQLDatabase
from langchain.agents import AgentExecutor, initialize_agent, AgentType, Tool
from langchain.agents import create_sql_agent, create_openai_tools_agent
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.callbacks.base import BaseCallbackManager
from langchain.requests import RequestsWrapper
from langchain.chains import APIChain
from langchain.agents.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain.utils.json_schema import dereference_refs
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from typing import List



try:
    from .prompts import (MSSQL_AGENT_PREFIX)
except Exception as e:
    print(e)
    from prompts import (MSSQL_AGENT_PREFIX)

    

#####################################################################################################
############################### AGENTS AND TOOL CLASSES #############################################
#####################################################################################################
    
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
        db = SQLDatabase.from_uri(db_url, schema = "public", view_support = True,)
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

    def _run(self, query: str, return_direct = False, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # Use the initialized agent_executor to invoke the query
            result = self.agent_executor.invoke(query)
            return result['output']
        except Exception as e:
            print(e)
            return str(e)  # Return an error indicator

    async def _arun(self, query: str, return_direct = False, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        # Note: Implementation assumes the agent_executor and its methods support async operations
        try:
            # Use the initialized agent_executor to asynchronously invoke the query
            result = await self.agent_executor.ainvoke(query)
            return result['output']
        except Exception as e:
            print(e)
            return str(e)  # Return an error indicator