# forms_utils.py
# Validation helpers for forms to be used across all 7 forms
import re
from typing import Dict

def validate_email(email: str) -> bool:
    if not email:
        return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def validate_required(fields: Dict[str, object]) -> Dict[str, str]:
    """
    fields: {"field_name": value}
    returns dict of errors keyed by field_name
    """
    errors = {}
    for k, v in fields.items():
        if v is None or (isinstance(v, str) and v.strip() == ""):
            errors[k] = "This field is required"
    return errors
