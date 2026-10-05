#!/bin/bash
# Run every comparison in the order used for the course. About 50 minutes, about 5 US dollars.
# Author: Roni Das. Created: 2026-10-04.
set -e
cd "$(dirname "$0")/.."
python compare/run_compare.py --task tickets --protocol accuracy
python compare/run_compare.py --task pairs   --protocol accuracy
python compare/run_compare.py --task tickets --protocol latency  --sample 40 --rounds 3
python compare/run_compare.py --task pairs   --protocol latency  --sample 40 --rounds 3
python compare/run_compare.py --task tickets --protocol batching --sample 30
python compare/run_compare.py --task pairs   --protocol batching --sample 30
python data/make_companies.py --seed 20261007 --out companies-fresh
python capstone/step1_block.py --data companies-fresh
python compare/run_compare.py --task pairs-v1-fresh --protocol accuracy
python compare/run_compare.py --task pairs-v2-fresh --protocol accuracy
python compare/summarize.py
echo "ALL COMPARISONS DONE"
