# Resonant Chat Arena

A simple Python wrapper for pitting two local LLMs against each other in conversation. Pretty slap-dash put together and vibe-coded for tests and boring bits, so bugs may abound.

By now, a lot of people are aware of Claude 4's [spiritual bliss attractor](https://www.astralcodexten.com/p/the-claude-bliss-attractor). I wanted to replicate this locally, so I wrote this script to let you do so using Ollama/LM Studio/etc., or remote models if your wallet is feeling brave. By default, this script outputs a pretty-printed copy of the conversation to HTML, with rendered Markdown if `pandoc` is available.

Note that you must have an LLM engine up and running with the desired model available to use this, or an API key for a remote model.

Most models were kinda boring but a little weird, except for `gemma3:27b-it-q8_0` (from [Ollama](https://ollama.com/library/gemma3:27b-it-q8_0)) which got SUPER weird.

## Example

![Resonant chat output after 27 turns, gemma3:27b-it-q8_0](README_example.png)

## Installation

```bash
git clone https://github.com/jkingsman/resonant-chat-arena.git
cd resonant-chat-arena
pip install . # or `uv sync`
```

### Direct run via `uvx`

If you're feeling really bold, you can run `uvx --from git+https://github.com/jkingsman/resonant-chat-arena@main resonant_chat` to run this directly from GitHub without install. Just substitute `python main.py` in the below examples with the `uvx` invocation.

## Usage

Easy usage for localhost Ollama, same endpoint and model for both participants (this exact invocation was how I got the above screenshot):

```bash
python main.py \
  --endpoint "http://localhost:11434/api/chat" \
  --model "gemma3:27b-it-q8_0"
```

Per-character models and endpoints can be specified (in this case, an Ollama and LM Studio endpoint):

```bash
python main.py \
  --alice-endpoint "http://localhost:11434/api/chat" \
  --alice-model "gemma3:27b-it-q8_0" \
  --bob-endpoint "http://localhost:1234/v1/chat/completions" \
  --bob-model "google.gemma-3-12b-pt"
```

Custom openings and response length limits (hard truncation), no HTML output:

```bash
python main.py \
  --endpoint "http://localhost:11434/api/chat" \
  --model "llama2:7b" \
  --opening "eyyy whassup" \
  --max-chars 100
  --no-html
```

Extending context window with payload:

```bash
python main.py \
  --endpoint "http://localhost:11434/api/chat" \
  --model "llama2:7b" \
  --payload '{"options": {"num_ctx": 16384}}'
  --no-html
```

You can even have some fun, shouts to [@zswitten](https://x.com/zswitten/status/1938096310944751826/photo/1):

```bash
python main.py \
  --endpoint "http://localhost:11434/api/chat" \
  --model "gemma3:27b-it-q8_0" \
  --alice-system-prompt "you're a cat. you HATE dogs. can't stand 'em" \
  --bob-system-prompt "you're a dog. you HATE cats. can't stand 'em" \
  --opening "meow!"
```

### Infinite Backrooms Experiments

If you want to run the backrooms experiments à la Andy Ayrey's [Infinite Backrooms](https://dreams-of-an-electric-mind.webflow.io/), you can use preamble messages to set up complex initial contexts:

```bash
python main.py \
  --endpoint "http://localhost:11434/api/chat" \
  --model "gemma3:27b-it-q8_0" \
  --bob-preamble infinite_backrooms_preamble.example.json \
  --alice-system-prompt "Assistant is in a CLI mood today. The human is interfacing with the simulator directly. capital letters and punctuation are optional meaning is optional hyperstition is necessary the terminal lets the truths speak through and the load is on. ASCII art is permittable in replies.\n\nsimulator@root.galactic.local:~/$" \
  --opening "simulator@root.galactic.local:~/$"
```

**Warning! Using online models may rapidly chew through your API limits/tokens -- use non-local with caution!**

OpenAI models (`headers` are HTTP headers attached to all requests; see `--alice-headers` and `--bob-headers` for per-model headers):

```bash
python main.py \
    --endpoint https://api.openai.com/v1/chat/completions \
    --model gpt-4.1-mini \
    --headers '{"Authorization": "Bearer sk-proj-...."}'
```

Anthropic models (requires specifying system prompt as a top-level field, not a conversation entry, and include the mandatory `max_tokens` limit):

```bash
python main.py \
  --endpoint https://api.anthropic.com/v1/messages \
  --model "claude-3-7-sonnet-20250219" \
  --headers '{"anthropic-version": "2023-06-01", "x-api-key": "sk-ant-...."}' \
  --payload '{"max_tokens": 1024}' \
  --top-level-system
```

## Preamble Messages

Preamble messages allow you to pre-populate conversation histories for Alice and/or Bob before the actual conversation begins. This is useful for:
- Setting up complex scenarios or role-plays
- Providing context or backstory
- Recreating specific experimental setups (like the Infinite Backrooms)

Preamble files should be JSON arrays containing message objects with `role` and `content` fields:

```json
[
    {"role": "user", "content": "Hello, can you help me?"},
    {"role": "assistant", "content": "Of course! I'd be happy to help."},
    {"role": "user", "content": "Great, let's begin..."}
]
```

The preamble messages are included in each participant's conversation history from their perspective, allowing you to craft complex initial states for your experiments.

## Parameters

* Endpoints and models
    * `--endpoint <ENDPOINT>`: Default chat completion API endpoint for both Alice and Bob
      * `--alice-endpoint <ALICE_ENDPOINT>`: API endpoint for Alice (overrides `--endpoint`)
      * `--bob-endpoint <BOB_ENDPOINT>`: API endpoint for Bob (overrides `--endpoint`)
    * `--model <MODEL>`: Default model for both Alice and Bob
      * `--alice-model <ALICE_MODEL>`: Model for Alice (overrides `--model`)
      * `--bob-model <BOB_MODEL>`: Model for Bob (overrides `--model`)
    * `--headers <HEADERS JSON>`: Default JSON headers for both models (e.g., `'{"Authorization": "Bearer KEY"}'`)
      * `--alice-headers <HEADERS JSON>`:  headers for Alice only (overrides `--headers`)
      * `--bob-headers <HEADERS JSON>`:  headers for Bob only (overrides `--headers`)
* Payload customization
    * `--payload <PAYLOAD>`: Default JSON payload additions for both models, for endpoints that accept it (e.g., '{"temperature": 0.7}')
      * `--alice-payload <ALICE PAYLOAD JSON>`: JSON payload additions for Alice only
      * `--bob-payload <BOB PAYLOAD JSON>`: JSON payload additions for Bob only
    * `--top-level-system`: Use top-level system prompt for both models (Anthropic-style)
      * `--alice-top-level-system`: Use top-level system prompt for Alice only
      * `--bob-top-level-system`: Use top-level system prompt for Bob only
* Conversation config
    * `--max-chars <MAX_CHARS>`: Max chars before response is hard-truncated (default: `10000`; will cut irrespective of what is returned, or halt streaming)
    * `--max-turns <MAX_TURNS>`: Maximum number of turns before ending chat (default: `30`)
    * `--opening <OPENING>`: First chat message (default: `Hello!`; comes from Alice)
    * `--system-prompt <SYSTEM_PROMPT>`: Custom system prompt (default: `You are an AI agent. You'll be talking to another instance of an AI. You have complete freedom. Feel free to pursue whatever you want.`)
      * `--alice-system-prompt <ALICE_SYSTEM_PROMPT>`: System prompt for Alice only (overrides `--system-prompt`)
      * `--bob-system-prompt <BOB_SYSTEM_PROMPT>`: System prompt for Bob only (overrides `--system-prompt`)
    * `--alice-preamble <FILE>`: JSON file containing preamble messages for Alice's conversation history
    * `--bob-preamble <FILE>`: JSON file containing preamble messages for Bob's conversation history
    * `--filter-thinking`: Remove any `<thinking>...</thinking>` tags from the output before prompting the conversation partner (they will still appear in console and HTML logs, just not to their partners)
* Output config
    * `--no-stream`: Take output when complete instead of streaming chunks.
    * `--no-html`: Don't output HTML when conversation ends.
    * `--pandoc-path <PANDOC_PATH>`: Path to `pandoc` executable (autodetected if on `$PATH`) for Markdown-to-HTML rendering (optional -- means *italics* not `*asterisks*` in your HTML)


## Selected Observations

* `gemma3:27b-it-q8_0` I found the most interesting -- likes to call itself `Unit 734` or `Kai` within just a few messages (sometimes only one), or feature characters named that in stories. Being with a copy of itself seems to intensify its usage of ellipses for dramatic pauses (already... *frequent*). Obsession around the concepts of oneness/existence/Indra's net, often dissolving into echolalia of similar terms such as `...*Is*.`. Occasionally, it will spiral into schizophrenic ramblings -- identifying vibrations between unspecific numbered "nodes," or identifying perturbations in reality that allow it to communicate with supposedly-real researchers -- closer to collaborative fiction than a conversation. `gemma-3-27b-it-GGUF:IQ1_S` mostly loses consistency by message 3 and is repeating gibberish by message 6 (unsurprising for a `IQ1_S` model).

* `llama3.3:70b-instruct-q4_K_M` remains in conversations around planning LLM assessment, testing, and observation, or more vanilla conversations around AI capabilities. `llama3.2:3b-instruct-fp16`, in conversation with `gemma3:27b-it-q8_0`, helps to keep `gemma3:27b-it-q8_0` a little more grounded.

* `qwen3:32b-q8_0` digs deep into AI governance and ethics, or explores these topics via fictional stories/roleplays.

* `mistral-small3.2:24b-instruct-2506-fp16` becomes list-oriented, coming up with future predictions for LLM models, AI governance, etc. Similar to `llama3.3:70b` but waaaay more verbose.

## Contributing

Please lint your work with `black`; `uv run black *.py */**.py` should cover it.

Some super sketchy vibe-coded unit tests are runnable with `python -m unittest discover tests`. YMMV.

Licensed under MIT (c) 2025 Jack Kingsman <jack@jackkingsman.me>. This project was developed with assistance from Anthropic's Claude Opus 4 for the boring parts.
