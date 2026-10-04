"""Step 1: cheap blocking. Find the pairs of records worth asking about.

730 records make 266,085 possible pairs. Asking a model about every pair
would be slow and silly, because almost all of them are obviously different.
So first a cheap rule with no AI keeps only pairs that look a little alike:

  - the cleaned names share enough three-letter pieces (trigrams), or
  - the phone numbers end with the same 7 digits, or
  - the websites (or email domains) are the same.

Then we check, using the truth file, how many real duplicates survived.
That number is the blocking recall: a duplicate dropped here can never be
found later, whatever model you use.

    python capstone/step1_block.py
    python capstone/step1_block.py --data companies-fresh

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAME_SIMILARITY_CUTOFF = 0.50
LEGAL_WORDS = {"private", "limited", "pvt", "ltd", "inc", "incorporated", "gmbh", "m/s", "the"}
FREE_MAIL = {"gmail.com"}


def clean_name(name: str) -> str:
    """Lowercase, drop punctuation and legal words like Ltd or GmbH."""
    words = re.sub(r"[^a-z0-9/ ]", " ", name.lower()).split()
    return " ".join(w for w in words if w not in LEGAL_WORDS)


def trigrams(text: str) -> set[str]:
    """All three-letter pieces of the text, with spaces as padding."""
    padded = f"  {text} "
    return {padded[i:i + 3] for i in range(len(padded) - 2)}


def similarity(a: set[str], b: set[str]) -> float:
    """Jaccard similarity: shared pieces divided by all pieces. 1.0 means identical."""
    return len(a & b) / len(a | b) if a | b else 0.0


def web_domain(record: dict) -> str | None:
    """The company's own web domain, from its website or its contact's email."""
    if record.get("website"):
        return re.sub(r"^(https?://)?(www\.)?", "", record["website"])
    email_domain = record["contact"]["email"].split("@")[1]
    return None if email_domain in FREE_MAIL else email_domain


def pair_kind(entity_a: str, entity_b: str, look_alikes: dict[tuple[str, str], str]) -> str:
    """Label a pair for the report: same, subsidiary, namesake or different."""
    if entity_a == entity_b:
        return "same"
    return look_alikes.get((entity_a, entity_b), "different")


def main() -> None:
    """Write the candidate pairs and report how many true duplicates they keep."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default="companies", help="folder inside data/")
    args = parser.parse_args()
    records_file = ROOT / "data" / args.data / "records.jsonl"
    truth_file = ROOT / "data" / args.data / "truth.json"
    suffix = "" if args.data == "companies" else "-" + args.data.removeprefix("companies-")
    out = ROOT / f"capstone/out/candidate_pairs{suffix}.jsonl"
    records = [json.loads(line) for line in records_file.read_text().splitlines()]
    truth = json.loads(truth_file.read_text())
    owner = truth["record_to_entity"]
    look_alikes = {}
    for rel in truth["related_pairs"]:
        look_alikes[(rel["a"], rel["b"])] = look_alikes[(rel["b"], rel["a"])] = rel["kind"]
    grams = {r["record_id"]: trigrams(clean_name(r["name"])) for r in records}
    pairs = []
    for a, b in itertools.combinations(records, 2):
        sim = similarity(grams[a["record_id"]], grams[b["record_id"]])
        same_phone = bool(a["phone"] and b["phone"]) and \
            re.sub(r"\D", "", a["phone"])[-7:] == re.sub(r"\D", "", b["phone"])[-7:]
        same_domain = web_domain(a) is not None and web_domain(a) == web_domain(b)
        if sim >= NAME_SIMILARITY_CUTOFF or same_phone or same_domain:
            pairs.append({"pair_id": f"P{len(pairs) + 1:05d}", "a": a, "b": b,
                          "name_similarity": round(sim, 3),
                          "same_entity": owner[a["record_id"]] == owner[b["record_id"]],
                          "kind": pair_kind(owner[a["record_id"]], owner[b["record_id"]],
                                            look_alikes)})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pairs))

    all_pairs = len(records) * (len(records) - 1) // 2
    true_dupes = sum(1 for a, b in itertools.combinations(records, 2)
                     if owner[a["record_id"]] == owner[b["record_id"]])
    kept_dupes = sum(p["same_entity"] for p in pairs)
    print(f"records: {len(records)}   all possible pairs: {all_pairs:,}")
    print(f"candidate pairs after blocking: {len(pairs):,} "
          f"({len(pairs) / all_pairs:.2%} of all pairs)")
    print(f"true duplicate pairs in the data: {true_dupes}")
    print(f"true duplicates kept by blocking: {kept_dupes} "
          f"(blocking recall {kept_dupes / true_dupes:.1%})")
    print(f"pairs that are NOT duplicates: {len(pairs) - kept_dupes:,}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
