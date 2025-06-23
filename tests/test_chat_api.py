import unittest
from unittest.mock import Mock, patch
from resonant_chat.chat_api import ChatAPI


class TestChatAPI(unittest.TestCase):
    def setUp(self):
        self.endpoint = "https://api.example.com/chat"
        self.api = ChatAPI(self.endpoint)

    def test_initialization(self):
        """Test that ChatAPI initializes with correct defaults"""
        self.assertEqual(self.api.endpoint, self.endpoint)
        self.assertEqual(self.api.headers["Content-Type"], "application/json")

        # Test with custom headers
        custom_headers = {"Authorization": "Bearer token123"}
        api_with_headers = ChatAPI(self.endpoint, headers=custom_headers)
        self.assertEqual(api_with_headers.headers["Content-Type"], "application/json")
        self.assertEqual(api_with_headers.headers["Authorization"], "Bearer token123")

    def test_query_character_limit_enforcement(self):
        """Test that non-streaming query enforces character limits"""
        # Mock a response that exceeds the character limit
        long_content = "x" * 1000
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": long_content}}]
        }

        with patch("requests.post", return_value=mock_response):
            result = self.api.query(
                messages=[{"role": "user", "content": "test"}],
                model="test-model",
                max_chars=100,
            )

            # Should be truncated to 100 characters
            self.assertEqual(len(result), 100)
            self.assertEqual(result, "x" * 100)

    def test_query_stream_character_limit_across_chunks(self):
        """Test that streaming query enforces character limits across multiple chunks"""
        # Create mock streaming response with multiple chunks
        chunks = [
            'data: {"choices": [{"delta": {"content": "Hello "}}]}\n',
            'data: {"choices": [{"delta": {"content": "this is a "}}]}\n',
            'data: {"choices": [{"delta": {"content": "very long message"}}]}\n',
            "data: [DONE]\n",
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [chunk.encode() for chunk in chunks]

        with patch("requests.post", return_value=mock_response):
            result = list(
                self.api.query_stream(
                    messages=[{"role": "user", "content": "test"}],
                    model="test-model",
                    max_chars=15,  # Should stop partway through second chunk
                )
            )

            # Concatenate all yielded chunks
            full_result = "".join(result)
            self.assertEqual(len(full_result), 15)
            self.assertEqual(full_result, "Hello this is a")

    def test_query_stream_partial_chunk_at_limit(self):
        """Test that streaming correctly yields partial chunk when hitting limit"""
        chunks = [
            'data: {"choices": [{"delta": {"content": "12345"}}]}\n',
            'data: {"choices": [{"delta": {"content": "678901234567890"}}]}\n',
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [chunk.encode() for chunk in chunks]

        with patch("requests.post", return_value=mock_response):
            result = list(
                self.api.query_stream(
                    messages=[{"role": "user", "content": "test"}],
                    model="test-model",
                    max_chars=10,
                )
            )

            full_result = "".join(result)
            self.assertEqual(len(full_result), 10)
            self.assertEqual(full_result, "1234567890")

    def test_different_response_formats(self):
        """Test parsing of different API response formats"""
        messages = [{"role": "user", "content": "test"}]

        # Test OpenAI format
        openai_response = Mock()
        openai_response.status_code = 200
        openai_response.json.return_value = {
            "choices": [{"message": {"content": "OpenAI response"}}]
        }

        with patch("requests.post", return_value=openai_response):
            result = self.api.query(messages, "test-model")
            self.assertEqual(result, "OpenAI response")

        # Test Ollama format
        ollama_response = Mock()
        ollama_response.status_code = 200
        ollama_response.json.return_value = {"message": {"content": "Ollama response"}}

        with patch("requests.post", return_value=ollama_response):
            result = self.api.query(messages, "test-model")
            self.assertEqual(result, "Ollama response")

        # Test Anthropic format with content array
        anthropic_response = Mock()
        anthropic_response.status_code = 200
        anthropic_response.json.return_value = {
            "content": [
                {"type": "text", "text": "Anthropic "},
                {"type": "text", "text": "response"},
            ]
        }

        with patch("requests.post", return_value=anthropic_response):
            result = self.api.query(messages, "test-model")
            self.assertEqual(result, "Anthropic response")

    def test_streaming_response_formats(self):
        """Test parsing of different streaming formats"""
        # Test Anthropic streaming format
        anthropic_chunks = [
            'data: {"delta": {"type": "text_delta", "text": "Hello "}}\n',
            'data: {"delta": {"type": "text_delta", "text": "Anthropic"}}\n',
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            chunk.encode() for chunk in anthropic_chunks
        ]

        with patch("requests.post", return_value=mock_response):
            result = list(
                self.api.query_stream(
                    messages=[{"role": "user", "content": "test"}], model="test-model"
                )
            )

            self.assertEqual("".join(result), "Hello Anthropic")

        # Test Ollama streaming format (direct JSON lines)
        ollama_chunks = [
            '{"message": {"content": "Hello "}}\n',
            '{"message": {"content": "Ollama"}}\n',
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            chunk.encode() for chunk in ollama_chunks
        ]

        with patch("requests.post", return_value=mock_response):
            result = list(
                self.api.query_stream(
                    messages=[{"role": "user", "content": "test"}], model="test-model"
                )
            )

            self.assertEqual("".join(result), "Hello Ollama")

    def test_system_prompt_handling(self):
        """Test that system prompts are added correctly"""
        messages = [{"role": "user", "content": "test"}]
        system_prompt = "You are a helpful assistant"

        # Test system prompt as message (default)
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response

            self.api.query(messages, "test-model", system_prompt=system_prompt)

            # Check the payload sent
            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            # System prompt should be first message
            self.assertEqual(len(payload["messages"]), 2)
            self.assertEqual(payload["messages"][0]["role"], "system")
            self.assertEqual(payload["messages"][0]["content"], system_prompt)
            self.assertEqual(payload["messages"][1], messages[0])

        # Test system prompt as top-level parameter
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response

            self.api.query(
                messages,
                "test-model",
                system_prompt=system_prompt,
                top_level_system=True,
            )

            # Check the payload sent
            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            # System prompt should be top-level, not in messages
            self.assertEqual(len(payload["messages"]), 1)
            self.assertEqual(payload["messages"][0], messages[0])
            self.assertEqual(payload["system"], system_prompt)

    def test_payload_additions(self):
        """Test that additional payload fields are included"""
        messages = [{"role": "user", "content": "test"}]
        additions = {"temperature": 0.7, "max_tokens": 500}

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response

            self.api.query(messages, "test-model", payload_additions=additions)

            # Check the payload sent
            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            self.assertEqual(payload["temperature"], 0.7)
            self.assertEqual(payload["max_tokens"], 500)
            self.assertIn("model", payload)
            self.assertIn("messages", payload)

    def test_error_handling(self):
        """Test that errors are handled gracefully"""
        import requests

        messages = [{"role": "user", "content": "test"}]

        # Test request exception
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException(
                "Connection error"
            )

            result = self.api.query(messages, "test-model")
            self.assertEqual(result, "")

        # Test HTTP error
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "HTTP 500"
            )
            mock_post.return_value = mock_response

            result = self.api.query(messages, "test-model")
            self.assertEqual(result, "")

    def test_json_decode_error_handling_in_stream(self):
        """Test that JSON decode errors are handled in streaming"""
        # Mix valid and invalid JSON
        chunks = [
            'data: {"choices": [{"delta": {"content": "Valid"}}]}\n',
            "data: INVALID JSON\n",
            'data: {"choices": [{"delta": {"content": " chunk"}}]}\n',
            "data: [DONE]\n",
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [chunk.encode() for chunk in chunks]

        with patch("requests.post", return_value=mock_response):
            result = list(
                self.api.query_stream(
                    messages=[{"role": "user", "content": "test"}], model="test-model"
                )
            )

            # Should skip the invalid JSON and continue
            self.assertEqual("".join(result), "Valid chunk")


if __name__ == "__main__":
    unittest.main()
