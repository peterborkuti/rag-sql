from retrievertypes import State


class FakeLLM():
    def __init__(self):
        
        print("FakeLLM initialized")
        
        # Add SQL examples to help the model generate better queries

    def generate_sql_query(self, state: State):
        """Generate SQL query to fetch information."""
        

        # Extract SQL from the response
        sql_query = "Fake SQL:SELECT COUNT(*) FROM answers"
        
        return {"query": sql_query}

    def generate_answer(self, state: State):
        prompt = (
            "Given the following user question, corresponding SQL query, "
            "and SQL result, answer the user question.\n\n"
            f'Question: {state["question"]}\n'
            f'SQL Query: {state["query"]}\n'
            f'SQL Result: {state["result"]}\n\n'
            "Provide a clear, concise answer based on the SQL result. "
            "If the result is empty, say so. If there's an error, explain what might be wrong."
        )

        return {"answer": "Fake answer: The answer table contains 10 rows."}