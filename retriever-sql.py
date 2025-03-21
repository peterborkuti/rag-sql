from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict


from langchain import hub
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool


from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict
import os

# Replace Groq with Ollama
from langchain_community.chat_models import ChatOllama
from langchain import hub
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.chat_models import init_chat_model

#groq api key
API_KEY="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"
os.environ["GROQ_API_KEY"] = API_KEY

DB_USERNAME=os.environ.get("DB_USERNAME")
DB_PASSWORD=os.environ.get("DB_PASSWORD")
DB_URL=os.environ.get("DB_URL")
DB_URL_LAST_PART=DB_URL.split("//")[-1]
DB_URL_PYTHON=f"oracle+oracledb://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL_LAST_PART}"
SCHEMA="ERFI_USER"
print(DB_URL_PYTHON)


llm = init_chat_model("llama3-8b-8192", model_provider="groq")

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

db = SQLDatabase.from_uri(
    DB_URL_PYTHON,
    schema=SCHEMA,
    include_tables=['ui_report_answers_core'],
    )
print(db.dialect)
print(db.get_usable_table_names())

print('table info:', db.get_table_info())
#db.run("SELECT * FROM Artist LIMIT 10;")

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

assert len(query_prompt_template.messages) == 1
#query_prompt_template.messages[0].pretty_print()

from typing_extensions import Annotated


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

def question_answer(query='How many Employees are there?'):
    print('query', query)
    sql_query = write_query({"question": query})
    print ('sql query', sql_query)
    query_result = execute_query({"query": sql_query["query"]})
    print('query result', query_result)
    answer = generate_answer({"question": query, "query": sql_query["query"], "result": query_result["result"]})
    print(answer["answer"])

#print(db.get_table_info())
#question_answer()