from html import escape


def save_html_checkpoint(dual_model_session):
    """Save the current conversation state to HTML"""
    if not dual_model_session.html_filename:
        return

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resonant Chat - {escape(dual_model_session.alice_model)} & {escape(dual_model_session.bob_model)}</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
        color: #333;
    }}

    .header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}

    .header h1 {{
        margin: 0 0 10px 0;
        font-size: 2.5em;
    }}

    .metadata {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }}

    .metadata-item {{
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
    }}

    .metadata-label {{
        font-size: 0.9em;
        opacity: 0.8;
    }}

    .metadata-value {{
        font-size: 1.1em;
        font-weight: 600;
        text-overflow: ellipsis;
        overflow: hidden;
    }}

    .system-prompt {{
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #ccc;
    }}

    .system-prompt-header {{
        font-size: 0.9em;
        font-weight: 600;
        color: #666;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .system-prompt-content {{
        color: #666;
        font-size: 0.95em;
        line-height: 1.5;
        white-space: pre-wrap;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    }}

    .conversation {{
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}

    .message {{
        margin-bottom: 25px;
        padding: 20px;
        border-radius: 10px;
        position: relative;
    }}

    .message:last-child {{
        margin-bottom: 0;
    }}

    .message.alice {{
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }}

    .message.bob {{
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }}

    .message-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-size: 0.9em;
    }}

    .speaker-info {{
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .speaker-name {{
        font-size: 1.2em;
    }}

    .model-badge {{
        background: rgba(0, 0, 0, 0.1);
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: normal;
    }}

    .turn-number {{
        background: rgba(0, 0, 0, 0.1);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.85em;
    }}

    .char-count {{
        color: #666;
        font-size: 0.85em;
        margin-left: 10px;
    }}

    .message-content {{
        line-height: 1.6;
        word-wrap: break-word;
    }}

    .message-content p {{
        margin: 0 0 1em 0;
    }}

    .message-content p:last-child {{
        margin-bottom: 0;
    }}

    .message-content pre {{
        background: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
    }}

    .message-content code {{
        background: #f0f0f0;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    }}

    .message-content pre code {{
        background: none;
        padding: 0;
    }}

    .message-content blockquote {{
        border-left: 3px solid #ccc;
        margin-left: 0;
        padding-left: 15px;
        color: #666;
    }}

    .message-content ul, .message-content ol {{
        margin: 0 0 1em 0;
        padding-left: 30px;
    }}

    .message-content li {{
        margin-bottom: 0.5em;
    }}

    .truncated-notice {{
        color: #ff6b6b;
        font-style: italic;
        font-size: 0.9em;
        margin-top: 10px;
    }}

    .filtered-notice {{
        color: #666;
        font-style: italic;
        font-size: 0.85em;
        margin-top: 5px;
    }}

    .thinking-block {{
        margin: 1em 0;
    }}

    .thinking-tag {{
        color: #999;
        font-family: monospace;
        font-size: 0.9em;
    }}

    .thinking-content {{
        font-style: italic;
        color: #666;
        margin: 0.5em 0;
    }}
</style>
</head>
<body>
<div class="header">
    <h1>Resonant Chat</h1>
    <div class="metadata">"""

    # Check if endpoints and models are shared
    shared_endpoint = (
        dual_model_session.alice_endpoint == dual_model_session.bob_endpoint
    )
    shared_model = dual_model_session.alice_model == dual_model_session.bob_model

    if shared_endpoint and shared_model:
        # Both endpoint and model are shared
        html_content += f"""
        <div class="metadata-item">
            <div class="metadata-label">Shared Model</div>
            <div class="metadata-value" title="{escape(dual_model_session.alice_model)}">{escape(dual_model_session.alice_model)}</div>
        </div>
        <div class="metadata-item">
            <div class="metadata-label">Shared Endpoint</div>
            <div class="metadata-value" title="{escape(dual_model_session.alice_endpoint)}">{escape(dual_model_session.alice_endpoint)}</div>
        </div>"""
    elif shared_endpoint:
        # Only endpoint is shared
        html_content += f"""
        <div class="metadata-item">
            <div class="metadata-label">Alice Model</div>
            <div class="metadata-value" title="{escape(dual_model_session.alice_model)}">{escape(dual_model_session.alice_model)}</div>
        </div>
        <div class="metadata-item">
            <div class="metadata-label">Bob Model</div>
            <div class="metadata-value" title="{escape(dual_model_session.bob_model)}">{escape(dual_model_session.bob_model)}</div>
        </div>
        <div class="metadata-item">
            <div class="metadata-label">Shared Endpoint</div>
            <div class="metadata-value" title="{escape(dual_model_session.alice_endpoint)}">{escape(dual_model_session.alice_endpoint)}</div>
        </div>"""
    else:
        # Different endpoints (and possibly models)
        html_content += f"""
        <div class="metadata-item">
            <div class="metadata-label">Alice</div>
            <div class="metadata-value" title="{escape(dual_model_session.alice_model)}">{escape(dual_model_session.alice_model)}<br><small style="opacity: 0.8" title="{escape(dual_model_session.alice_endpoint)}">{escape(dual_model_session.alice_endpoint)}</small></div>
        </div>
        <div class="metadata-item">
            <div class="metadata-label">Bob</div>
            <div class="metadata-value" title="{escape(dual_model_session.bob_model)}">{escape(dual_model_session.bob_model)}<br><small style="opacity: 0.8" title="{escape(dual_model_session.bob_endpoint)}">{escape(dual_model_session.bob_endpoint)}</small></div>
        </div>"""

    # Calculate total characters
    total_chars = sum(
        msg.get("char_count", 0) for msg in dual_model_session.full_conversation_log
    )

    html_content += f"""
        <div class="metadata-item">
            <div class="metadata-label">Max Characters</div>
            <div class="metadata-value">{dual_model_session.max_chars:,}</div>
        </div>
        <div class="metadata-item">
            <div class="metadata-label">Turn Limit</div>
            <div class="metadata-value">{dual_model_session.max_turns}</div>
        </div>
        <div class="metadata-item">
            <div class="metadata-label">Total Characters</div>
            <div class="metadata-value">{total_chars:,}</div>
        </div>
    </div>
</div>

"""
    
    # Show system prompts
    if dual_model_session.alice_system_prompt == dual_model_session.bob_system_prompt:
        # Same prompt for both
        html_content += f"""
<div class="system-prompt">
    <div class="system-prompt-header">System Prompt</div>
    <div class="system-prompt-content">{escape(dual_model_session.system_prompt)}</div>
</div>
"""
    else:
        # Different prompts
        html_content += f"""
<div class="system-prompt">
    <div class="system-prompt-header">Alice System Prompt</div>
    <div class="system-prompt-content">{escape(dual_model_session.alice_system_prompt)}</div>
</div>

<div class="system-prompt">
    <div class="system-prompt-header">Bob System Prompt</div>
    <div class="system-prompt-content">{escape(dual_model_session.bob_system_prompt)}</div>
</div>
"""
    
    html_content += """

<div class="conversation">
"""

    # Add messages
    for msg in dual_model_session.full_conversation_log:
        speaker_class = msg["speaker"].lower()
        char_count = msg.get("char_count", len(msg["content"]))
        truncated = char_count >= dual_model_session.max_chars
        was_filtered = msg.get("was_filtered", False)

        html_content += f"""
    <div class="message {speaker_class}">
        <div class="message-header">
            <div class="speaker-info">
                <span class="speaker-name">{escape(msg['speaker'])}</span>
                <span class="model-badge">{escape(msg['model'])}</span>
            </div>
            <div>
                <span class="turn-number">Turn {msg['turn']}</span>
                <span class="char-count">{char_count:,} chars</span>
            </div>
        </div>
        <div class="message-content">{dual_model_session._render_markdown_to_html(msg['content'])}</div>"""
        if truncated:
            html_content += f"""            <div class="truncated-notice">Response truncated at {dual_model_session.max_chars:,} characters</div>"""
        if was_filtered:
            html_content += f"""            <div class="filtered-notice">Note: Thinking tags were filtered from this message before the counterpart responded.</div>"""
        html_content += """        </div>"""
    html_content += """
</div>
</body>
</html>
"""

    with open(dual_model_session.html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
