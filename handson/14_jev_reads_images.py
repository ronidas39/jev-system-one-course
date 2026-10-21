"""Exercise 14: Jev reads a photo. A refund claim with a message and a photo.

On 14 October 2026 TypeSafe announced image input for Jev. It is a "danger zone"
feature: send the header TypeSafe-Danger-Zone-Images: true, and do not use it in
production yet. A Box question (where is it?) needs Jev 1.14, so we ask jev-preview.

Run it from the handson folder:
    python 14_jev_reads_images.py

Author: Roni Das
Created: 2026-10-21
"""

import io
import os

from PIL import Image as PILImage
from PIL import ImageDraw
from typesafe_sdk import Box, Choice, Image, Noul, TypeSafeClient

# Read the API key from the .env file in the course folder (one folder up).
for line in open("../.env"):
    if line.startswith("TYPESAFE_API_KEY="):
        os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip()

# Three refund claims from the egg shop: the claim, the message, the photo it came with.
CLAIMS = [
    ("C06", "Broken egg in the pack, see the photo.", "broken-01"),
    ("C03", "One egg in my pack is cracked.", "box10-03"),
    ("C05", "My order came a day late.", "tray-02"),
]

QUESTIONS = {
    "broken": Noul(instructions="Does `photo` show an egg that is cracked or broken?"),
    "condition": Choice(
        instructions="What is the condition of the egg shell in `photo`?",
        criteria={
            "clean": "Shell is intact with no dirt, stains or droppings.",
            "dirty": "Shell is intact but has dirt, stains or droppings.",
            "cracked": "Shell has a crack, hole, or is broken open.",
            "unclear": "The photo does not show the shell well enough.",
        },
    ),
    "matches": Noul(instructions="Does `photo` show the problem described in `message`?"),
    "where": Box(instructions="the egg in `photo`"),
}

with TypeSafeClient(model="jev-preview") as client:
    for claim_id, message, photo_name in CLAIMS:
        # Jev takes PNG or JPEG, 280 to 1568 pixels on each side.
        # Some of our egg photos are smaller, so we scale them up first.
        photo = PILImage.open(f"../decisions/eggs/{photo_name}.jpg").convert("RGB")
        if min(photo.size) < 280:
            scale = 280 / min(photo.size)
            size = (round(photo.width * scale), round(photo.height * scale))
            photo = photo.resize(size)
        jpeg = io.BytesIO()
        photo.save(jpeg, "JPEG", quality=90)

        response = client.system_one(
            state={"message": message, "photo": Image(jpeg.getvalue())},
            questions=QUESTIONS,
            extra_headers={"TypeSafe-Danger-Zone-Images": "true"},
        )
        answers = response.answers

        print(f"{claim_id}  {message}")
        print(f"   photo {photo_name}, sent at {photo.width}x{photo.height}")
        print(f"   broken (noul)      {answers['broken'].noul:.2f}")
        print(f"   condition (choice) {answers['condition'].choice}"
              f"  confidence {answers['condition'].confidence:.2f}")
        print(f"   matches (noul)     {answers['matches'].noul:.2f}")

        # The Box answer: four edges, as fractions of the photo's width and height.
        edges = answers["where"].box
        print(f"   where (box)        left {edges.left:.2f} top {edges.top:.2f}"
              f" right {edges.right:.2f} bottom {edges.bottom:.2f}"
              f"  confidence {answers['where'].confidence:.2f}")

        # Draw the box on the photo, so we can see where Jev looked.
        box = (edges.left * photo.width, edges.top * photo.height,
               edges.right * photo.width, edges.bottom * photo.height)
        ImageDraw.Draw(photo).rectangle(box, outline="red", width=4)
        photo.save(f"out_{claim_id}_box.jpg")

        print(f"   model {response.model}, input tokens {response.usage.input_tokens}")
        print()
