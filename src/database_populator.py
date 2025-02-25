import os
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import insert
from src.mysql_database import Patient, Measurement
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DatabasePopulator:
    def __init__(self, db, history_file, user="root", password="password", host="127.0.0.1", port=3306):
        self.db = db
        self.history_file = history_file
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        logging.info(f"database_populator.py: Database URI: {self.database_uri}")
        try:
            self.engine = create_engine(self.database_uri, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            logging.info("database_populator.py: MySQL database connection established.")
        except SQLAlchemyError as e:
            logging.error(f"database_populator.py: Error initializing database connection: {e}")

    def populate(self):
        """Populate the database with patient and measurement data."""
        if not self.db_has_tables():
            logging.warning("database_populator.py: Database has no tables, please create tables first.")
            return
        if self.db_has_tables() and not self.db_is_populated():
            logging.info("database_populator.py: Database is empty, populating with history data.")
            self.add_history_to_db()
            logging.info("database_populator.py: Database populated successfully.")
        else:
            logging.info("database_populator.py: Everything is already OK with the database, no need to populate.")
        
    def add_history_to_db(self):
        """
        Reads the history CSV file and populates the database with patient and measurement data.
        """
        try:
            df = pd.read_csv(self.history_file)
            session = self.Session()

            for index, row in df.iterrows():
                mrn = row['mrn']

                # Insert or update patient record
                stmt = insert(Patient).values(mrn=mrn, age=None, sex=None)
                stmt = stmt.on_duplicate_key_update(age=stmt.inserted.age, sex=stmt.inserted.sex)
                session.execute(stmt)

                # Find max index for creatinine measurements
                max_index = max([int(col.split('_')[2]) for col in row.keys() if 'creatinine_date' in col], default=0)

                for i in range(1, max_index + 1):
                    date = row.get(f'creatinine_date_{i}')
                    result = row.get(f'creatinine_result_{i}')

                    # Skip if date or result is missing
                    if pd.isna(date) or pd.isna(result):
                        continue

                    # Convert date to correct format
                    try:
                        parsed_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")  # Adjust format if needed
                    except ValueError:
                        logging.warning(f"database_populator.py: Invalid date format for MRN {mrn}: {date}")
                        continue

                    # Insert measurement
                    stmt = insert(Measurement).values(mrn=mrn, creatinine_date=parsed_date, creatinine_result=result)
                    stmt = stmt.on_duplicate_key_update(creatinine_result=stmt.inserted.creatinine_result)
                    session.execute(stmt)

                # Commit after processing each row
                session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"database_populator.py: Error adding history: {e}")
        finally:
            session.close()

    def db_has_tables(self):
        """Check if the database contains any tables."""
        session = self.Session()
        try:
            result = session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :db"), {"db": self.db})
            table_count = result.scalar()
            if table_count and table_count > 0:
                logging.info(f"database_populator.py: Database contains {table_count} tables.")
                return True
            else:
                logging.warning("database_populator.py: Database has no tables.")
                return False
        except SQLAlchemyError as e:
            logging.error(f"database_populator.py: Error checking tables: {e}")
            return False
        finally:
            session.close()

    def db_is_populated(self):
        """Check if any table in the database has at least one row."""
        session = self.Session()
        try:
            result = session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = :db"), {"db": self.db})
            tables = [row[0] for row in result]
            if not tables:
                logging.warning("database_populator.py: Database has no tables.")
                return False

            for table in tables:
                count_result = session.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
                row_count = count_result.scalar()
                if row_count and row_count > 0:
                    logging.info(f"database_populator.py: Database is populated (Table `{table}` has {row_count} rows).")
                    return True

            logging.warning("database_populator.py: Database has tables but no data.")
            return False

        except SQLAlchemyError as e:
            logging.error(f"database_populator.py: Error checking if database is populated: {e}")
            return False
        finally:
            session.close()

# Example usage
if __name__ == "__main__":
    db_populator = DatabasePopulator(db="hospital_db", history_file="../data/history.csv", user="root", password="password", host="db", port=3306)
    db_populator.add_history_to_db()
