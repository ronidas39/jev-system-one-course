"""Make synthetic customer support tickets, with the right answers attached.

Every ticket is built from parts: one main problem (which decides the team),
one urgency phrase (which decides urgency), one mood phrase (which decides
frustration), and some mess: greetings, signatures, typos, lowercase text,
extra details nobody needs, and a side remark about another team's topic.

The same seed always makes the same file, so your numbers can match mine.

    python data/make_tickets.py            # writes data/tickets.jsonl (300 tickets)

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import json
import random
from pathlib import Path

SEED = 20261006
OUT = Path(__file__).with_name("tickets.jsonl")

PRODUCTS = ["the Pro plan", "the Team plan", "the mobile app", "the desktop app", "the API",
            "the web dashboard", "the analytics add-on", "the starter kit"]
PLANS = ["the Pro plan", "the Team plan", "the analytics add-on", "my monthly plan"]
CITIES = ["Pune", "Leeds", "Austin", "Lagos", "Manila", "Kraków", "Toronto", "Kochi"]

PROBLEMS: dict[str, list[str]] = {
    "billing": [
        "I was charged {amount} twice for {plan} this month.",
        "My invoice {invoice} shows {amount} but my plan costs less than that.",
        "I cancelled {plan} last month and you still took {amount} from my card.",
        "Please send a refund for the {amount} charge on {date}, we never used it.",
        "The VAT number is missing from invoice {invoice}, our finance team needs it fixed.",
        "Why did the price of {plan} go up to {amount} without any notice?",
        "My card was declined but the money left my account anyway. Order {order}.",
        "Can you change the billing email on our account? Invoices go to someone who left.",
    ],
    "technical": [
        "{product} crashes every time I open the reports page.",
        "We get a 500 error from the API on every POST to /v2/orders since this morning.",
        "The export button does nothing. I click it and no file arrives.",
        "Sync between the mobile app and the web dashboard stopped working after the update.",
        "Our webhook stopped firing. The last event we received was on {date}.",
        "Pages in {product} take more than a minute to load, it used to be instant.",
        "Login works but the dashboard shows a blank white screen in Chrome and Safari.",
        "The CSV import fails with the message 'unexpected column 7'.",
    ],
    "shipping": [
        "My order {order} says delivered but nothing arrived.",
        "The tracking link for order {order} has not changed in six days.",
        "The parcel arrived with the box crushed and the device inside is cracked.",
        "Can I change the delivery address for order {order}? I moved to {city}.",
        "The courier left my package with a neighbour I do not know.",
        "Order {order} was meant to arrive on {date} and there is still no sign of it.",
        "I received someone else's item in my parcel instead of what I ordered.",
        "Do you ship to {city}? The checkout will not accept my postcode.",
    ],
    "account": [
        "I cannot log in. The password reset email never arrives.",
        "Please delete my account and all the data you hold about me.",
        "I got an email about a login from a country I have never visited.",
        "How do I give my colleague admin rights on our workspace?",
        "Two-factor codes stopped working after I changed my phone.",
        "I need to change the owner of our workspace because I am leaving the company.",
        "My account is locked after too many attempts and I do not know why.",
        "Please change the email address on my profile to my new work address.",
    ],
    "sales": [
        "We are 40 people and want a quote for {product} for the whole company.",
        "Do you give a discount for non-profit organisations?",
        "Can we book a demo of {product} for our leadership team?",
        "What is the price difference between the Team plan and Enterprise?",
        "We want to move from the Team plan to Enterprise next quarter. Who should we talk to?",
        "Is there an annual plan that is cheaper than paying monthly for {product}?",
        "Our procurement team needs a formal quote and your security documents.",
        "Can we try {product} for a month before we buy it for 200 seats?",
    ],
}

URGENCY: list[list[str]] = [
    ["No rush on this.", "Whenever someone has time is fine.", "Just asking for later.",
     "It is not urgent.", "", ""],
    ["Could you look at this in the next day or two?", "We need this sorted this week.",
     "Please reply before Friday if you can.", "It would be good to fix this soon.",
     "Our month-end close is next week, so we need it by then."],
    ["Our whole team is blocked right now.", "This is stopping our payroll run today.",
     "We cannot take any orders until this is fixed.", "I need this fixed within the hour.",
     "Customers are complaining right now and we are losing sales.",
     # Was "This looks like someone is in my account at this moment." (fixed 5 Oct 2026). That
     # phrase describes an account-security problem, which the prompt gives to the account team,
     # but it was added to tickets of every team, so 13 of 15 labels contradicted the prompt.
     # Same position in the list, so every other ticket comes out exactly as before.
     "Nothing works for us until this is fixed."],
]

MOOD: list[list[str]] = [
    ["Thanks for your help.", "Thank you in advance.", "", "Have a nice day.", ""],
    ["This is the second time I am writing about this.",
     "Honestly this is a bit disappointing.", "I expected better, to be honest.",
     "I have been waiting for an answer for three days now."],
    ["This is completely unacceptable.", "If this is not fixed today I am cancelling and "
     "telling everyone I know.", "I am furious. Third time this month!!",
     "Worst service I have ever paid for. I want to speak to a manager.",
     "I will dispute the charge with my bank if nobody answers."],
]

GREETINGS = ["Hi,", "Hello team,", "hey", "Dear support,", "Good morning,", ""]
SIGNATURES = ["Thanks, Priya", "Regards,\nTomás", "- Sent from my phone", "Best, Aisha K.",
              "Cheers, Ben", "", "Kind regards, Mr. Okafor"]
EXTRA_DETAILS = [
    "We are a small team of 12 in {city}.",
    "I have been a customer since 2021.",
    "My manager asked me to write to you.",
    "I am using a MacBook with the latest updates.",
    "Our office moved last year.",
]
SIDE_REMARKS = {
    "billing": "I know the invoice is due soon, but that is not the issue here.",
    "technical": "The app works fine otherwise.",
    "shipping": "The payment went through without a problem.",
    "account": "I can still see my orders.",
    "sales": "We are happy with the product so far.",
}


def fill(template: str, rng: random.Random) -> str:
    """Put random but realistic values into the {slots} of one sentence."""
    return template.format(
        amount=f"${rng.choice([19, 29, 49, 99, 149, 480])}.{rng.choice(['00', '99'])}",
        product=rng.choice(PRODUCTS),
        plan=rng.choice(PLANS),
        invoice=f"INV-{rng.randint(10000, 99999)}",
        order=f"#{rng.randint(100000, 999999)}",
        date=f"{rng.randint(1, 28)} September",
        city=rng.choice(CITIES),
    )


def add_typo(text: str, rng: random.Random) -> str:
    """Swap two letters inside one longer word, like a fast typist would."""
    words = text.split(" ")
    long_words = [i for i, w in enumerate(words) if len(w) > 5 and w.isalpha()]
    if not long_words:
        return text
    i = rng.choice(long_words)
    w = words[i]
    j = rng.randint(1, len(w) - 3)
    words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def make_ticket(number: int, rng: random.Random) -> dict[str, object]:
    """Build one ticket and remember exactly what went into it."""
    team = rng.choice(list(PROBLEMS))
    urgency = rng.choices([0, 1, 2], weights=[4, 3, 3])[0]
    frustration = rng.choices([0, 1, 2], weights=[5, 3, 2])[0]
    traits: list[str] = []
    parts = [rng.choice(GREETINGS)]
    if rng.random() < 0.35:
        parts.append(fill(rng.choice(EXTRA_DETAILS), rng))
        traits.append("extra_detail")
    parts.append(fill(rng.choice(PROBLEMS[team]), rng))
    if rng.random() < 0.25:
        other = rng.choice([t for t in SIDE_REMARKS if t != team])
        parts.append(SIDE_REMARKS[other])
        traits.append(f"side_remark_about_{other}")
    parts += [rng.choice(URGENCY[urgency]), rng.choice(MOOD[frustration]), rng.choice(SIGNATURES)]
    text = " ".join(p for p in parts if p).replace(" \n", "\n")
    if rng.random() < 0.3:
        text = add_typo(text, rng)
        traits.append("typo")
    if rng.random() < 0.15:
        text = text.lower()
        traits.append("all_lowercase")
    return {"id": f"T{number:04d}", "text": text, "team": team, "urgency": urgency,
            "frustration": frustration, "traits": traits}


def main() -> None:
    """Write the tickets file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    tickets = [make_ticket(i + 1, rng) for i in range(args.count)]
    OUT.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tickets))
    teams = {t: sum(x["team"] == t for x in tickets) for t in PROBLEMS}
    print(f"wrote {len(tickets)} tickets to {OUT.name} (seed {args.seed})")
    print("tickets per team:", teams)


if __name__ == "__main__":
    main()
