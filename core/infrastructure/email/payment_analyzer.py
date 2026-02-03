import re
import math
from collections import Counter
from decimal import Decimal
from core.infrastructure.models import UsedPaymentReference

BANK_KEY_PHRASES = [
    "interac e-transfer",
    "you have received money",
    "deposit completed",
]

REFERENCE_REGEX = r"\b[A-Z0-9]{8,20}\b"
AMOUNT_REGEX = r"\$?\s?([0-9]+(?:\.[0-9]{2}))"

def entropy(s):
    counts = Counter(s)
    probs = [v / len(s) for v in counts.values()]
    return -sum(p * math.log2(p) for p in probs)

def looks_random(reference):
    return entropy(reference) > 2.8

def extract_reference(text):
    matches = re.findall(REFERENCE_REGEX, text.upper())
    return matches[0] if matches else None

def extract_amount(text):
    m = re.search(AMOUNT_REGEX, text)
    return Decimal(m.group(1)) if m else None

def bank_template_score(text):
    score = 0
    t = text.lower()
    for phrase in BANK_KEY_PHRASES:
        if phrase in t:
            score += 1
    return score

def reference_used(ref):
    return UsedPaymentReference.objects.filter(reference=ref).exists()

def analyze_payment_email(body, expected_total):
    ref = extract_reference(body)
    amount = extract_amount(body)

    if not ref or not amount:
        return None, "missing_data"

    if reference_used(ref):
        return None, "reference_used"

    score = 0
    score += bank_template_score(body)
    score += 2 if looks_random(ref) else -3
    score += 3 if amount == expected_total else -5

    if score < 4:
        return None, "low_confidence"

    return {
        "reference": ref,
        "amount": amount
    }, "ok"
