import re

ILLEGAL_CHARACTERS = r'[\\/:*?"<>|{}$!\'"&%`@+=,;]'

def sanitize_filename(filename):
    sanitized = re.sub(ILLEGAL_CHARACTERS, '', filename)
    sanitized = re.sub(r'[^\x00-\x7F]+', '', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    return sanitized
