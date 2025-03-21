from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict


from langchain import hub
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool


from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict
import os
import pandas as pd
from sqlalchemy import create_engine

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
CSV_FILE='data/ui_report_answer_core.csv'

# Load CSV into pandas
df = pd.read_csv(CSV_FILE, sep="\t")
print(f"CSV loaded with {len(df)} rows and columns: {df.columns.tolist()}")

# Create in-memory SQLite database from pandas DataFrame
engine = create_engine('sqlite:///:memory:')
df.to_sql('answers', engine, index=False)

# Create LangChain SQLDatabase from SQLite connection
db = SQLDatabase(engine=engine)
#print(db.dialect)
#print(db.get_usable_table_names())
table_info = db.get_table_info()
column_descriptions = {
    "answers": {
        "ID": "Unique identifier for each answer entry in the database. Primary key for individual response records.",
        "ANSWER": "The actual response content provided by the respondent. Format varies based on TYPE column - may contain HTML tags for text responses, numeric values for ratings, pipe-delimited values for multiple choice selections (e.g., 'Option 1|Option 2|Option 3'), or confidentiality markers with <confidential-highlight> tags.",
        "TYPE": "Format type of the answer that determines how to interpret the ANSWER field. Common values include: CHOICE (single/multiple selection), RATING (numeric scale), CURRENCY (monetary value), SIMPLE_TEXT (free text), NUMBER (numeric value), EMAIL (email address), TIME (time format), DATE (date only), DATETIME (date and time), PHONE (telephone number), PERCENTAGE (percentage value), RANKING (ordered preferences with format '(1) First|(2) Second|(3) Third').",
        "QUESTION_ID": "Unique identifier linking to the specific question being answered. Can be joined with other question-related tables to get question text or metadata.",
        "ROW_QUESTION": "For table-based questions, contains the row label or description (e.g., company names like 'Microsoft', 'Google', or location names like 'Bruxelles', 'Anvers'). Empty for non-table questions.",
        "COLUMN_QUESTION_ID": "Identifier for the column question in table-based questions. Links to a specific column header or question aspect in a table-format question.",
        "COL_ID": "Technical identifier for the column in a table-based question. References the specific column's database ID.",
        "ROW_ID": "Technical identifier for the row in a table-based question. References the specific row's database ID.",
        "DATETIME": "Timestamp when the answer was submitted (format: DD-MMM-YY HH.MM.SS.NNNNNN AM/PM). Shows exactly when the respondent provided this specific answer.",
        "RESPONDENT": "Name or identifier of the person or entity who provided the answer (e.g., 'OutlookACC', 'DG COMP', 'Collab'). This can represent individuals, organizations, or system users.",
        "SECRET": "Flag indicating whether the answer contains confidential information (when SECRET=0 that means 'non confidential' or 'non-secret', when SECRET=1 that means, the answer itself is confidential or secret or part of the answer is secret or confidentialidential). Confidential answers often contain <confidential-highlight> tags in the ANSWER field.",
        "ADDR_RFI_DATA_ID": "Reference ID for the addressee or Request for Information data. Links to information about who was asked to provide this information.",
        "TABLE_QUESTION": "Indicates if the question is part of a table structure (0=not table, 1=table question). Determines whether ROW_QUESTION, COL_ID, ROW_ID fields are relevant.",
        "CASE_REFERENCE": "Reference code for the specific case or matter (e.g., 'DMA.400213', 'AT.49123', 'M.8871'). Identifies which legal case or investigation this answer relates to.",
        "ADDRESSEE_QUESTION_ID": "Identifier linking to the specific addressee of the question. Can help determine who was specifically asked this particular question."
    }
}

column_desc_text = "\n\n--- COLUMN DESCRIPTIONS ---\n"
for table, columns in column_descriptions.items():
    column_desc_text += f"\nTable: {table}\n"
    for col, desc in columns.items():
        column_desc_text += f"- {col}: {desc}\n"

table_info += column_desc_text

examples = """
--- EXAMPLES ---
Question: How many text answers do we have?
SQL: SELECT COUNT(*) FROM answers WHERE TYPE='SIMPLE_TEXT';
Question: How many secret answers do we have?
SQL: SELECT COUNT(*) FROM answers WHERE SECRET=1';
Question: How many secret text answers do we have?
SQL: SELECT COUNT(*) FROM answers WHERE TYPE='SIMPLE_TEXT' AND SECRET=1;
"""

table_info += examples

llm = init_chat_model("llama3-8b-8192", model_provider="groq")

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

# db = SQLDatabase.from_uri(
#    DB_URL_PYTHON,
#    schema=SCHEMA,
#    include_tables=['ui_report_answers_core'],
#    )
#print(db.dialect)
#print(db.get_usable_table_names())

#print('table info:', db.get_table_info())
#db.run("SELECT * FROM Artist LIMIT 10;")

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

#print(query_prompt_template)

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
            "table_info": table_info,
            "input": state["question"],

        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    #print("Prompt:", prompt)
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

    #print("Prompt:", prompt)
    response = llm.invoke(prompt)
    return {"answer": response.content}

def question_answer(query='How many addressee answered?'):
    #print('query', query)
    sql_query = write_query({"question": query})
    #print ('sql query', sql_query)
    query_result = execute_query({"query": sql_query["query"]})
    #print('query result', query_result)
    answer = generate_answer({"question": query, "query": sql_query["query"], "result": query_result["result"]})
    #print(answer["answer"])
    return sql_query, answer["answer"]

#print(db.get_table_info())
while True:
    question = input("Ask a question: ")
    if question == "exit":
        break
    print(question_answer(question))
