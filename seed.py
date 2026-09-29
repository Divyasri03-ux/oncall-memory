"""
Seed script for Northwind Pay OnCall Memory.
Populates Hindsight memory bank with 25 realistic production incidents,
including root causes, error logs, remediation steps, and failed attempts.
"""

import sys
import logging
from backend.sample_data import SEED_INCIDENTS
from backend.memory_client import memory_manager
from backend.config import HINDSIGHT_BANK_ID, HINDSIGHT_BASE_URL, is_hindsight_configured

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

def run_seed():
    print("=" * 70)
    print(" Northwind Pay: Seeding OnCall Memory Bank into Hindsight")
    print("=" * 70)
    print(f"Target Bank ID:      {HINDSIGHT_BANK_ID}")
    print(f"Hindsight Endpoint:  {HINDSIGHT_BASE_URL}")
    print(f"Configured Credentials: {is_hindsight_configured()}")
    print(f"Incidents to seed:   {len(SEED_INCIDENTS)}")
    print("-" * 70)

    success_count = 0
    failed_attempts = 0

    for idx, inc in enumerate(SEED_INCIDENTS, start=1):
        status_badge = "SUCCESS" if inc['fix_status'] == "SUCCESS" else "FAILED REMEDIATION"
        print(f"[{idx:02d}/25] Retaining {inc['id']} ({inc['service']}) - [{status_badge}]...")
        print(f"       Title: {inc['title']}")
        print(f"       Engineer: {inc['who_fixed_it']} | MTTR: {inc['time_to_resolve']}")
        
        if inc['fix_status'] == "FAILED":
            failed_attempts += 1

        result = memory_manager.retain_incident(inc)
        if result.get("status") == "success":
            success_count += 1
        else:
            print(f"       Warning: {result}")

    print("-" * 70)
    stats = memory_manager.get_memory_stats()
    print(f"Seeding Complete!")
    print(f"Total Retained Incidents:  {success_count} / {len(SEED_INCIDENTS)}")
    print(f"Failed Fix Traps Retained: {failed_attempts} (to train agent against bad fixes)")
    print(f"Current Bank Memory Count: {stats['total_memories']}")
    print(f"Active Storage Mode:       {stats['mode']}")
    print("=" * 70)

if __name__ == "__main__":
    run_seed()
