
import os
from langchain import hub
from langchain.chat_models import init_chat_model

from retrievertypes import QueryOutput, State

# You need to set groq API key in the environment variable: GROQ_API_KEY
# https://console.groq.com/keys
class GrokLLM():
    def __init__(self, sql_dialect, table_info):
        self.sql_dialect = sql_dialect
        self.table_info = table_info
        self.query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")
        self.llm = init_chat_model("llama3-8b-8192", model_provider="groq")

    def generate_sql_query(self, state: State):
        """Generate SQL query to fetch information."""

        prompt = self.query_prompt_template.invoke(
            {
                "dialect": self.sql_dialect,
                "top_k": 10,
                "table_info": self.table_info,
                "input": state["question"],

            }
        )
        structured_llm = self.llm.with_structured_output(QueryOutput)
        #print("Prompt:", prompt)
        result = structured_llm.invoke(prompt)
        return {"query": result["query"]}

    def generate_answer(self, state: State):
        """Answer question using retrieved information as context."""
        prompt = (
            "Given the following user question, corresponding SQL query, "
            "and SQL result, answer the user question.\n\n"
            f'Question: {state["question"]}\n'
            f'SQL Query: {state["query"]}\n'
            f'SQL Result: {state["result"]}'
        )

        #print("Prompt:", prompt)
        response = self.llm.invoke(prompt)
        return {"answer": response.content}


