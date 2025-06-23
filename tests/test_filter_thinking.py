#!/usr/bin/env python3

import unittest
from resonant_chat.utils import filter_thinking_tags


class TestFilterThinkingTags(unittest.TestCase):
    """Test cases for filter_thinking_tags function"""

    def test_no_thinking_tags(self):
        """Test content without thinking tags remains unchanged"""
        content = "This is regular content without any thinking tags."
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, content)
        self.assertEqual(original, content)

    def test_single_think_tag(self):
        """Test removal of single <think> tag"""
        content = "Before <think>This is private thinking</think> After"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Before After")
        self.assertEqual(original, content)

    def test_single_thinking_tag(self):
        """Test removal of single <thinking> tag"""
        content = "Start <thinking>Internal thoughts here</thinking> End"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Start End")
        self.assertEqual(original, content)

    def test_multiple_tags(self):
        """Test removal of multiple thinking tags"""
        content = "A <think>thought 1</think> B <thinking>thought 2</thinking> C"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "A B C")
        self.assertEqual(original, content)

    def test_nested_content(self):
        """Test thinking tags with complex nested content"""
        content = "Before <thinking>This has\n\nmultiple lines\nand formatting</thinking> After"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Before After")
        self.assertEqual(original, content)

    def test_case_insensitive(self):
        """Test that tag matching is case-insensitive"""
        content = (
            "Test <THINK>uppercase</THINK> and <ThInKiNg>mixed case</ThInKiNg> tags"
        )
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Test and tags")
        self.assertEqual(original, content)

    def test_unclosed_tags(self):
        """Test handling of unclosed tags"""
        content = "Test <think>unclosed content"
        filtered, original = filter_thinking_tags(content)
        # Should not remove unclosed tags
        self.assertEqual(filtered, content)
        self.assertEqual(original, content)

    def test_empty_tags(self):
        """Test removal of empty thinking tags"""
        content = "Before <think></think> Middle <thinking></thinking> After"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Before Middle After")
        self.assertEqual(original, content)

    def test_whitespace_cleanup(self):
        """Test that multiple spaces are cleaned up"""
        content = "Word1    <think>removed</think>    Word2"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Word1 Word2")
        self.assertEqual(original, content)

    def test_newline_cleanup(self):
        """Test that multiple newlines are cleaned up"""
        content = "Line1\n\n\n<thinking>removed</thinking>\n\n\n\nLine2"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Line1\n\nLine2")
        self.assertEqual(original, content)

    def test_strip_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped"""
        content = "  \n  <think>removed</think> Content <thinking>also removed</thinking>  \n  "
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Content")
        self.assertEqual(original, content)

    def test_tags_at_boundaries(self):
        """Test tags at the beginning and end of content"""
        content = "<think>Start thinking</think>Middle<thinking>End thinking</thinking>"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Middle")
        self.assertEqual(original, content)

    def test_only_thinking_tags(self):
        """Test content that is only thinking tags"""
        content = "<think>Only thinking here</think>"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "")
        self.assertEqual(original, content)

    def test_special_characters_in_tags(self):
        """Test thinking tags containing special regex characters"""
        content = "Before <think>Content with $pecial ch@rs & symbols!</think> After"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Before After")
        self.assertEqual(original, content)

    def test_very_long_content(self):
        """Test performance with very long thinking sections"""
        long_thinking = "x" * 10000
        content = f"Start <thinking>{long_thinking}</thinking> End"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Start End")
        self.assertEqual(original, content)

    def test_html_like_content_in_tags(self):
        """Test thinking tags containing HTML-like content"""
        content = "Text <think>This has <b>bold</b> and <i>italic</i> tags</think> More"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Text More")
        self.assertEqual(original, content)

    def test_adjacent_tags(self):
        """Test adjacent thinking tags with no content between"""
        content = "Start <think>A</think><thinking>B</thinking> End"
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Start End")
        self.assertEqual(original, content)

    def test_unicode_content(self):
        """Test thinking tags with unicode content"""
        content = (
            "Hello <think>思考中 🤔</think> World <thinking>考える 🧠</thinking> !"
        )
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "Hello World !")
        self.assertEqual(original, content)

    def test_empty_input(self):
        """Test empty string input"""
        content = ""
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "")
        self.assertEqual(original, "")

    def test_whitespace_only_input(self):
        """Test whitespace-only input"""
        content = "   \n\n   \t  "
        filtered, original = filter_thinking_tags(content)
        self.assertEqual(filtered, "")
        self.assertEqual(original, content)


if __name__ == "__main__":
    unittest.main()
