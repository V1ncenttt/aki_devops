from sqlalchemy import create_engine
import pandas as pd

# Database connection string
DATABASE_URL = "mysql://user:password@mysql_container:3306/hospital_db" #Will need to compose that with the secrets to not share the secrets


# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

#Load df
df = pd.read_csv('data/history.csv')

# Write a pandas DataFrame to MySQL
# Add code to feed the database

# Iterate over the rows of the DataFrame
for index, row in df.iterrows():
    # Insert the row into the database
    mrn = row['mrn']
    age = row['age']
    query = f"INSERT INTO patients (mrn, age) VALUES ({mrn}, {age})"

    # Add the patient
    engine.execute(query)

    #Iterate through the measurements named creatinine_date_x,creatinine_result_x
    max_index = max([int(x.split('_')[2]) for x in row.keys() if 'creatinine_date' in x])

    for i in range(1, max_index+1):
        date = row[f'creatinine_date_{i}']
        result = row[f'creatinine_result_{i}']
        query += f"; INSERT INTO measurements (mrn, test_date, result) VALUES ({mrn}, '{date}', {result})" # might need to make sure that the date is in the correct format
        engine.execute(query)
    
