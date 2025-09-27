import re


def extract_id_from_url(url: str) -> int:
    """Extract the numeric ID from the URL field.
    - Handles optional trailing slash
    """
    match = re.search(r"/(\d+)/?$", url)
    if match:
        return int(match.group(1))
    raise ValueError(f"Could not extract ID from URL: {url}")