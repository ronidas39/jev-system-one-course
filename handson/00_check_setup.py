"""Exercise 0: check the setup. Is the key there, and can we reach TypeSafe?

Lists the model names your account can use. Never prints the key.

Author: Roni Das
Created: 2026-10-04
"""

import typesafe_sdk
from typesafe_sdk import TypeSafeClient

from common import check_key_present, show

check_key_present()
show("SDK version", typesafe_sdk.__version__)

with TypeSafeClient() as client:
    listing = client.models.list()

for model in listing.models:
    show(model.name, f"released {model.release_date[:10]}: {model.description}")
