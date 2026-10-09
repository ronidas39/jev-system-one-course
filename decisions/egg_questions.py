"""The three questions we ask about every egg photo. Shared by 09, 10 and 11.

Author: Roni Das
Created: 2026-10-09
"""

OPTIONS = ["clean", "dirty", "cracked", "unclear"]

EGG_QUESTIONS = [
    {
        "type": "choice",
        "name": "condition",
        "instructions": "What is the condition of the egg shell in this photo?",
        "choices": [
            {"value": "clean", "description": "Shell is intact with no dirt, stains or droppings."},
            {"value": "dirty", "description": "Shell is intact but has dirt, stains or droppings."},
            {"value": "cracked", "description": "Shell has a crack, hole, or is broken open."},
            {"value": "unclear", "description": "The photo does not show the shell well enough."},
        ],
    },
    {
        "type": "predicate",
        "name": "visible_crack",
        "instructions": "Does the egg shell have a visible crack, hole or break? Ignore shadows "
        "and the carton.",
    },
    {
        "type": "score",
        "name": "dirt_level",
        "instructions": "How dirty is the egg shell?",
        "levels": [
            {"label": "none", "description": "No visible dirt or stains."},
            {"label": "light", "description": "A few small marks a customer might not notice."},
            {"label": "heavy", "description": "Smears or many spots a customer would notice."},
        ],
    },
]
