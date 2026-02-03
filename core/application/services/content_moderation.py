import json
from openai import OpenAI

def moderate_text(api_key: str, text: str) -> str | None:
    """
    Returns None if content is allowed
    Returns error message string if content is NOT allowed
    """

    if not api_key:
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a strict content moderation system.

Your task is ONLY to analyze the following text.
DO NOT rewrite, improve, summarize, or generate any content.

Check whether the text contains ANY of the following:
- Hate speech
- Insults or offensive language
- Sexual content
- Nudity
- Adult content
- Political content
- Religious extremism
- Violence or threats
- Illegal activities
- Harassment or discrimination

Return the result ONLY in valid JSON format with no extra text.

JSON format:
{{
  "allowed": true | false,
  "issues": [list of detected issues],
  "confidence": "low | medium | high"
}}

Text to analyze:
\"\"\"
{text}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        if not result.get("allowed", False):
            issues = ", ".join(result.get("issues", []))
            return f"Content rejected due to: {issues}"

        return None

    except Exception:
        return None
