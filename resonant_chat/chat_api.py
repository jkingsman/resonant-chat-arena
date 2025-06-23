import requests
import json
from typing import List, Dict, Optional, Generator


class ChatAPI:
    """Handles communication with any OpenAI-compatible chat API, or Anthropic compatibel with top_level_system=True"""

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint
        self.headers = {"Content-Type": "application/json"}
        # Merge any additional headers
        if headers:
            self.headers.update(headers)

    def query_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_chars: int = 10000,
        system_prompt: Optional[str] = None,
        payload_additions: Optional[Dict[str, any]] = None,
        top_level_system: bool = False,
    ) -> Generator[str, None, None]:
        """Query the API with streaming response, enforcing character limit"""

        payload = {
            "model": model,
            "messages": [],
            "stream": True,
        }

        # Add any additional payload fields
        if payload_additions:
            payload.update(payload_additions)

        # Add system prompt - either as top-level parameter or as a message
        if system_prompt:
            if top_level_system:
                payload["system"] = system_prompt
            else:
                payload["messages"].append({"role": "system", "content": system_prompt})

        # Add conversation messages
        payload["messages"].extend(messages)

        char_count = 0

        try:
            response = requests.post(
                self.endpoint, headers=self.headers, json=payload, stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    # OpenAI format
                    if line_str.startswith("data: "):
                        if line_str.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line_str[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    chunk = delta["content"]
                                    # Check if adding this chunk would exceed limit
                                    if char_count + len(chunk) > max_chars:
                                        # Yield only the portion that fits
                                        remaining_chars = max_chars - char_count
                                        if remaining_chars > 0:
                                            yield chunk[:remaining_chars]
                                        break  # Stop streaming
                                    else:
                                        char_count += len(chunk)
                                        yield chunk
                            elif "delta" in data:
                                # Anthropic streaming format
                                delta = data["delta"]
                                if (
                                    delta.get("type") == "text_delta"
                                    and "text" in delta
                                ):
                                    chunk = delta["text"]
                                    # Check if adding this chunk would exceed limit
                                    if char_count + len(chunk) > max_chars:
                                        # Yield only the portion that fits
                                        remaining_chars = max_chars - char_count
                                        if remaining_chars > 0:
                                            yield chunk[:remaining_chars]
                                        break  # Stop streaming
                                    else:
                                        char_count += len(chunk)
                                        yield chunk
                        except json.JSONDecodeError:
                            continue
                    else:
                        # Ollama format - direct JSON lines
                        try:
                            data = json.loads(line_str)
                            if "message" in data and "content" in data["message"]:
                                chunk = data["message"]["content"]
                                # Check if adding this chunk would exceed limit
                                if char_count + len(chunk) > max_chars:
                                    # Yield only the portion that fits
                                    remaining_chars = max_chars - char_count
                                    if remaining_chars > 0:
                                        yield chunk[:remaining_chars]
                                    break  # Stop streaming
                                else:
                                    char_count += len(chunk)
                                    yield chunk
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.RequestException as e:
            print(f"\nError querying API: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"API message: {e.response.text}")
            yield ""

    def query(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_chars: int = 10000,
        system_prompt: Optional[str] = None,
        payload_additions: Optional[Dict[str, any]] = None,
        top_level_system: bool = False,
    ) -> str:
        """Query the API without streaming, enforcing character limit"""

        payload = {
            "model": model,
            "messages": [],
            "stream": False,
        }

        # Add any additional payload fields
        if payload_additions:
            payload.update(payload_additions)

        # Add system prompt - either as top-level parameter or as a message
        if system_prompt:
            if top_level_system:
                payload["system"] = system_prompt
            else:
                payload["messages"].append({"role": "system", "content": system_prompt})

        payload["messages"].extend(messages)

        try:
            response = requests.post(self.endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Handle both OpenAI and Ollama response formats
            content = ""
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"].strip()
            elif "message" in data and "content" in data["message"]:
                content = data["message"]["content"].strip()
            elif "content" in data:
                # Anthropic format - content is an array of content blocks
                if isinstance(data["content"], list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in data["content"]:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    content = "".join(text_parts).strip()
                else:
                    # Fallback if content is a string
                    content = str(data["content"]).strip()
            else:
                print(f"Unexpected response format: {data}")
                return ""

            # Truncate to max_chars if necessary
            if len(content) > max_chars:
                content = content[:max_chars]
                print(f"\n[Response truncated to {max_chars} characters]")

            return content

        except requests.exceptions.RequestException as e:
            print(f"Error querying API: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"API message: {e.response.text}")
            return ""
