"""Make messy synthetic company records from three systems, with the truth kept apart.

A company buys from us. Sales types it into the CRM. Finance types it into
billing. Support types it into the help desk. Three people, three spellings.
This script invents those companies and their records, with the mess real
data has: legal suffixes added or dropped, short forms, typos, capital
letters, old city names, moved offices, phone numbers written five ways,
missing websites and different contact people.

It also adds the cases that trick simple matching:
  - namesakes: two different companies with the same name in different cities
  - subsidiaries: "X Logistics" and "X Logistics UK" are related, not the same
  - siblings: "Cedar Foods" and "Cedar Analytics" share a word, nothing else

The records go to records.jsonl. Which record belongs to which real company
goes to truth.json, which the model never sees.

    python data/make_companies.py
    python data/make_companies.py --seed 20261007 --out companies-fresh   # a fresh test set

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import json
import random
import re
from pathlib import Path

SEED = 20261006
OUT_DIR = Path(__file__).with_name("companies")

FIRST = ["Blue Harbor", "Saffron Peak", "Northwind", "Silver Oak", "Red Kite", "Granite Hill",
         "Lotus Field", "Bright Path", "Cedar", "Monsoon", "Iron Bridge", "Coral Bay", "Summit Ridge",
         "Evergreen", "Falcon", "Riverbend", "Starling", "Tidewater", "Amberline", "Orchid",
         "Pinnacle", "Crescent", "Kestrel", "Maple Line", "Sandstone", "Juniper", "Indigo",
         "Westbrook", "Peregrine", "Halcyon"]
CORE = ["Logistics", "Foods", "Software", "Textiles", "Pharma", "Engineering", "Solar",
        "Analytics", "Hospitality", "Motors", "Packaging", "Health", "Finance", "Robotics",
        "Ceramics"]
SHORT = {"Engineering": "Engg", "Pharma": "Pharmaceuticals", "Logistics": "Logistic",
         "Hospitality": "Hosp.", "Analytics": "Analytic", "Packaging": "Pkg", "Software": "Soft"}

COUNTRIES = {
    "IN": {"suffix": ["Private Limited", "Pvt Ltd", "Pvt. Ltd.", ""], "tld": ".in", "code": "+91",
           "cities": {"Mumbai": "Bombay", "Bengaluru": "Bangalore", "Gurugram": "Gurgaon",
                      "Kolkata": "Calcutta", "Chennai": "Madras", "Pune": "Pune"}},
    "GB": {"suffix": ["Ltd", "Limited", "Ltd.", ""], "tld": ".co.uk", "code": "+44",
           "cities": {"London": "London", "Leeds": "Leeds", "Manchester": "Manchester"}},
    "US": {"suffix": ["Inc.", "Inc", "Incorporated", ""], "tld": ".com", "code": "+1",
           "cities": {"Austin": "Austin", "Boston": "Boston", "Chicago": "Chicago"}},
    "DE": {"suffix": ["GmbH", "GmbH", ""], "tld": ".de", "code": "+49",
           "cities": {"Munich": "München", "Berlin": "Berlin", "Hamburg": "Hamburg"}},
}
STREETS = ["Station", "Park", "Mill", "Church", "Lake", "Market", "Hill", "Harbour", "MG", "Ring"]
STREET_TYPES = {"Road": "Rd", "Street": "St.", "Avenue": "Ave", "Lane": "Ln"}
GIVEN = ["Priya", "Rahul", "Anita", "Tom", "Sarah", "Lukas", "Mei", "Omar", "Grace", "Arjun",
         "Hannah", "Diego", "Fatima", "Ken", "Leila", "Sven", "Ngozi", "Ravi", "Emma", "Yusuf"]
FAMILY = ["Sharma", "Iyer", "Brooks", "Müller", "Chen", "Haddad", "Okafor", "Patel", "Novak",
          "Silva", "Khan", "Fischer", "Das", "Walsh", "Mehta", "Rossi", "Kowalski", "Ito"]
ROLES = ["Finance manager", "Head of IT", "Procurement lead", "Office manager", "CTO", "Buyer"]
SOURCES = ["crm", "billing", "support"]


def slug(text: str) -> str:
    """Lowercase letters and digits only, for web domains."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def make_company(eid: str, name: str, rng: random.Random, country: str | None = None,
                 city: str | None = None) -> dict[str, object]:
    """One real company, as it exists in the world. This is the truth."""
    country = country or rng.choice(list(COUNTRIES))
    info = COUNTRIES[country]
    city = city or rng.choice(list(info["cities"]))
    people = [{"name": f"{rng.choice(GIVEN)} {rng.choice(FAMILY)}", "role": rng.choice(ROLES)}
              for _ in range(rng.randint(1, 3))]
    return {
        "entity_id": eid, "name": name, "suffix": rng.choice([s for s in info["suffix"] if s]),
        "country": country, "city": city,
        "street": f"{rng.randint(2, 240)} {rng.choice(STREETS)} {rng.choice(list(STREET_TYPES))}",
        "postcode": str(rng.randint(10000, 99999)),
        "phone": f"{info['code']} {rng.randint(20, 99)} {rng.randint(1000, 9999)} "
                 f"{rng.randint(1000, 9999)}",
        "domain": slug(name) + info["tld"], "people": people,
    }


def messy_name(c: dict[str, object], rng: random.Random, mess: float) -> tuple[str, list[str]]:
    """Write the company name the way a busy person might type it."""
    notes: list[str] = []
    name = str(c["name"])
    if rng.random() < mess * 0.5:
        for long, short in SHORT.items():
            if long in name:
                name = name.replace(long, short)
                notes.append("short_form")
    suffix = rng.choice(COUNTRIES[str(c["country"])]["suffix"]) if rng.random() < mess else c["suffix"]
    if suffix != c["suffix"]:
        notes.append("suffix_changed")
    full = f"{name} {suffix}".strip()
    if c["country"] == "IN" and rng.random() < mess * 0.3:
        full, _ = "M/s. " + full, notes.append("ms_prefix")
    if rng.random() < mess * 0.3:
        full, _ = full.upper(), notes.append("uppercase")
    if rng.random() < mess * 0.35:
        words = full.split(" ")
        i = rng.randrange(len(words))
        w = words[i]
        if len(w) > 4:
            j = rng.randint(1, len(w) - 3)
            words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
            full, _ = " ".join(words), notes.append("typo")
    return full, notes


def messy_record(c: dict[str, object], source: str, rid: str,
                 rng: random.Random) -> dict[str, object]:
    """One record of company `c` as it was typed into one system."""
    mess = {"crm": 0.35, "billing": 0.6, "support": 0.8}[source]
    name, notes = messy_name(c, rng, mess)
    info = COUNTRIES[str(c["country"])]
    city = str(c["city"])
    if rng.random() < mess * 0.4 and info["cities"][city] != city:
        city, _ = info["cities"][city], notes.append("old_city_name")
    street = str(c["street"])
    if rng.random() < mess * 0.5:
        for long, short in STREET_TYPES.items():
            street = street.replace(long, short)
    if source == "billing" and rng.random() < 0.12:
        street = f"{rng.randint(2, 240)} {rng.choice(STREETS)} Road"
        notes.append("moved_office")
    if rng.random() < mess * 0.3:
        street = f"{rng.choice(['2nd Floor', 'Unit 4', 'Suite 210', 'Block B'])}, {street}"
    digits = re.sub(r"\D", "", str(c["phone"]))
    phone_forms = [str(c["phone"]), "+" + digits, digits[-10:], f"({digits[-10:-7]}) {digits[-7:]}"]
    phone: str | None = rng.choice(phone_forms)
    if rng.random() < mess * 0.25:
        phone, _ = None, notes.append("no_phone")
    elif rng.random() < 0.1:
        phone, _ = f"{info['code']} {rng.randint(20, 99)} {rng.randint(1000, 9999)} 0000", \
            notes.append("other_phone_line")
    domain = str(c["domain"])
    website: str | None = rng.choice([domain, "www." + domain, "https://www." + domain])
    if rng.random() < mess * 0.4:
        website, _ = None, notes.append("no_website")
    person = rng.choice(c["people"])  # type: ignore[arg-type]
    email_domain = domain if rng.random() > 0.15 else "gmail.com"
    email = f"{person['name'].split()[0].lower()}.{slug(person['name'].split()[1])}@{email_domain}"
    return {
        "record_id": rid, "source": source, "name": name,
        "address": f"{street}, {city}" + (f" {c['postcode']}" if rng.random() > mess * 0.4 else ""),
        "country": c["country"], "phone": phone, "website": website,
        "contact": {"name": person["name"], "role": person["role"], "email": email},
        "_notes": notes,
    }


def build(count: int, rng: random.Random) -> tuple[list[dict], dict[str, object]]:
    """Make the companies, then their records. Returns (records, truth)."""
    names = rng.sample([f"{f} {c}" for f in FIRST for c in CORE], count)
    companies = [make_company(f"E{i + 1:04d}", n, rng) for i, n in enumerate(names)]
    related: list[dict[str, str]] = []
    for parent in rng.sample(companies[:count], count // 10):
        child_country = rng.choice([k for k in COUNTRIES if k != parent["country"]])
        tag = {"IN": "India", "GB": "UK", "US": "USA", "DE": "Deutschland"}[child_country]
        child = make_company(f"E{len(companies) + 1:04d}", f"{parent['name']} {tag}", rng,
                             country=child_country)
        child["domain"] = str(parent["domain"]).split(".")[0] + COUNTRIES[child_country]["tld"]
        companies.append(child)
        related.append({"a": str(parent["entity_id"]), "b": str(child["entity_id"]),
                        "kind": "subsidiary"})
    for twin in rng.sample(companies[:count], count // 12):
        other_cities = [k for k in COUNTRIES if k != twin["country"]]
        namesake = make_company(f"E{len(companies) + 1:04d}", str(twin["name"]), rng,
                                country=rng.choice(other_cities))
        namesake["domain"] = slug(str(twin["name"])) + "-" + slug(str(namesake["city"])) + \
            COUNTRIES[str(namesake["country"])]["tld"]
        companies.append(namesake)
        related.append({"a": str(twin["entity_id"]), "b": str(namesake["entity_id"]),
                        "kind": "namesake"})
    records: list[dict] = []
    owner: dict[str, str] = {}
    for c in companies:
        present = [s for s, p in zip(SOURCES, (0.85, 0.7, 0.5), strict=True) if rng.random() < p]
        for source in present or [rng.choice(SOURCES)]:
            rid = f"{source[:3].upper()}-{len(records) + 1:05d}"
            records.append(messy_record(c, source, rid, rng))
            owner[rid] = str(c["entity_id"])
    rng.shuffle(records)
    truth = {"record_to_entity": owner, "entities": companies, "related_pairs": related}
    return records, truth


def main() -> None:
    """Write records.jsonl and truth.json."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--companies", type=int, default=300)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", default="companies", help="folder name inside data/")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    records, truth = build(args.companies, rng)
    out_dir = OUT_DIR.with_name(args.out)
    out_dir.mkdir(exist_ok=True)
    clean = [{k: v for k, v in r.items() if k != "_notes"} for r in records]
    (out_dir / "records.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in clean))
    truth["record_notes"] = {r["record_id"]: r["_notes"] for r in records}
    (out_dir / "truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=1))
    entities = len(truth["entities"])  # type: ignore[arg-type]
    kinds = [p["kind"] for p in truth["related_pairs"]]  # type: ignore[union-attr]
    print(f"wrote {len(records)} records for {entities} real companies (seed {args.seed})")
    print(f"tricky look-alikes: {kinds.count('subsidiary')} subsidiaries, "
          f"{kinds.count('namesake')} namesakes")


if __name__ == "__main__":
    main()
