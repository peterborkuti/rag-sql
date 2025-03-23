import os
import pandas as pd
from sqlalchemy import StaticPool, create_engine
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.utilities import SQLDatabase

from app_config import AppConfig
from retrievertypes import State

class RetrieverDB:
    def __init__(self, csv_file):
        self.db = None
        self.table_info = None
        self._init_db(os.path.join(AppConfig.DATA_DIR, csv_file))

    def _column_descriptions(self):
        descriptions = {
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
        for table, columns in descriptions.items():
            column_desc_text += f"\nTable: {table}\n"
            for col, desc in columns.items():
                column_desc_text += f"- {col}: {desc}\n"

        return column_desc_text


    def _examples(self):
        return """
        --- EXAMPLES ---
        Question: How many text answers do we have?
        SQL: SELECT COUNT(*) FROM answers WHERE TYPE='SIMPLE_TEXT';
        Question: How many secret answers do we have?
        SQL: SELECT COUNT(*) FROM answers WHERE SECRET=1';
        Question: How many secret text answers do we have?
        SQL: SELECT COUNT(*) FROM answers WHERE TYPE='SIMPLE_TEXT' AND SECRET=1;
        """

    def _init_db(self, csv_file):
        # Load CSV into pandas
        df = pd.read_csv(csv_file, sep="\t")
        print(f"CSV loaded with {len(df)} rows and columns: {df.columns.tolist()}")

        # Create in-memory SQLite database from pandas DataFrame
        engine = create_engine(
            'sqlite:///:memory:',
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
            )
        df.to_sql('answers', engine, index=False)

        # Create LangChain SQLDatabase from SQLite connection
        self.db = SQLDatabase(engine=engine)
        #print(db.dialect)
        print("Usable table names:", self.db.get_usable_table_names())
        self.table_info = self.db.get_table_info()

        self.table_info += self._column_descriptions()
        self.table_info += self._examples()

    def execute_query(self, state: State):
        execute_query_tool = QuerySQLDatabaseTool(db=self.db)
        return {"result": execute_query_tool.invoke(state["query"])}