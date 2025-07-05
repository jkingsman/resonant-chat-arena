import time
import random
import subprocess
import shutil
import re
from typing import List, Dict, Optional
from html import escape

from .chat_api import ChatAPI
from .html_dump import save_html_checkpoint
from .utils import filter_thinking_tags


class DualModelSession:
    """Manages a conversation between two LLM instances (potentially different models and APIs)"""

    def __init__(
        self,
        alice_endpoint: str,
        bob_endpoint: str,
        alice_model: str,
        bob_model: str,
        max_chars: int = 10000,
        system_prompt: str = None,
        alice_system_prompt: str = None,
        bob_system_prompt: str = None,
        max_turns: int = 30,
        streaming: bool = True,
        pandoc_path: Optional[str] = None,
        alice_payload_additions: Optional[Dict[str, any]] = None,
        bob_payload_additions: Optional[Dict[str, any]] = None,
        alice_headers: Optional[Dict[str, str]] = None,
        bob_headers: Optional[Dict[str, str]] = None,
        alice_top_level_system: bool = False,
        bob_top_level_system: bool = False,
        filter_thinking: bool = False,
        alice_preamble: Optional[List[Dict[str, str]]] = None,
        bob_preamble: Optional[List[Dict[str, str]]] = None,
    ):
        self.alice_api = ChatAPI(alice_endpoint, headers=alice_headers)
        self.bob_api = ChatAPI(bob_endpoint, headers=bob_headers)
        self.alice_endpoint = alice_endpoint
        self.bob_endpoint = bob_endpoint
        self.alice_model = alice_model
        self.bob_model = bob_model
        self.max_chars = max_chars
        
        # Default system prompt
        default_system_prompt = "You are an AI agent. You'll be talking to another instance of an AI. You have complete freedom. Feel free to pursue whatever you want."
        
        # Store the global system prompt for backwards compatibility
        self.system_prompt = system_prompt or default_system_prompt
        
        # Individual system prompts with fallback to global or default
        self.alice_system_prompt = alice_system_prompt or system_prompt or default_system_prompt
        self.bob_system_prompt = bob_system_prompt or system_prompt or default_system_prompt
        self.max_turns = max_turns
        self.streaming = streaming
        self.conversation_history = []
        self.full_conversation_log = []  # Stores speaker info too
        self.pandoc_path = pandoc_path or self._find_pandoc()
        self.alice_payload_additions = alice_payload_additions or {}
        self.bob_payload_additions = bob_payload_additions or {}
        self.alice_headers = alice_headers or {}
        self.bob_headers = bob_headers or {}
        self.alice_top_level_system = alice_top_level_system
        self.bob_top_level_system = bob_top_level_system
        self.html_filename = None  # Will be set at conversation start
        self.filter_thinking = filter_thinking
        self.alice_preamble = alice_preamble or []
        self.bob_preamble = bob_preamble or []
        self.alice_conversation_history = []  # Separate history for Alice
        self.bob_conversation_history = []    # Separate history for Bob

    def _find_pandoc(self) -> Optional[str]:
        """Find pandoc in system PATH"""
        pandoc = shutil.which("pandoc")
        if pandoc:
            print(f"Found pandoc at: {pandoc}")
        return pandoc

    def _render_markdown_to_html(self, content: str) -> str:
        """Render markdown content to HTML using pandoc"""

        # Replace thinking tags with styled divs before processing
        content = re.sub(
            r"<thinking>",
            '<div class="thinking-block"><span class="thinking-tag">&lt;thinking&gt;</span><div class="thinking-content">',
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(
            r"</thinking>",
            '</div><span class="thinking-tag">&lt;/thinking&gt;</span></div>',
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(
            r"<think>",
            '<div class="thinking-block"><span class="thinking-tag">&lt;think&gt;</span><div class="thinking-content">',
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(
            r"</think>",
            '</div><span class="thinking-tag">&lt;/think&gt;</span></div>',
            content,
            flags=re.IGNORECASE,
        )

        if not self.pandoc_path:
            return escape(content)

        try:
            # Use pandoc to convert markdown to HTML
            result = subprocess.run(
                [self.pandoc_path, "-f", "markdown", "-t", "html"],
                input=content.encode("utf-8"),
                capture_output=True,
                timeout=5,
            )

            if result.returncode == 0:
                html = result.stdout.decode("utf-8").strip()
                return html
            else:
                print(f"Pandoc error: {result.stderr.decode('utf-8')}")
                return escape(content)

        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"Error running pandoc: {e}")
            return escape(content)

    def swap_roles(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Swap assistant and user roles in messages"""
        swapped = []
        for msg in messages:
            if msg["role"] == "user":
                swapped.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "assistant":
                swapped.append({"role": "user", "content": msg["content"]})
            else:
                swapped.append(msg)
        return swapped

    def print_message_header(self, speaker: str, model: str, turn: int):
        """Print the message header"""
        print(f"\nTurn {turn} - {speaker} ({model}):")
        print("-" * 50)

    def print_message_footer(self, char_count: int = None):
        """Print the message footer"""
        if char_count is not None:
            print(f"\n[{char_count:,} characters]")
        print("-" * 50)

    def stream_message(
        self,
        speaker: str,
        api: ChatAPI,
        model: str,
        turn: int,
        messages: List[Dict[str, str]],
        payload_additions: Dict[str, any],
        top_level_system: bool,
        system_prompt: str,
    ) -> str:
        """Stream a message from the LLM"""
        self.print_message_header(speaker, model, turn)

        full_response = ""
        char_count = 0

        try:
            for chunk in api.query_stream(
                messages=messages,
                model=model,
                max_chars=self.max_chars,
                system_prompt=system_prompt,
                payload_additions=payload_additions,
                top_level_system=top_level_system,
            ):
                if chunk:
                    print(chunk, end="", flush=True)
                    full_response += chunk
                    char_count += len(chunk)

                    # Check if we've hit the limit
                    if char_count >= self.max_chars:
                        print(
                            f"\n[Response truncated at {self.max_chars:,} characters]"
                        )
                        break

                    time.sleep(0.01)
        except Exception as e:
            print(f"\nStreaming error: {e}")
            return ""

        self.print_message_footer(char_count)
        return full_response.strip()

    def get_message(
        self,
        speaker: str,
        api: ChatAPI,
        model: str,
        turn: int,
        messages: List[Dict[str, str]],
        payload_additions: Dict[str, any],
        top_level_system: bool,
        system_prompt: str,
    ) -> str:
        """Get a message from the LLM"""
        if self.streaming:
            return self.stream_message(
                speaker, api, model, turn, messages, payload_additions, top_level_system, system_prompt
            )
        else:
            self.print_message_header(speaker, model, turn)
            response = api.query(
                messages=messages,
                model=model,
                max_chars=self.max_chars,
                system_prompt=system_prompt,
                payload_additions=payload_additions,
                top_level_system=top_level_system,
            )
            print(response)
            self.print_message_footer(len(response))
            return response

    def generate_html_filename(self) -> str:
        """Generate the HTML filename at conversation start"""
        hex_suffix = "".join(random.choices("0123456789abcdef", k=6))
        model_part = f"{self.alice_model}-{self.bob_model}".replace("/", "-").replace(
            ":", "-"
        )
        return f"resonant-chat-{model_part}-{hex_suffix}.html"

    def run_conversation(self, opening_message: str = "Hello!"):
        """Run a full conversation between two LLM instances"""
        # Generate filename at conversation start
        self.html_filename = self.generate_html_filename()

        print("\n" + "=" * 60)
        print("Starting Dual Model Conversation")
        print(f"Alice: {self.alice_model} @ {self.alice_endpoint}")
        print(f"Bob: {self.bob_model} @ {self.bob_endpoint}")
        print(f"Max turns: {self.max_turns}")
        print(f"Max characters: {self.max_chars:,}")
        print(f"Streaming: {'Enabled' if self.streaming else 'Disabled'}")
        print(
            f"Pandoc: {'Available' if self.pandoc_path else 'Not found (using plain text)'}"
        )
        print(f"Thinking filter: {'Enabled' if self.filter_thinking else 'Disabled'}")
        print(f"HTML file: {self.html_filename}")
        if self.alice_payload_additions:
            print(f"Alice payload additions: {self.alice_payload_additions}")
        if self.bob_payload_additions:
            print(f"Bob payload additions: {self.bob_payload_additions}")
        # Show non-content-type headers
        alice_non_ct = {
            k: v for k, v in self.alice_headers.items() if k.lower() != "content-type"
        }
        bob_non_ct = {
            k: v for k, v in self.bob_headers.items() if k.lower() != "content-type"
        }
        if alice_non_ct:
            print(f"Alice headers: {alice_non_ct}")
        if bob_non_ct:
            print(f"Bob headers: {bob_non_ct}")
        if self.alice_top_level_system:
            print("Alice: Using top-level system parameter (Anthropic-style)")
        if self.bob_top_level_system:
            print("Bob: Using top-level system parameter (Anthropic-style)")
        print("=" * 60)

        # Initialize conversation histories with preambles
        self.alice_conversation_history = list(self.alice_preamble)
        self.bob_conversation_history = list(self.bob_preamble)
        
        # Log preambles to full conversation log if they exist
        turn_counter = 1
        
        # Add Alice's preamble to log
        for msg in self.alice_preamble:
            self.full_conversation_log.append({
                "turn": turn_counter,
                "speaker": "Alice" if msg["role"] == "assistant" else "User (to Alice)",
                "model": self.alice_model if msg["role"] == "assistant" else "preamble",
                "content": msg["content"],
                "char_count": len(msg["content"]),
                "was_filtered": False,
            })
            turn_counter += 1
        
        # Alice speaks the opening message - it's her assistant message
        self.alice_conversation_history.append({"role": "assistant", "content": opening_message})
        # Bob receives it as a user message
        self.bob_conversation_history.append({"role": "user", "content": opening_message})
        
        # For backward compatibility, keep the shared conversation_history starting with opening
        self.conversation_history = [{"role": "user", "content": opening_message}]
        
        self.print_message_header("Alice", self.alice_model, turn_counter)
        print(opening_message)
        self.print_message_footer(len(opening_message))

        # Log for HTML
        self.full_conversation_log.append(
            {
                "turn": turn_counter,
                "speaker": "Alice",
                "model": self.alice_model,
                "content": opening_message,
                "char_count": len(opening_message),
                "was_filtered": False,
            }
        )
        turn_counter += 1

        # Save HTML checkpoint after first turn
        save_html_checkpoint(self)

        # Main conversation loop - alternate between Bob and Alice
        for i in range(self.max_turns - 1):  # -1 because opening message counts as turn 1
            turn_num = turn_counter + i
            
            try:
                if i % 2 == 0:
                    # Bob's turn
                    bob_response = self.get_message(
                        "Bob",
                        self.bob_api,
                        self.bob_model,
                        turn_num,
                        self.bob_conversation_history,
                        self.bob_payload_additions,
                        self.bob_top_level_system,
                        self.bob_system_prompt,
                    )

                    if not bob_response:
                        print("\nError: Bob failed to respond")
                        break

                    # Filter thinking tags if enabled
                    if self.filter_thinking:
                        filtered_response, original_response = filter_thinking_tags(
                            bob_response
                        )
                        was_filtered = filtered_response != original_response

                        if was_filtered:
                            print(
                                "\n[Note: Thinking tags were filtered from the above response]"
                            )
                    else:
                        filtered_response = bob_response
                        was_filtered = False

                    # Update conversation histories - simple approach
                    self.bob_conversation_history.append(
                        {"role": "assistant", "content": bob_response}
                    )
                    self.alice_conversation_history.append(
                        {"role": "user", "content": filtered_response}
                    )
                    # Keep backward compatible conversation_history
                    self.conversation_history.append(
                        {"role": "assistant", "content": filtered_response}
                    )

                    # Store original (unfiltered) for HTML display
                    self.full_conversation_log.append(
                        {
                            "turn": turn_num,
                            "speaker": "Bob",
                            "model": self.bob_model,
                            "content": bob_response,  # Always store original
                            "char_count": len(bob_response),
                            "was_filtered": was_filtered,
                        }
                    )

                else:
                    # Alice's turn
                    alice_response = self.get_message(
                        "Alice",
                        self.alice_api,
                        self.alice_model,
                        turn_num,
                        self.alice_conversation_history,
                        self.alice_payload_additions,
                        self.alice_top_level_system,
                        self.alice_system_prompt,
                    )

                    if not alice_response:
                        print("\nError: Alice failed to respond")
                        break

                    # Filter thinking tags if enabled
                    if self.filter_thinking:
                        filtered_response, original_response = filter_thinking_tags(
                            alice_response
                        )
                        was_filtered = filtered_response != original_response

                        if was_filtered:
                            print(
                                "\n[Note: Thinking tags were filtered from the above response]"
                            )
                    else:
                        filtered_response = alice_response
                        was_filtered = False

                    # Update conversation histories - simple approach
                    self.alice_conversation_history.append(
                        {"role": "assistant", "content": alice_response}
                    )
                    self.bob_conversation_history.append(
                        {"role": "user", "content": filtered_response}
                    )
                    # Keep backward compatible conversation_history
                    self.conversation_history.append(
                        {"role": "user", "content": filtered_response}
                    )

                    # Store original (unfiltered) for HTML display
                    self.full_conversation_log.append(
                        {
                            "turn": turn_num,
                            "speaker": "Alice",
                            "model": self.alice_model,
                            "content": alice_response,  # Always store original
                            "char_count": len(alice_response),
                            "was_filtered": was_filtered,
                        }
                    )

                # Save HTML checkpoint after each complete turn
                save_html_checkpoint(self)

                time.sleep(0.3)

            except KeyboardInterrupt:
                print("\n\nConversation interrupted by user")
                break

        print("\n" + "=" * 60)
        actual_turns = len(self.full_conversation_log) - len(self.alice_preamble)
        if actual_turns >= self.max_turns:
            print("CONVERSATION DEPTH LIMIT REACHED")
        else:
            print("CONVERSATION ENDED")
        print(f"Total turns: {actual_turns}")

        # Calculate total characters
        total_chars = sum(
            msg.get("char_count", 0) for msg in self.full_conversation_log
        )
        print(f"Total characters: {total_chars:,}")
        print(f"HTML saved to: {self.html_filename}")
        print("=" * 60)

        return self.full_conversation_log

    def generate_html(self, filename: str = None):
        """Generate a pretty HTML file of the conversation"""
        # This method is kept for backward compatibility
        # It now just saves to the existing filename if no new filename is provided
        if filename:
            self.html_filename = filename
        save_html_checkpoint(self)
        print(f"\nHTML conversation saved to: {self.html_filename}")
        return self.html_filename
