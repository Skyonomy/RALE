import json
import requests
import time
import concurrent.futures

BASE_URL = "https://rale-service-128635617414.us-central1.run.app"

target_outcomes = {
    "A Family-Friendly Theme Park Resort": ("repair", "stress"),
    "A Vibrant Tropical Wildlife Zoo": ("clean", "normal"),
    "A Lush City Botanical Garden": ("repair", "stress"),
    "A Prestigious University Campus": ("repair", "stress"),
    "A Historic Downtown Museum District": ("repair", "stress")
}

with open('static/js/cached_runs.js', 'r') as f:
    content = f.read()

content = content.replace('const CACHED_RUNS = ', '').strip()
if content.endswith(';'):
    content = content[:-1]

cached_runs = json.loads(content)

print("Starting targeted remote cache regeneration...")

def process_scenario(scenario, target, regime):
    print(f"Generating for {scenario} (Target: {target}, Regime: {regime})...")
    while True:
        try:
            res = requests.post(f'{BASE_URL}/api/generate', json={
                "scenario": scenario,
                "spatial_regime": regime,
                "skip_audio": False
            }, timeout=600)
            
            if res.status_code == 200:
                data = res.json()
                recovered = data.get("audit", {}).get("recovery_triggered", False)
                if target == "clean" and recovered:
                    print(f"[{scenario}] Got a repair, but wanted clean. Retrying...")
                    time.sleep(2)
                    continue
                if target == "repair" and not recovered:
                    print(f"[{scenario}] Got a clean run, but wanted repair. Retrying...")
                    time.sleep(2)
                    continue
                
                # Fetch full logs
                run_id = data.get('run_id')
                logs_res = requests.get(f'{BASE_URL}/api/trace?run_id={run_id}', timeout=30)
                logs = logs_res.json().get('logs', [])
                data['logs'] = logs
                
                print(f"Success for {scenario}! (Recovered: {recovered})")
                return scenario, data
            else:
                print(f"[{scenario}] Failed: {res.status_code}. Retrying...")
                time.sleep(2)
        except Exception as e:
            print(f"[{scenario}] Error: {e}. Retrying...")
            time.sleep(2)

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_scenario, scenario, target, regime) for scenario, (target, regime) in target_outcomes.items()]
    for future in concurrent.futures.as_completed(futures):
        scenario, data = future.result()
        cached_runs[scenario] = data
        
        # Write incrementally
        output = "const CACHED_RUNS = " + json.dumps(cached_runs, indent=4) + ";\n"
        with open('static/js/cached_runs.js', 'w', encoding='utf-8') as f:
            f.write(output)

print("Cache regeneration complete.")
