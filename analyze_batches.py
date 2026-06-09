import datetime

with open('runs_dump.txt', 'r') as f:
    lines = f.readlines()

runs = []
for line in lines:
    parts = line.strip().split('|')
    if len(parts) >= 2:
        ts_str = parts[1].strip()
        try:
            ts = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')
            runs.append((parts[0].strip(), ts))
        except ValueError:
            pass

runs.sort(key=lambda x: x[1])

batches = []
current_batch = [runs[0]]
for i in range(1, len(runs)):
    gap = (runs[i][1] - runs[i-1][1]).total_seconds()
    if gap > 1200: # 20 minutes gap
        batches.append(current_batch)
        current_batch = [runs[i]]
    else:
        current_batch.append(runs[i])
batches.append(current_batch)

for idx, b in enumerate(batches):
    print(f"Batch {idx+1}: {len(b)} runs, from {b[0][1]} to {b[-1][1]}")
