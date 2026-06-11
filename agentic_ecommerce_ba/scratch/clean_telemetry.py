import os
import csv
import json

telemetry_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "telemetry")

def clean_csv(filename):
    filepath = os.path.join(telemetry_dir, filename)
    if not os.path.exists(filepath): return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = [row for row in reader if "TestCaseAgent" not in row]
        
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Cleaned {filename}")

def clean_jsonl(filename):
    filepath = os.path.join(telemetry_dir, filename)
    if not os.path.exists(filepath): return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    clean_lines = []
    for line in lines:
        try:
            data = json.loads(line)
            if data.get("agent_name") != "TestCaseAgent":
                clean_lines.append(line)
        except:
            clean_lines.append(line)
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(clean_lines)
    print(f"Cleaned {filename}")

try:
    clean_csv("eval_agent_runs.csv")
    clean_jsonl("eval_agent_runs.jsonl")
    print("Local telemetry cleaned successfully.")
except Exception as e:
    print(f"Error: {e}")
