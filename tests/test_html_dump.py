#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, patch, mock_open
from html import escape
from resonant_chat.dual_model_session import DualModelSession
from resonant_chat.html_dump import save_html_checkpoint


class TestSaveHtmlCheckpoint(unittest.TestCase):
    """Test cases for save_html_checkpoint function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock(spec=DualModelSession)
        self.mock_session.alice_model = "gpt-4"
        self.mock_session.bob_model = "claude-3"
        self.mock_session.alice_endpoint = "https://api.openai.com"
        self.mock_session.bob_endpoint = "https://api.anthropic.com"
        self.mock_session.system_prompt = "Have a conversation."
        self.mock_session.max_chars = 10000
        self.mock_session.max_turns = 30
        self.mock_session.html_filename = "test_output.html"
        self.mock_session.full_conversation_log = []
        self.mock_session._render_markdown_to_html = Mock(
            side_effect=lambda x: f"<p>{escape(x)}</p>"
        )

    def test_no_html_filename(self):
        """Test function returns early when no HTML filename is set"""
        self.mock_session.html_filename = None
        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            mock_file.assert_not_called()

    def test_shared_endpoint_and_model(self):
        """Test HTML generation when both endpoint and model are shared"""
        self.mock_session.alice_model = "gpt-4"
        self.mock_session.bob_model = "gpt-4"
        self.mock_session.alice_endpoint = "https://api.openai.com"
        self.mock_session.bob_endpoint = "https://api.openai.com"

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn("Shared Model", written_content)
            self.assertIn("Shared Endpoint", written_content)
            self.assertNotIn("Alice Model", written_content)
            self.assertNotIn("Bob Model", written_content)

    def test_shared_endpoint_only(self):
        """Test HTML generation when only endpoint is shared"""
        self.mock_session.alice_endpoint = "https://api.openai.com"
        self.mock_session.bob_endpoint = "https://api.openai.com"

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn("Alice Model", written_content)
            self.assertIn("Bob Model", written_content)
            self.assertIn("Shared Endpoint", written_content)

    def test_conversation_with_messages(self):
        """Test HTML generation with actual conversation messages"""
        self.mock_session.full_conversation_log = [
            {
                "speaker": "Alice",
                "model": "gpt-4",
                "turn": 1,
                "content": "Hello Bob!",
                "char_count": 10,
            },
            {
                "speaker": "Bob",
                "model": "claude-3",
                "turn": 2,
                "content": "Hi Alice! How are you?",
                "char_count": 22,
            },
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn('<div class="message alice">', written_content)
            self.assertIn('<div class="message bob">', written_content)
            self.assertIn("Turn 1", written_content)
            self.assertIn("Turn 2", written_content)
            self.assertIn("10 chars", written_content)
            self.assertIn("22 chars", written_content)
            self.assertIn(
                'Total Characters</div>\n            <div class="metadata-value">32</div>',
                written_content,
            )

    def test_truncated_message(self):
        """Test HTML generation with truncated message"""
        self.mock_session.full_conversation_log = [
            {
                "speaker": "Alice",
                "model": "gpt-4",
                "turn": 1,
                "content": "A" * 10000,
                "char_count": 10000,
            }
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn("Response truncated at 10,000 characters", written_content)

    def test_filtered_message(self):
        """Test HTML generation with filtered message"""
        self.mock_session.full_conversation_log = [
            {
                "speaker": "Alice",
                "model": "gpt-4",
                "turn": 1,
                "content": "Hello!",
                "char_count": 6,
                "was_filtered": True,
            }
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn(
                "Note: Thinking tags were filtered from this message", written_content
            )

    def test_special_characters_escaping(self):
        """Test that special characters are properly escaped"""
        self.mock_session.alice_model = 'model<>&"'
        self.mock_session.bob_model = "model'test"
        self.mock_session.full_conversation_log = [
            {
                "speaker": "Alice<>",
                "model": 'model<>&"',
                "turn": 1,
                "content": "Test & <script>alert('xss')</script>",
                "char_count": 37,
            }
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn("model&lt;&gt;&amp;&quot;", written_content)
            self.assertIn("Alice&lt;&gt;", written_content)
            # Content is handled by _render_markdown_to_html mock

    def test_large_numbers_formatting(self):
        """Test that large numbers are formatted with commas"""
        self.mock_session.max_chars = 1000000
        self.mock_session.full_conversation_log = [
            {
                "speaker": "Alice",
                "model": "gpt-4",
                "turn": 1,
                "content": "Test",
                "char_count": 999999,
            }
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn("1,000,000", written_content)  # max_chars
            self.assertIn("999,999", written_content)  # char_count and total

    def test_missing_char_count(self):
        """Test handling of messages without char_count"""
        self.mock_session.full_conversation_log = [
            {
                "speaker": "Alice",
                "model": "gpt-4",
                "turn": 1,
                "content": "Hello!",
                # char_count missing
            }
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            save_html_checkpoint(self.mock_session)
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            self.assertIn("6 chars", written_content)  # len("Hello!")

    def test_file_write_error(self):
        """Test that file write errors are propagated"""
        with patch("builtins.open", side_effect=IOError("Write failed")):
            with self.assertRaises(IOError):
                save_html_checkpoint(self.mock_session)


if __name__ == "__main__":
    unittest.main()
