import pandas as pd

# Path to your parquet file
input_path = "c:/ropax.parquet"

# Path to save the CSV output
output_path = "C:/Users/sandipkumar.pal/OneDrive - S&P Global/Office/bulk_emission_2024.csv"

# Read the parquet file
df = pd.read_parquet(input_path,engine='pyarrow')

# Save as CSV (without index)
df.to_csv(output_path, index=False)

print(f"✅ Successfully converted '{input_path}' to '{output_path}'")
