import pandas as pd

# Load the original data
df = pd.read_csv("data/history.csv")

# Create Patients DataFrame
patients_df = pd.DataFrame({
    "mrn": df["mrn"],
    "age": None,  # Placeholder
    "sex": None   # Placeholder
})

# Save Patients DataFrame
patients_df.to_csv("data/patients.csv", index=False)

# Reshape Measurements DataFrame
measurements = []
for index, row in df.iterrows():
    mrn = row["mrn"]
    for i in range(26):  # Adjust this if the number of measurement columns changes
        date_col = f"creatinine_date_{i}"
        result_col = f"creatinine_result_{i}"

        # Ensure the columns exist and have valid data
        if date_col in row and result_col in row and pd.notna(row[date_col]) and pd.notna(row[result_col]):
            measurements.append([mrn, row[date_col], row[result_col]])

# Convert to DataFrame
measurements_df = pd.DataFrame(measurements, columns=["mrn", "measurement_date", "measurement_value"])

# Save Measurements DataFrame
measurements_df.to_csv("data/measurements.csv", index=False)

print("CSV files created successfully: patients.csv and measurements.csv")
