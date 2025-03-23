import os
from langchain import hub
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser

from retrievertypes import QueryOutput, State

class LocalLLM():
    def __init__(self, sql_dialect, table_info, model_name="llama3"):
        self.sql_dialect = sql_dialect
        self.table_info = table_info
        self.query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            model=model_name, 
            temperature=0.1,  # Lower temperature for more deterministic outputs
            num_ctx=4096      # Increase context window for complex SQL queries
        )
        
        print(f"LocalLLM initialized with model: {model_name}")
        
        # Add SQL examples to help the model generate better queries

    def generate_sql_query(self, state: State):
        """Generate SQL query to fetch information."""
        
        # Create enhanced prompt with examples and specific instructions
        prompt = self.query_prompt_template.invoke(
            {
                "dialect": self.sql_dialect,
                "top_k": 10,
                "table_info": self.table_info,
                "input": state["question"],
            }
        )  
     
        #print(prompt)
        response = self.llm.invoke(prompt)
        
        # Extract SQL from the response
        sql_query = self._extract_sql_from_response(response)
        
        return {"query": sql_query}
    
    def _extract_sql_from_response(self, text):
        """Extract SQL query from the LLM response."""
        # Try to extract SQL from code blocks
        if "```sql" in text:
            # Extract SQL between ```sql and ```
            query = text.split("```sql")[1].split("```")[0].strip()
        elif "```" in text:
            # Extract content between ``` blocks (generic code block)
            query = text.split("```")[1].split("```")[0].strip()
        else:
            # Just use the text as is
            query = text.strip()
        
        # Clean up the query
        query = query.replace("\n", " ").strip()
        return query

    def generate_answer(self, state: State):
        """Answer question using retrieved information as context."""
        prompt = (
            "Given the following user question, corresponding SQL query, "
            "and SQL result, answer the user question.\n\n"
            f'Question: {state["question"]}\n'
            f'SQL Query: {state["query"]}\n'
            f'SQL Result: {state["result"]}\n\n'
            "Provide a clear, concise answer based on the SQL result. "
            "If the result is empty, say so. If there's an error, explain what might be wrong."
        )

        response = self.llm.invoke(prompt)
        
        # Clean up response (remove any markdown formatting if present)
        answer = response.strip()
        return {"answer": answer}