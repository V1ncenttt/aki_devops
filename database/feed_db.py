from sqlalchemy import create_engine
import sqlalchemy
import pandas as pd

# Database connection string
DATABASE_URL = "mysql://root:password@0.0.0.0:3306/hospital_db" #Will need to compose that with the secrets to not share the secrets


# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    
    #Load df
    df = pd.read_csv('../data/history.csv')

    # Write a pandas DataFrame to MySQL
    # Add code to feed the database

    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():
        # Insert the row into the database
        mrn = row['mrn']

        query = sqlalchemy.text(f"INSERT INTO Patients (mrn, age, sex) VALUES ({mrn}, NULL, NULL)")

        # Add the patient
        
        conn.execute(query)
        conn.commit()

        #Iterate through the measurements named creatinine_date_x,creatinine_result_x
        max_index = max([int(x.split('_')[2]) for x in row.keys() if 'creatinine_date' in x])
        query = ""
        
        for i in range(1, max_index+1):
            date = row[f'creatinine_date_{i}']
            result = row[f'creatinine_result_{i}']
            if not date is None and not result is None and not pd.isna(date) and not pd.isna(result):
                
                query = f"INSERT INTO Measurements (mrn, measurement_date, measurement_value) VALUES ({mrn}, '{date}', {result})" # might need to make sure that the date is in the correct format
                conn.execute(sqlalchemy.text(query))
                conn.commit()
