#!/usr/bin/env python3

from .dual_model_session import DualModelSession
from .utils import parse_headers, parse_payload_additions


def chat():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Dual Model Chat Tool with HTML Output"
    )

    # Global defaults
    parser.add_argument("--endpoint", help="Default API endpoint for both models")
    parser.add_argument("--model", help="Default model for both Alice and Bob")

    # Individual endpoints
    parser.add_argument(
        "--alice-endpoint", help="API endpoint for Alice (overrides --endpoint)"
    )
    parser.add_argument(
        "--bob-endpoint", help="API endpoint for Bob (overrides --endpoint)"
    )

    # Individual models
    parser.add_argument("--alice-model", help="Model for Alice (overrides --model)")
    parser.add_argument("--bob-model", help="Model for Bob (overrides --model)")

    # Headers
    parser.add_argument(
        "--headers",
        help='Default JSON headers for both models (e.g., \'{"Authorization": "Bearer KEY"}\')',
    )
    parser.add_argument(
        "--alice-headers", help="JSON headers for Alice only (overrides --headers)"
    )
    parser.add_argument(
        "--bob-headers", help="JSON headers for Bob only (overrides --headers)"
    )

    # System prompt handling
    parser.add_argument(
        "--top-level-system",
        action="store_true",
        help="Use top-level system parameter for both models (Anthropic-style)",
    )
    parser.add_argument(
        "--alice-top-level-system",
        action="store_true",
        help="Use top-level system parameter for Alice only",
    )
    parser.add_argument(
        "--bob-top-level-system",
        action="store_true",
        help="Use top-level system parameter for Bob only",
    )

    # Payload additions
    parser.add_argument(
        "--payload",
        help="Default JSON payload additions for both models (e.g., '{\"temperature\": 0.7}')",
    )
    parser.add_argument("--alice-payload", help="JSON payload additions for Alice only")
    parser.add_argument("--bob-payload", help="JSON payload additions for Bob only")

    # Conversation settings
    parser.add_argument(
        "--max-chars",
        type=int,
        default=10000,
        help="Maximum characters per response (default: 10,000)",
    )
    parser.add_argument(
        "--max-turns", type=int, default=30, help="Maximum number of turns"
    )
    parser.add_argument("--opening", default="Hello!", help="Opening message")
    parser.add_argument("--system-prompt", help="Custom system prompt")

    # Output options
    parser.add_argument(
        "--no-stream", action="store_true", help="Disable streaming mode"
    )
    parser.add_argument("--no-html", action="store_true", help="Skip HTML generation")
    parser.add_argument(
        "--pandoc-path",
        help="Path to pandoc executable (auto-detected if not specified)",
    )

    # Thinking filter option
    parser.add_argument(
        "--filter-thinking",
        action="store_true",
        help="Filter out content between <think></think> or <thinking></thinking> tags from the partner's view (still shown in logs)",
    )

    args = parser.parse_args()

    # Resolve endpoints and models
    if not args.endpoint and (not args.alice_endpoint or not args.bob_endpoint):
        parser.error(
            "Must specify either --endpoint or both --alice-endpoint and --bob-endpoint"
        )

    if not args.model and (not args.alice_model or not args.bob_model):
        parser.error(
            "Must specify either --model or both --alice-model and --bob-model"
        )

    alice_endpoint = args.alice_endpoint or args.endpoint
    bob_endpoint = args.bob_endpoint or args.endpoint
    alice_model = args.alice_model or args.model
    bob_model = args.bob_model or args.model

    # Parse headers
    default_headers = parse_headers(args.headers) if args.headers else {}
    alice_headers = (
        parse_headers(args.alice_headers) if args.alice_headers else default_headers
    )
    bob_headers = (
        parse_headers(args.bob_headers) if args.bob_headers else default_headers
    )

    # Parse payload additions
    default_payload = parse_payload_additions(args.payload) if args.payload else {}
    alice_payload = (
        parse_payload_additions(args.alice_payload)
        if args.alice_payload
        else default_payload
    )
    bob_payload = (
        parse_payload_additions(args.bob_payload)
        if args.bob_payload
        else default_payload
    )

    # Determine top-level system settings
    alice_top_level = args.alice_top_level_system or args.top_level_system
    bob_top_level = args.bob_top_level_system or args.top_level_system

    # Create and run session
    session = DualModelSession(
        alice_endpoint=alice_endpoint,
        bob_endpoint=bob_endpoint,
        alice_model=alice_model,
        bob_model=bob_model,
        max_chars=args.max_chars,
        system_prompt=args.system_prompt,
        max_turns=args.max_turns,
        streaming=not args.no_stream,
        pandoc_path=args.pandoc_path,
        alice_payload_additions=alice_payload,
        bob_payload_additions=bob_payload,
        alice_headers=alice_headers,
        bob_headers=bob_headers,
        alice_top_level_system=alice_top_level,
        bob_top_level_system=bob_top_level,
        filter_thinking=args.filter_thinking,
    )

    try:
        session.run_conversation(opening_message=args.opening)

        if not args.no_html:
            # Final save is already done in run_conversation
            pass

    except KeyboardInterrupt:
        print("\n\nConversation interrupted by user")
        # HTML checkpoint already saved after each turn
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        # HTML checkpoint already saved after each turn
