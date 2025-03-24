
from db import RetrieverDB
from localllm import LocalLLM

db = RetrieverDB("ui_report_answer_core.csv")
llm = LocalLLM(db.db.dialect, db.table_info, 'llama3:latest')


def question_answer(query='How many addressee answered?'):
    #print('query', query)
    #sql_query = {'query': 'SELECT COUNT(*) FROM answers'}
    sql_query = llm.generate_sql_query({"question": query})
    print ('sql query', sql_query)
    query_result = db.execute_query({"query": sql_query["query"]})
    print('query result', query_result)
    #answer = {'answer': query_result["result"]}
    answer = llm.generate_answer({"question": query, "query": sql_query["query"], "result": query_result["result"]})
    print(answer["answer"])
    return sql_query["query"], answer["answer"]

if __name__ == "__main__":
    while True:
        question = input("Ask a question: ")
        if question == "exit":
            break
        print(question_answer(question))
