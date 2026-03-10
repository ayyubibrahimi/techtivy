import json
import os
import random
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TEST = True

BASE_URL = "https://d2ftw.westus2.cloudapp.azure.com"
INPUT_PATH = Path("../data/input/merged_cases/20260212_case_index_output_all.jsonl")
OUTPUT_PATH_TEST = Path("../data/output/enriched_test.jsonl")
OUTPUT_PATH_FULL = Path("../data/output/enriched_full.jsonl")


def get_token():
    r = requests.post(
        f"{BASE_URL}/o/token/",
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("D2_CLIENT_ID"),
            "client_secret": os.getenv("D2_CLIENT_SECRET"),
        },
    )
    return r.json()["access_token"]


def fetch_provcase_fields(token, prov_id):
    r = requests.get(
        f"{BASE_URL}/d2-api",
        headers={"Authorization": f"Bearer {token}"},
        params={"targetentity": "provcase", "caseids": prov_id},
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    return results[0]


def enrich_record(record, token):
    prov_ids = record.get("provisional_case_resourceids") or []

    all_death_classifications = []
    all_case_numbers = []

    for prov_id in prov_ids:
        prov = fetch_provcase_fields(token, prov_id)
        if prov is None:
            continue

        dc = prov.get("extracted_death_classification")
        if dc is not None:
            all_death_classifications.append(dc)

        case_nums = prov.get("extracted_case_numbers") or []
        all_case_numbers.extend(case_nums)

    all_case_numbers = list(dict.fromkeys(all_case_numbers))

    return {
        **record,
        "extracted_death_classifications": all_death_classifications,
        "extracted_case_numbers": all_case_numbers,
    }


def main():
    token = get_token()

    with INPUT_PATH.open() as f:
        records = [json.loads(line) for line in f]

    if TEST:
        output_path = OUTPUT_PATH_TEST
        records = [random.choice(records)]
        print(f"[TEST] Selected random case: {records[0].get('resourceid')}")
        print(f"[TEST] Provisional case IDs: {records[0].get('provisional_case_resourceids')}")
    else:
        output_path = OUTPUT_PATH_FULL
        print(f"[FULL] Processing {len(records)} cases...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as out:
        for i, record in enumerate(records):
            enriched = enrich_record(record, token)
            out.write(json.dumps(enriched) + "\n")

            if TEST:
                print(f"\nextracted_death_classifications: {enriched['extracted_death_classifications']}")
                print(f"extracted_case_numbers: {enriched['extracted_case_numbers']}")
            else:
                if (i + 1) % 50 == 0:
                    print(f"  {i + 1}/{len(records)} done")

    print(f"\nWritten to {output_path}")


if __name__ == "__main__":
    main()
