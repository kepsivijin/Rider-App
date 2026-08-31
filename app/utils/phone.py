import re


def normalize_phone(phone_number: str) -> str:
    """Normalize to 10-digit Indian mobile number."""
    digits = re.sub(r'\D', '', phone_number or '')
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    return digits
