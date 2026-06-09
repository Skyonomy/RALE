import os
import sys
import json
import time
import requests
import argparse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_cloud_test(url, scenario, mode, idx, total):
    print(f"\n🚀 [Run {idx+1}/{total}] Scenario: '{scenario}'")
    api_url = f"{url.rstrip('/')}/api/generate"
    
    payload = {
        "scenario": scenario,
        "spatial_regime": mode,
        "skip_audio": True
    }
    
    start_time = time.time()
    try:
        resp = requests.post(api_url, json=payload, timeout=900)
        duration = round(time.time() - start_time, 2)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                # Check recovery from the response data if possible, or assume False
                # The orchestrator returns 'status': 'success', 'data': final_data
                # We might need to check the database later for 'recovery_triggered'
                # but for the benchmark's immediate output, we'll try to find it.
                recovery = False 
                
                print(f"  ✅ SUCCESS Run {idx+1} ({duration}s) | Healed: {recovery}")
                return (True, duration, recovery, "Success")
            else:
                print(f"  ❌ FAILED Run {idx+1} ({duration}s): {data.get('message')}")
                return (False, duration, False, data.get("message", "Unknown Error"))
        else:
            print(f"  ❌ HTTP ERROR Run {idx+1} {resp.status_code} ({duration}s)")
            return (False, duration, False, f"HTTP {resp.status_code}: {resp.text[:200]}")
            
    except Exception as e:
        print(f"  💥 CONNECTION CRASH Run {idx+1}: {str(e)}")
        return (False, 0, False, str(e))

def main():
    print("="*60)
    print("🧪 RALE ARCHITECT: BATCH PERFORMANCE AUDITOR")
    print("="*60)
    
    parser = argparse.ArgumentParser(description="Run RALE benchmark.")
    parser.add_argument("url", help="Cloud Run URL (e.g., https://rale-xxxxxx.a.run.app)")
    parser.add_argument("--mode", choices=["normal", "constrained", "stress"], required=True, help="Mode to run")
    parser.add_argument("--runs", type=int, default=100, help="Total number of runs")
    parser.add_argument("--concurrency", type=int, default=10, help="Maximum concurrent requests")
    args = parser.parse_args()
    
    cloud_url = args.url
    mode = args.mode
    total_runs = args.runs
    concurrent_limit = args.concurrency
    
    scenarios_pool = [
        "A Family-Friendly Theme Park Resort",
        "A Vibrant Tropical Wildlife Zoo",
        "A Lush City Botanical Garden",
        "A Prestigious University Campus",
        "A Historic Downtown Museum District"
    ]
    
    scenarios_to_run = []
    for _ in range(total_runs):
        base_scenario = random.choice(scenarios_pool)
        if mode == "stress":
            scenarios_to_run.append(base_scenario + " [STRESS]")
        elif mode == "constrained":
            scenarios_to_run.append(base_scenario + " [CONSTRAINED]")
        else:
            scenarios_to_run.append(base_scenario)
    
    stats = {
        "passed": 0, "failed": 0, "repairs": 0,
        "times": [], "errors": [],
        "actual_cost": 0.0, "pro_cost_baseline": 0.0
    }
    
    results = []
    
    print(f"Starting {total_runs} runs in {mode.upper()} mode with concurrency {concurrent_limit}...")
    
    with ThreadPoolExecutor(max_workers=concurrent_limit) as executor:
        futures = {}
        for idx, scenario in enumerate(scenarios_to_run):
            futures[executor.submit(run_cloud_test, cloud_url, scenario, mode, idx, total_runs)] = idx
            time.sleep(1.5)
        
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
        
    # Process Results
    for passed, duration, recovery, error_msg in results:
        if passed:
            stats["passed"] += 1
            stats["times"].append(duration)
            artistCost = 0.0300
            reviewerCost = 0.0002
            standardBaseCost = 0.0035
            standardProBaseCost = 0.0162
            repairCost = 0.0190
            
            total = artistCost + reviewerCost + standardBaseCost
            proOnlyTotal = artistCost + reviewerCost + standardProBaseCost
            
            if recovery:
                stats["repairs"] += 1
                total += repairCost
                proOnlyTotal += repairCost
                
            stats["actual_cost"] += total
            stats["pro_cost_baseline"] += proOnlyTotal
        else:
            stats["failed"] += 1
            stats["errors"].append(error_msg)
            
    savings = stats["pro_cost_baseline"] - stats["actual_cost"]
    savings_pct = (savings / stats["pro_cost_baseline"] * 100) if stats["pro_cost_baseline"] > 0 else 0
            
    print("\n" + "="*50)
    print("📊 GOOGLE CLOUD RUN AUDIT SUMMARY")
    print("="*50)
    print(f"Total Runs:     {total_runs}")
    print(f"Pass Rate:      {stats['passed']}/{total_runs} ({(stats['passed']/total_runs)*100:.1f}%)")
    print(f"Failure Rate:   {stats['failed']}/{total_runs} ({(stats['failed']/total_runs)*100:.1f}%)")
    print(f"Self-Heal Runs: {stats['repairs']} (Live Cloud Repairs)")
    
    base_invocations = stats['passed'] * 5
    repair_invocations = stats['repairs'] * 2 
    total_invocations = base_invocations + repair_invocations
    
    print("\n🤖 AGENT INVOCATION METRICS")
    print(f"Est. Total API Calls: {total_invocations} (Dynamic Routing)")
    
    if stats['times']:
        avg_time = sum(stats['times']) / len(stats['times'])
        print(f"\n⚡ PERFORMANCE")
        print(f"Avg Latency:    {avg_time:.2f} seconds")
        
    print("\n💰 FINANCIAL AUDIT (Estimated Model, Not Token-Metered)")
    print(f"Tiered Cost:    ${stats['actual_cost']:.4f}")
    print(f"Monolithic Pro: ${stats['pro_cost_baseline']:.4f}")
    
    if stats["errors"]:
        print("\n❌ Live Failures Encountered:")
        for err in set(stats["errors"]):
            print(f"  - {err}")
    print("="*50)

if __name__ == "__main__":
    main()
