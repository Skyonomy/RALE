#!/bin/bash
URL="https://rale-service-128635617414.us-central1.run.app"

echo "Starting Tier 2: Robustness (200px) - Target 100 Total..."
python3 -u final_benchmark.py $URL --mode constrained --target 100

echo "Starting Tier 3: Failure Boundary (260px) - Target 100 Total..."
python3 -u final_benchmark.py $URL --mode stress --target 100

echo "All tiers complete. Clean data ready for submission."
