import json
import database

# Mapping of the final successful run IDs from the SQLite database
run_id_map = {
    'A Family-Friendly Theme Park Resort': 'a66f2d3c-05f1-41b7-a1e8-4798614a4cdb',
    'A Vibrant Tropical Wildlife Zoo': '949fa57e-cf1f-4dcf-8eef-30d375ecf340',
    'A Lush City Botanical Garden': '0964a9ef-038d-4bfe-bde9-8eb4f61050c6',
    'A Prestigious University Campus': '287cb8b8-2e95-40c3-a00e-1e267e948f93',
    'A Historic Downtown Museum District': '3446acba-a487-4770-a003-fdff01421e2d'
}

with open('static/js/cached_runs.js', 'r') as f:
    content = f.read()

content = content.replace('const CACHED_RUNS = ', '').strip()
if content.endswith(';'):
    content = content[:-1]

data = json.loads(content)

for scenario, run_data in data.items():
    run_id = run_id_map.get(scenario)
    if run_id:
        logs = database.get_trace_logs(run_id=run_id)
        if logs:
            run_data['logs'] = logs
            print(f"Added {len(logs)} logs to {scenario}")
        else:
            print(f"Warning: No logs found in DB for {scenario} ({run_id})")
    else:
        print(f"No run_id mapping found for {scenario}")

output = "const CACHED_RUNS = " + json.dumps(data, indent=4) + ";\n"
with open('static/js/cached_runs.js', 'w', encoding='utf-8') as f:
    f.write(output)

print("Logs successfully injected into cache.")