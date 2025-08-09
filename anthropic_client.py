# anthropic_client.py
import os
from anthropic import Anthropic

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing ANTHROPIC_API_KEY environment variable")

client = Anthropic(api_key=API_KEY)
