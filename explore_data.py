import json
import csv
import os

# Helper to print a summary for JSON files
def summarize_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\nFile: {os.path.basename(path)}")
    print(f"Type: {type(data).__name__}")
    if isinstance(data, list):
        print(f"Records: {len(data)}")
        print("Sample:", data[0] if data else 'Empty')
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())[:5]}")
        print("Sample:", {k: data[k] for k in list(data)[:1]})
    else:
        print("Unknown JSON structure.")

# Helper to print a summary for CSV files
def summarize_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    print(f"\nFile: {os.path.basename(path)}")
    print(f"Rows: {len(rows)-1 if len(rows)>1 else 0}")
    print(f"Columns: {rows[0] if rows else 'Empty'}")
    print(f"Sample: {rows[1] if len(rows)>1 else 'No data'}")

if __name__ == "__main__":
    # Summarize JSON files
    for json_file in ["stations.json", "trains.json", "schedules.json"]:
        if os.path.exists(json_file):
            summarize_json(json_file)
        else:
            print(f"{json_file} not found.")
    # Summarize CSV file
    csv_file = "Train_details_22122017.csv"
    if os.path.exists(csv_file):
        summarize_csv(csv_file)
    else:
        print(f"{csv_file} not found.")
