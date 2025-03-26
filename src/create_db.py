import os
import pandas as pd
from sqlalchemy import create_engine

from app_config import AppConfig

class CreateDB:
    def __init__(self, csv_file):
        csv_path = os.path.join(AppConfig.DATA_DIR, csv_file)
        data_path = os.path.join(AppConfig.DATA_DIR, 'data.db')
        if os.path.exists(data_path):
            # delete file
            os.remove(data_path)

        self._init_db(csv_path, data_path)

    def _init_db(self, csv_file, data_file):
        # Load CSV into pandas
        df = pd.read_csv(csv_file, sep="\t")
        print(f"CSV loaded with {len(df)} rows and columns: {df.columns.tolist()}")

        # Create in-memory SQLite database from pandas DataFrame
        first_engine = create_engine(
            'sqlite:///' + data_file
        )
        
        df.to_sql('answers', first_engine, index=False)

if __name__ == "__main__":
    CreateDB("ui_report_answer_core.csv")