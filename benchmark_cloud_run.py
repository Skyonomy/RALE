import os
import sys
import json
import time
import requests

def run_cloud_test(url, scenario, idx, total):
    print(f"\n🚀 [Run {idx+1}/{total}] Scenario: '{scenario}'")
    api_url = f"{url.rstrip('/')}/api/generate"
    
    payload = {
        "scenarioType": "custom",
        "customScenario": scenario,
        "isStressTest": "false"
    }
    
    start_time = time.time()
    try:
        print(f"  - Dispatching HTTP POST request to Cloud Run: {api_url}")
        # Note: Large timeout since Imagen and self-healing take time
        resp = requests.post(api_url, json=payload, timeout=300)
        duration = round(time.time() - start_time, 2)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                print(f"  ✅ SUCCESS ({duration}s)")
                # If there are items in the logs about repairing or rejected, self-healing triggered
                logs = data.get("audit", {}).get("message", "")
                recovery = "REJECTED" in logs or "repaired" in logs or "REPAIR" in logs
                if recovery:
                    print("    ✨ SELF-HEALING: Cloud Run Auditor detected error and Playwright repaired it.")
                return True, duration, recovery, "Success"
            else:
                print(f"  ❌ FAILED ({duration}s): {data.get('message')}")
                return False, duration, False, data.get("message", "Unknown Error")
        else:
            print(f"  ❌ HTTP ERROR {resp.status_code} ({duration}s)")
            return False, duration, False, f"HTTP {resp.status_code}: {resp.text[:200]}"
            
    except Exception as e:
        print(f"  💥 CONNECTION CRASH: {str(e)}")
        return False, 0, False, str(e)

def main():
    print("="*60)
    print("🧪 RALE ARCHITECT: GOOGLE CLOUD RUN LIVE PERFORMANCE AUDITOR")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\nError: Please provide your live Cloud Run URL as an argument!")
        print("Usage: python3 benchmark_cloud_run.py https://rale-xxxxxx.a.run.app\n")
        return
        
    cloud_url = sys.argv[1]
    print(f"Target Cloud Run Instance: {cloud_url}")
    
    # Standard testing scenarios to verify active generation on Vertex
    scenarios = [
        "A Modern Luxury Ocean Liner Deck",
        "A Large University Sports Complex",
        "A Sustainable Smart-City Residential Zone"
    ]
    
    stats = {
        "total": len(scenarios),
        "passed": 0,
        "failed": 0,
        "repairs": 0,
        "times": [],
        "errors": []
    }
    
    for i, scenario in enumerate(scenarios):
        passed, duration, recovery, error_msg = run_cloud_test(cloud_url, scenario, i, stats["total"])
        if passed:
            stats["passed"] += 1
        else:
            stats["failed"] += 1
            stats["errors"].append(f"{scenario}: {error_msg}")
        
        if recovery:
            stats["repairs"] += 1
            
        if duration > 0:
            stats["times"].append(duration)
            
        # Small cooldown between requests to be safe
        if i < stats["total"] - 1:
            print("  - Cooldown 5s...")
            time.sleep(5)
            
    print("\n" + "="*50)
    print("📊 GOOGLE CLOUD RUN AUDIT SUMMARY")
    print("="*50)
    print(f"Instance URL:   {cloud_url}")
    print(f"Pass Rate:      {stats['passed']}/{stats['total']} ({(stats['passed']/stats['total'])*100:.1f}%)")
    print(f"Self-Heal Runs: {stats['repairs']} (Live Cloud Repairs)")
    if stats['times']:
        avg_time = sum(stats['times']) / len(stats['times'])
        print(f"Avg Latency:    {avg_time:.2f} seconds (Network + Compute)")
    
    if stats["errors"]:
        print("\n❌ Live Failures Encountered:")
        for err in stats["errors"]:
            print(f"  - {err}")
    print("="*50)

if __name__ == "__main__":
    main()
