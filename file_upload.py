## checks if the script is run with the correct number of arguments
import sys
import os
import chardet
import pandas as pd


if len(sys.argv) != 2:
    print("Usage: uv run autolysis.py <dataset.csv>")
    sys.exit(1)

## checks if csv file exists in current directory of the script
file_name = sys.argv[1]
csv_file = os.path.join("data", file_name)

if not os.path.exists(csv_file):
    print(f"Error: File {csv_file} not found.")
    sys.exit(1)

# Load the dataset
try:
    with open(csv_file, "rb") as f:
        encoding_result = chardet.detect(f.read())
        df = pd.read_csv(
            csv_file, encoding=encoding_result["encoding"]
        )  ## dataset loaded into dataframe

    print(f"Dataset loaded successfully: {csv_file}")
except Exception as e:
    print(f"Error loading dataset: {e}")
    sys.exit(1)
