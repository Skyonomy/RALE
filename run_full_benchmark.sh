#!/bin/bash
URL="https://rale.skyonomy.com/"
CONCURRENCY=4

echo "Starting Tier 1: Normal (140px) - 100 runs..."
python3 benchmark_cloud_run.py $URL --mode normal --runs 100 --concurrency $CONCURRENCY

echo "Starting Tier 2: Constrained (200px) - 100 runs..."
python3 benchmark_cloud_run.py $URL --mode constrained --runs 100 --concurrency $CONCURRENCY

echo "Starting Tier 3: Stress (260px) - 100 runs..."
python3 benchmark_cloud_run.py $URL --mode stress --runs 100 --concurrency $CONCURRENCY

echo "All tiers complete."
