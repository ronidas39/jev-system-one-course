"""The two tasks we compare: ticket triage and the duplicate-record check.

For each task this file holds three things, so both models get exactly the
same job:
  - the Jev questions (Choice, Score, Noul),
  - the same questions written as instructions plus a strict JSON schema
    for an OpenAI model,
  - a function that turns either model's answer into the same plain form,
    so the scoring code never has to know which model answered.

Author: Roni Das
Created: 2026-10-04
"""

import json
import re
from typing import Any

from typesafe_sdk import Choice, Noul, Score

# ---------------------------------------------------------------- ticket triage

TEAMS = {
    "billing": "Charges, refunds, invoices, prices on a bill, subscriptions, billing details",
    "technical": "Bugs, errors, crashes, outages, slow pages, API or integration problems",
    "shipping": "Delivery, tracking, couriers, damaged or lost parcels, delivery addresses",
    "account": "Login, passwords, security, profile, users and permissions, data deletion",
    "sales": "Buying, plans, quotes, discounts, demos, trials for new or bigger purchases",
}
URGENCY_LEVELS = [
    "Can wait: no harm if answered in a few days",
    "Soon: should be handled within a day or two",
    "Today: work, money or security is blocked right now",
]
FRUSTRATION_LEVELS = [
    "Calm, just stating facts",
    "Frustrated but civil",
    "Very angry, insulting, or threatening to leave or complain",
]

TICKET_QUESTIONS = {
    "team": Choice(instructions="Which team should handle this support ticket?", criteria=TEAMS),
    "urgency": Score(instructions="How soon does this ticket need a response?",
                     criteria=URGENCY_LEVELS),
    "frustration": Score(instructions="How frustrated does the customer appear?",
                         criteria=FRUSTRATION_LEVELS),
}

TICKET_SYSTEM_PROMPT = (
    "You classify customer support tickets. Answer with JSON only.\n"
    "team: which team should handle this support ticket? Options: "
    + "; ".join(f"{k} = {v}" for k, v in TEAMS.items())
    + "\nurgency: how soon does this ticket need a response? "
    + "; ".join(f"{i} = {v}" for i, v in enumerate(URGENCY_LEVELS))
    + "\nfrustration: how frustrated does the customer appear? "
    + "; ".join(f"{i} = {v}" for i, v in enumerate(FRUSTRATION_LEVELS))
    + "\nteam_confidence: a number from 0 to 1 for how sure you are about the team."
)
TICKET_SCHEMA = {
    "name": "ticket_labels", "strict": True,
    "schema": {
        "type": "object", "additionalProperties": False,
        "required": ["team", "urgency", "frustration", "team_confidence"],
        "properties": {
            "team": {"type": "string", "enum": list(TEAMS)},
            "urgency": {"type": "integer", "enum": [0, 1, 2]},
            "frustration": {"type": "integer", "enum": [0, 1, 2]},
            "team_confidence": {"type": "number"},
        },
    },
}


def ticket_from_jev(answers: dict[str, Any]) -> dict[str, Any]:
    """Jev's typed answers in the common form."""
    return {"team": answers["team"]["choice"], "team_confidence": answers["team"]["confidence"],
            "urgency": round(answers["urgency"]["score"]),
            "frustration": round(answers["frustration"]["score"])}


def ticket_from_openai(answer: dict[str, Any]) -> dict[str, Any]:
    """An OpenAI JSON answer in the common form."""
    return {"team": answer["team"], "team_confidence": float(answer["team_confidence"]),
            "urgency": int(answer["urgency"]), "frustration": int(answer["frustration"])}


# ------------------------------------------------------------ duplicate records

LINK_LEVELS_V1 = [
    "They describe two different companies. This includes a parent company and its "
    "subsidiary in another country, and two companies that share a name but are in "
    "different countries or cities.",
    "They might be the same company, but the evidence is missing or conflicts, so a "
    "person should check before anything is merged.",
    "They describe one and the same company, written differently.",
]
"""The first wording. Jev read "evidence is missing" literally and sent many clear
duplicates to a person, because some field is missing in most real records."""

LINK_LEVELS_V2 = [
    LINK_LEVELS_V1[0],
    "The records disagree on something important that the other fields cannot explain, "
    "so a person should check before anything is merged.",
    "They describe one and the same company. One company is often written differently in "
    "different systems: legal words like Ltd or GmbH added or dropped, short forms, capital "
    "letters, small typos, an old city name, a missing phone or website, a different contact "
    "person, or a new street address in the same city.",
]
"""The second wording: say what is normal for a duplicate, so a missing field is not
read as a reason to stop."""

WORDINGS = {"v1": LINK_LEVELS_V1, "v2": LINK_LEVELS_V2}


def pair_questions(wording: str = "v2") -> dict[str, Any]:
    """The Jev questions for one pair: one Score and two Nouls."""
    return {
        "link": Score(instructions="How do the two company records relate?",
                      criteria=WORDINGS[wording]),
        "same_name": Noul(instructions="Do `record_a` and `record_b` name the same company, "
                          "ignoring legal words like Ltd or GmbH, short forms, capital letters "
                          "and small typos?"),
        "same_place": Noul(instructions="Do `record_a` and `record_b` put the company in the "
                           "same city and country? Old city names count as the same city, for "
                           "example Bombay and Mumbai."),
    }


def pair_system_prompt(wording: str = "v2") -> str:
    """The same questions, written for an OpenAI model."""
    return (
        "You compare two company records from different business systems. "
        "Answer with JSON only.\n"
        "link: how do the two company records relate? "
        + "; ".join(f"{i} = {v}" for i, v in enumerate(WORDINGS[wording]))
        + "\nlink_confidence: a number from 0 to 1 for how sure you are about link."
        + "\nsame_name: do record_a and record_b name the same company, ignoring legal words "
          "like Ltd or GmbH, short forms, capital letters and small typos?"
        + "\nsame_place: do record_a and record_b put the company in the same city and country? "
          "Old city names count as the same city, for example Bombay and Mumbai."
    )


PAIR_QUESTIONS = pair_questions("v2")
PAIR_SYSTEM_PROMPT = pair_system_prompt("v2")
PAIR_SCHEMA = {
    "name": "pair_labels", "strict": True,
    "schema": {
        "type": "object", "additionalProperties": False,
        "required": ["link", "link_confidence", "same_name", "same_place"],
        "properties": {
            "link": {"type": "integer", "enum": [0, 1, 2]},
            "link_confidence": {"type": "number"},
            "same_name": {"type": "boolean"},
            "same_place": {"type": "boolean"},
        },
    },
}

HIDDEN_FIELDS = {"record_id"}


def pair_state(pair: dict[str, Any]) -> dict[str, Any]:
    """The material both models see for one pair.

    Comparing digits is arithmetic, and the docs say Jev is not a calculator,
    so plain code does that check and the result goes into the state.
    The truth label is never part of the state.
    """
    def digits(phone: str | None) -> str:
        return re.sub(r"\D", "", phone or "")[-7:]

    def domain(record: dict[str, Any]) -> str | None:
        site = record.get("website")
        return re.sub(r"^(https?://)?(www\.)?", "", site) if site else None

    a, b = pair["a"], pair["b"]
    same_phone = (digits(a["phone"]) == digits(b["phone"])) if a["phone"] and b["phone"] else None
    same_site = (domain(a) == domain(b)) if domain(a) and domain(b) else None
    return {
        "record_a": {k: v for k, v in a.items() if k not in HIDDEN_FIELDS},
        "record_b": {k: v for k, v in b.items() if k not in HIDDEN_FIELDS},
        "checked_by_code": {"phone_last_7_digits_match": same_phone,
                            "website_matches": same_site},
    }


def pair_user_message(pair: dict[str, Any]) -> str:
    """The same state, as text for an OpenAI model."""
    return json.dumps(pair_state(pair), ensure_ascii=False)


def pair_from_jev(answers: dict[str, Any]) -> dict[str, Any]:
    """Jev's typed answers in the common form."""
    link = answers["link"]
    return {"link": min(round(link["score"]), 2), "link_score": link["score"],
            "link_confidence": link["confidence"],
            "p_same": link["probabilities"].get("2", link["probabilities"].get(2, 0.0)),
            "same_name": answers["same_name"]["noul"], "same_place": answers["same_place"]["noul"]}


def pair_from_openai(answer: dict[str, Any]) -> dict[str, Any]:
    """An OpenAI JSON answer in the common form."""
    return {"link": int(answer["link"]), "link_score": float(answer["link"]),
            "link_confidence": float(answer["link_confidence"]),
            "p_same": float(answer["link_confidence"]) if int(answer["link"]) == 2 else 0.0,
            "same_name": float(answer["same_name"]), "same_place": float(answer["same_place"])}
