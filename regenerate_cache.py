import json
from app import create_app

app = create_app()
app.testing = True
client = app.test_client()

scenarios = [
    "A Family-Friendly Theme Park Resort",
    "A Vibrant Tropical Wildlife Zoo",
    "A Lush City Botanical Garden",
    "A Prestigious University Campus",
    "A Historic Downtown Museum District"
]

cached_runs = {}

print("Starting cache regeneration...")

with app.app_context():
    for scenario in scenarios:
        print(f"Generating for {scenario}...")
        res = client.post('/api/generate', json={
            "scenario": scenario,
            "stress_test": False
        })
        if res.status_code == 200:
            cached_runs[scenario] = res.get_json()
            print(f"Success for {scenario}")
        else:
            print(f"Failed for {scenario}: {res.status_code}")
            print(res.text)

print("Writing to static/js/cached_runs.js...")
output = "const CACHED_RUNS = " + json.dumps(cached_runs, indent=4) + ";\n"
with open('static/js/cached_runs.js', 'w', encoding='utf-8') as f:
    f.write(output)

print("Cache regeneration complete.")
