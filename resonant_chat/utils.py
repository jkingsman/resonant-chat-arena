import json
import re
from typing import Tuple, Dict, List, Optional


def filter_thinking_tags(content: str) -> Tuple[str, str]:
    """
    Remove content between <think></think> or <thinking></thinking> tags.
    Returns a tuple of (filtered_content, original_content).
    """
    # Pattern to match both <think> and <thinking> tags (case-insensitive)
    pattern = r"<(?:think|thinking)>.*?</(?:think|thinking)>"

    # Remove the thinking sections
    filtered = re.sub(pattern, "", content, flags=re.DOTALL | re.IGNORECASE)

    # Clean up any resulting double spaces or extra newlines
    filtered = re.sub(r"\n\s*\n\s*\n", "\n\n", filtered)
    filtered = re.sub(r"  +", " ", filtered)
    filtered = filtered.strip()

    return filtered, content


def parse_payload_additions(payload_str: str) -> Dict[str, any]:
    """Parse a JSON string into a dictionary for payload additions"""
    try:
        return json.loads(payload_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing payload additions: {e}")
        print('Expected JSON format, e.g.: \'{"temperature": 0.7, "top_p": 0.9}\'')
        return {}


def parse_headers(header_str: str) -> Dict[str, str]:
    """Parse a JSON string into a dictionary for headers"""
    try:
        headers = json.loads(header_str)
        # Ensure all values are strings
        return {k: str(v) for k, v in headers.items()}
    except json.JSONDecodeError as e:
        print(f"Error parsing headers: {e}")
        print(
            'Expected JSON format, e.g.: \'{"Authorization": "Bearer YOUR_API_KEY"}\''
        )
        return {}


def parse_preamble_file(preamble_path: Optional[str]) -> Optional[List[Dict[str, str]]]:
    """Parse a JSON file containing preamble messages"""
    if not preamble_path:
        return None
    
    try:
        with open(preamble_path, 'r') as f:
            preamble = json.load(f)
        
        # Validate the structure
        if not isinstance(preamble, list):
            print(f"Error: Preamble file must contain a JSON array of messages")
            return None
        
        for i, msg in enumerate(preamble):
            if not isinstance(msg, dict):
                print(f"Error: Message {i} in preamble must be a dictionary")
                return None
            if "role" not in msg or "content" not in msg:
                print(f"Error: Message {i} in preamble must have 'role' and 'content' fields")
                return None
            if msg["role"] not in ["user", "assistant", "system"]:
                print(f"Error: Message {i} has invalid role '{msg['role']}'. Must be 'user', 'assistant', or 'system'")
                return None
        
        return preamble
    
    except FileNotFoundError:
        print(f"Error: Preamble file not found: {preamble_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing preamble JSON: {e}")
        print('Expected format: [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]')
        return None
    except Exception as e:
        print(f"Error reading preamble file: {e}")
        return None
