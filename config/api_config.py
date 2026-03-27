import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def get_anthropic_api_key() -> str:
	key = (ANTHROPIC_API_KEY or "").strip()
	if not key or key.lower() == "your_key_here":
		raise RuntimeError("Anthropic API key not configured")
	return key
