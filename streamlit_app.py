import base64
import html
import uuid
from typing import Any

import boto3
import botocore.exceptions
import streamlit as st


APP_TITLE = "Toki-chan"
APP_SUBTITLE = "Memory-aware personal AI assistant"
BRAND_NAME = "TOKAICOM Mitra Indonesia"
MAX_UPLOAD_CHARS = 20_000

ASSISTANT_INSTRUCTION = (
    "You are Toki-chan, a helpful personal AI assistant with AgentCore Memory support. "
    "Help the user with general work, notes, summaries, drafts, planning, and safe memory-aware assistance. "
    "You may also help with AWS topics when asked, but do not force AWS framing. "
    "Keep answers concise, practical, and clear. "
    "Never store or expose secrets, credentials, tokens, passwords, private keys, or confidential data."
)

REQUIRED_SECRETS = (
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "HARNESS_ARN",
)

QUICK_ACTIONS = {
    "Remember this": "Store this as safe reusable memory if appropriate. Do not store secrets or confidential data: ",
    "Recall memory": "Retrieve and summarize relevant safe memory context.",
    "Forget": "Forget or mark inactive this memory/preference if supported: ",
    "Summarize": "Summarize this clearly and concisely.",
    "Draft": "Draft a clear, polished message. Ask for recipient, goal, and tone if needed.",
}


def load_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #F8FAFC;
                --card: #FFFFFF;
                --primary: #2563EB;
                --primary-soft: #EFF6FF;
                --text: #0F172A;
                --muted: #64748B;
                --border: #E2E8F0;
                --shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
            }

            header[data-testid="stHeader"],
            [data-testid="stToolbar"],
            #MainMenu,
            footer {
                visibility: hidden;
                height: 0;
            }

            .stApp {
                background:
                    radial-gradient(circle at 50% 2rem, rgba(124, 58, 237, 0.12), transparent 16rem),
                    radial-gradient(circle at 74% 18rem, rgba(37, 99, 235, 0.10), transparent 18rem),
                    var(--bg);
                color: var(--text);
            }

            .block-container {
                max-width: 980px;
                min-height: 100vh;
                padding: 1rem 1.6rem 6rem;
            }

            [data-testid="stSidebar"] {
                width: 19rem;
                border-right: 1px solid var(--border);
                background: #FFFFFF;
            }

            [data-testid="stSidebar"] > div:first-child {
                padding: 1.1rem 0.95rem;
            }

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p {
                color: var(--muted);
                font-size: 0.84rem;
            }

            .sidebar-section {
                color: var(--text);
                font-size: 0.74rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                margin: 1rem 0 0.35rem;
                text-transform: uppercase;
            }

            .sidebar-brand {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                margin-bottom: 0.8rem;
            }

            .sidebar-brand-title {
                color: var(--text);
                font-size: 0.88rem;
                font-weight: 800;
                line-height: 1.2;
            }

            .sidebar-brand-subtitle {
                color: var(--muted);
                font-size: 0.74rem;
                margin-top: 0.1rem;
            }

            .tokai-logo {
                display: block;
                width: 7.4rem;
                height: auto;
            }

            .tokai-logo-sidebar {
                width: 5.9rem;
            }

            .chat-header {
                position: sticky;
                top: 0;
                z-index: 5;
                padding: 0.75rem 0 0.85rem;
                background: linear-gradient(180deg, rgba(248, 250, 252, 0.97), rgba(248, 250, 252, 0.86));
                backdrop-filter: blur(12px);
                border-bottom: 1px solid rgba(226, 232, 240, 0.7);
            }

            .chat-header-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
            }

            .chat-title {
                color: var(--text);
                font-size: 1.2rem;
                font-weight: 800;
                line-height: 1.2;
            }

            .chat-subtitle {
                color: var(--muted);
                font-size: 0.86rem;
                margin-top: 0.15rem;
            }

            .status-row {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 0.45rem;
                flex-wrap: wrap;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                min-height: 1.75rem;
                padding: 0.3rem 0.66rem;
                border: 1px solid var(--border);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.86);
                color: var(--muted);
                font-size: 0.76rem;
                font-weight: 700;
                white-space: nowrap;
            }

            .status-pill.connected {
                border-color: #BFDBFE;
                background: var(--primary-soft);
                color: #1D4ED8;
            }

            .empty-state {
                display: flex;
                min-height: 52vh;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
            }

            .empty-orb {
                width: 3.4rem;
                height: 3.4rem;
                margin-bottom: 1rem;
                border-radius: 999px;
                background:
                    radial-gradient(circle at 32% 22%, rgba(255, 255, 255, 0.95), transparent 28%),
                    radial-gradient(circle at 38% 72%, rgba(125, 211, 252, 0.82), transparent 38%),
                    radial-gradient(circle at 68% 40%, rgba(124, 58, 237, 0.72), transparent 43%),
                    radial-gradient(circle at 76% 76%, rgba(37, 99, 235, 0.42), transparent 45%);
                box-shadow: 0 16px 42px rgba(99, 102, 241, 0.22);
            }

            .empty-state h1 {
                color: var(--text);
                font-size: 2rem;
                font-weight: 800;
                letter-spacing: 0;
                margin: 0 0 0.4rem;
            }

            .empty-state p {
                color: var(--muted);
                margin: 0;
            }

            .chat-history {
                padding: 1rem 0 1.2rem;
            }

            [data-testid="stChatMessage"] {
                border: 1px solid var(--border);
                border-radius: 16px;
                background: #FFFFFF;
                box-shadow: var(--shadow);
                padding: 0.6rem 0.75rem;
                margin-bottom: 0.85rem;
            }

            .user-bubble {
                max-width: 74%;
                margin: 0 0 0.85rem auto;
                padding: 0.72rem 0.9rem;
                border: 1px solid #BFDBFE;
                border-radius: 16px 16px 4px 16px;
                background: var(--primary-soft);
                color: var(--text);
                box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
                white-space: pre-wrap;
            }

            .assistant-bubble {
                max-width: 84%;
                margin: 0 auto 0.85rem 0;
                padding: 0.84rem 0.96rem;
                border: 1px solid var(--border);
                border-radius: 16px 16px 16px 4px;
                background: #FFFFFF;
                color: var(--text);
                box-shadow: var(--shadow);
                white-space: pre-wrap;
            }

            .composer-actions {
                margin-top: 0.6rem;
                padding: 0.7rem 0 0.25rem;
                border-top: 1px solid rgba(226, 232, 240, 0.65);
            }

            .composer-actions div.stButton > button {
                min-height: 2.2rem;
                border-radius: 999px;
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.9);
                color: var(--text);
                font-size: 0.82rem;
                font-weight: 700;
                box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
            }

            .composer-actions div.stButton > button:hover,
            div.stButton > button:hover {
                border-color: #BFDBFE;
                background: var(--primary-soft);
                color: #1D4ED8;
            }

            div.stButton > button,
            div.stDownloadButton > button {
                border: 1px solid var(--border);
                border-radius: 10px;
                background: #FFFFFF;
                color: var(--text);
                font-weight: 700;
            }

            .debug-note {
                color: var(--muted);
                font-size: 0.82rem;
            }

            @media (max-width: 900px) {
                .block-container {
                    padding: 0.75rem 1rem 6rem;
                }

                .chat-header-row {
                    align-items: flex-start;
                    flex-direction: column;
                }

                .status-row {
                    justify-content: flex-start;
                }

                .user-bubble,
                .assistant-bubble {
                    max-width: 96%;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def shorten(value: str, prefix: int = 12, suffix: int = 6) -> str:
    if not value:
        return "Not configured"
    if len(value) <= prefix + suffix + 3:
        return value
    return f"{value[:prefix]}...{value[-suffix:]}"


def render_tokai_logo(extra_class: str = "") -> str:
    class_attr = f"tokai-logo {extra_class}".strip()
    logo_svg = """
    <svg viewBox="0 0 176 65" role="img" aria-label="TOKAICOM Mitra Indonesia logo"
        xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="tokaiWingA" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#004ea8"/>
                <stop offset="1" stop-color="#2f72d9"/>
            </linearGradient>
            <linearGradient id="tokaiWingB" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#486eb8"/>
                <stop offset="1" stop-color="#d5def4"/>
            </linearGradient>
            <linearGradient id="tokaiWingC" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#0c5db8"/>
                <stop offset="1" stop-color="#c7d6f2"/>
            </linearGradient>
        </defs>
        <g transform="translate(0 14)">
            <path d="M3 17 L30 7 L27 19 L0 29 Z" fill="url(#tokaiWingA)"/>
            <path d="M28 6 L58 0 L52 17 L24 22 Z" fill="url(#tokaiWingB)"/>
            <path d="M27 21 L52 16 L45 32 L18 36 Z" fill="url(#tokaiWingC)"/>
            <path d="M7 29 L19 25 L14 38 L2 40 Z" fill="#005eb8"/>
            <text x="5" y="47" fill="#005eb8" font-family="Arial, Helvetica, sans-serif"
                font-size="5" font-weight="700" font-style="italic">TOKAI GROUP</text>
        </g>
        <g fill="#005eb8" font-family="Arial, Helvetica, sans-serif">
            <text x="66" y="14" font-size="20" font-weight="500" letter-spacing="0">TOKAICOM</text>
            <text x="66" y="36" font-size="20" font-weight="500" letter-spacing="0">Mitra</text>
            <text x="66" y="58" font-size="20" font-weight="500" letter-spacing="0">Indonesia</text>
        </g>
    </svg>
    """
    logo_data = base64.b64encode(logo_svg.encode("utf-8")).decode("ascii")
    return (
        f'<img class="{html.escape(class_attr)}" '
        f'src="data:image/svg+xml;base64,{logo_data}" '
        'alt="TOKAICOM Mitra Indonesia logo" />'
    )


def validate_secrets() -> dict[str, str]:
    missing = [key for key in REQUIRED_SECRETS if not st.secrets.get(key)]
    if missing:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                {render_tokai_logo()}
                <div>
                    <div class="sidebar-brand-title">{html.escape(BRAND_NAME)}</div>
                    <div class="sidebar-brand-subtitle">Setup required</div>
                </div>
            </div>
            <div class="assistant-bubble">
                <strong>Setup Required</strong><br>
                Add the missing Streamlit Secrets below, then redeploy or rerun the app.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code("\n".join(missing), language="text")
        st.stop()

    return {key: str(st.secrets[key]) for key in REQUIRED_SECRETS}


def login_gate() -> None:
    app_password = st.secrets.get("APP_PASSWORD", "")
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False if app_password else True

    if st.session_state.authenticated:
        return

    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-orb"></div>
            <h1>{html.escape(APP_TITLE)}</h1>
            <p>{html.escape(APP_SUBTITLE)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    password = st.text_input("Password", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if password == app_password:
            st.session_state.authenticated = True
            st.rerun()
        st.error("Wrong password")
    st.stop()


def init_session() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("runtime_session_id", str(uuid.uuid4()))
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("pending_context", None)
    st.session_state.setdefault("last_event_summary", [])
    st.session_state.setdefault("last_invocation_error", None)
    st.session_state.setdefault("uploaded_context", None)


def build_prompt(user_prompt: str, uploaded_context: str | None = None) -> str:
    context_block = ""
    if uploaded_context:
        context_block = (
            "\n\nUploaded context follows. Use it only for this request.\n"
            "--- BEGIN CONTEXT ---\n"
            f"{uploaded_context[:MAX_UPLOAD_CHARS]}\n"
            "--- END CONTEXT ---"
        )

    return (
        f"{ASSISTANT_INSTRUCTION}\n\n"
        "Respond in Indonesian or English following the user's message.\n\n"
        f"User request:\n{user_prompt.strip()}"
        f"{context_block}"
    )


def create_agentcore_client(secrets: dict[str, str]) -> Any:
    return boto3.client(
        "bedrock-agentcore",
        region_name=secrets["AWS_REGION"],
        aws_access_key_id=secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=secrets["AWS_SECRET_ACCESS_KEY"],
    )


def sanitize_sensitive_text(value: Any, secrets: dict[str, str]) -> str:
    text = str(value)
    replacements = {
        secrets.get("AWS_ACCESS_KEY_ID", ""): "[masked access key]",
        secrets.get("AWS_SECRET_ACCESS_KEY", ""): "[masked secret key]",
        secrets.get("HARNESS_ARN", ""): shorten(secrets.get("HARNESS_ARN", ""), 18, 8),
    }
    for raw_value, replacement in replacements.items():
        if raw_value:
            text = text.replace(raw_value, replacement)
    return text


def summarize_event(event: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
    event_type = next(iter(event.keys()), "unknown")
    summary: dict[str, Any] = {"type": event_type}

    if event_type == "contentBlockDelta":
        delta = event[event_type].get("delta", {})
        summary["has_text"] = "text" in delta
        summary["text_chars"] = len(delta.get("text", ""))
    elif event_type in {"runtimeClientError", "validationException"}:
        value = event.get(event_type, {})
        if isinstance(value, dict):
            summary["message"] = sanitize_sensitive_text(value.get("message", "Error event received"), secrets)
        else:
            summary["message"] = sanitize_sensitive_text(value, secrets)
    elif isinstance(event.get(event_type), dict):
        summary["keys"] = list(event[event_type].keys())

    return summary


def invoke_harness(prompt: str) -> str:
    secrets = validate_secrets()
    session_id = st.session_state.runtime_session_id
    st.session_state.last_event_summary = []
    st.session_state.last_invocation_error = None

    try:
        client = create_agentcore_client(secrets)
        response = client.invoke_harness(
            harnessArn=secrets["HARNESS_ARN"],
            runtimeSessionId=session_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
        )

        output_parts: list[str] = []
        for event in response.get("stream", []):
            st.session_state.last_event_summary.append(summarize_event(event, secrets))

            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    output_parts.append(delta["text"])
            elif "messageStop" in event:
                continue
            elif "runtimeClientError" in event:
                message = sanitize_sensitive_text(
                    event["runtimeClientError"].get("message", "Runtime client error"),
                    secrets,
                )
                output_parts.append(f"\nAgentCore runtime error: {message}")
            elif "validationException" in event:
                value = event["validationException"]
                message = value.get("message", value) if isinstance(value, dict) else value
                message = sanitize_sensitive_text(message, secrets)
                output_parts.append(f"\nValidation error: {message}")

        output = "".join(output_parts).strip()
        return output or "No response from AgentCore Harness."

    except botocore.exceptions.ClientError as exc:
        message = exc.response.get("Error", {}).get("Message", str(exc))
        message = sanitize_sensitive_text(message, secrets)
        st.session_state.last_invocation_error = message
        return f"AgentCore Harness returned an AWS client error: {message}"
    except Exception as exc:
        st.session_state.last_invocation_error = sanitize_sensitive_text(exc, secrets)
        return "I could not reach AgentCore Harness. Please check the app secrets, Harness ARN, region, and AWS permissions."


def read_uploaded_text(uploaded_file: Any) -> tuple[str, bool]:
    raw = uploaded_file.getvalue()
    text = raw.decode("utf-8", errors="replace")
    truncated = len(text) > MAX_UPLOAD_CHARS
    return text[:MAX_UPLOAD_CHARS], truncated


def send_message(user_prompt: str, uploaded_context: str | None = None) -> None:
    prompt = user_prompt.strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    final_prompt = build_prompt(prompt, uploaded_context)
    with st.spinner("Thinking..."):
        output = invoke_harness(final_prompt)
    st.session_state.messages.append({"role": "assistant", "content": output})
    st.session_state.uploaded_context = None
    st.rerun()


def render_sidebar(secrets: dict[str, str]) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                {render_tokai_logo("tokai-logo-sidebar")}
                <div>
                    <div class="sidebar-brand-title">{html.escape(BRAND_NAME)}</div>
                    <div class="sidebar-brand-subtitle">Toki-chan</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
        if st.button("New Chat", use_container_width=True):
            st.session_state.runtime_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.last_event_summary = []
            st.session_state.uploaded_context = None
            st.rerun()
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown('<div class="sidebar-section">Upload Context</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Context", type=["txt", "md", "csv", "json", "py", "log"])
        if uploaded_file:
            uploaded_context, truncated = read_uploaded_text(uploaded_file)
            st.session_state.uploaded_context = uploaded_context
            size_kb = len(uploaded_file.getvalue()) / 1024
            st.caption(f"{uploaded_file.name} - {size_kb:.1f} KB")
            if truncated:
                st.caption(f"Limited to {MAX_UPLOAD_CHARS:,} characters.")
            with st.expander("Preview", expanded=False):
                st.text(uploaded_context[:3_000])

        st.markdown('<div class="sidebar-section">Memory</div>', unsafe_allow_html=True)
        if st.button("What do you remember?", use_container_width=True):
            send_message("Retrieve and summarize relevant safe memory context.")

        preference = st.text_area("Preference to remember", height=84, placeholder="Example: I prefer short weekly summaries.")
        if st.button("Remember", use_container_width=True):
            if preference.strip():
                send_message(
                    "Store this as safe reusable memory if appropriate. "
                    f"Do not store secrets or confidential data: {preference.strip()}"
                )
            else:
                st.warning("Add a preference first.")

        forget_target = st.text_input("Forget / mark inactive", placeholder="Optional memory or preference")
        if st.button("Forget / Mark inactive", use_container_width=True):
            target = forget_target.strip() or "the relevant memory/preference"
            send_message(f"Forget or mark inactive this memory/preference if supported: {target}")

        st.markdown('<div class="sidebar-section">Debug</div>', unsafe_allow_html=True)
        with st.expander("Debug", expanded=False):
            try:
                client = create_agentcore_client(secrets)
                method_available = hasattr(client, "invoke_harness")
            except Exception:
                method_available = False

            st.markdown('<div class="debug-note">Sensitive values are masked.</div>', unsafe_allow_html=True)
            st.json(
                {
                    "region": secrets["AWS_REGION"],
                    "harness_arn_short": shorten(secrets["HARNESS_ARN"], 18, 8),
                    "runtime_session_id": st.session_state.runtime_session_id,
                    "invoke_harness_available": method_available,
                    "last_invocation_error": st.session_state.last_invocation_error,
                    "last_event_summary": st.session_state.last_event_summary,
                }
            )

        st.markdown('<div class="sidebar-section">Account</div>', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()


def render_header(secrets: dict[str, str]) -> None:
    region = secrets.get("AWS_REGION", "Not configured")
    session_short = shorten(st.session_state.runtime_session_id, 8, 4)

    st.markdown(
        f"""
        <div class="chat-header">
            <div class="chat-header-row">
                <div>
                    <div class="chat-title">{html.escape(APP_TITLE)}</div>
                    <div class="chat-subtitle">{html.escape(APP_SUBTITLE)}</div>
                </div>
                <div class="status-row">
                    <span class="status-pill connected">AgentCore Connected</span>
                    <span class="status-pill">{html.escape(region)}</span>
                    <span class="status-pill">Session: {html.escape(session_short)}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    st.markdown('<main class="chat-history">', unsafe_allow_html=True)
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-orb"></div>
                <h1>Ask Toki-chan anything</h1>
                <p>Start a conversation or use a memory action.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for message in st.session_state.messages:
            content = str(message["content"])
            if message["role"] == "user":
                st.markdown(f'<div class="user-bubble">{html.escape(content)}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-bubble">{html.escape(content)}</div>', unsafe_allow_html=True)
    st.markdown("</main>", unsafe_allow_html=True)


def render_quick_actions() -> None:
    st.markdown('<div class="composer-actions">', unsafe_allow_html=True)
    columns = st.columns(5)
    for column, (label, prompt) in zip(columns, QUICK_ACTIONS.items()):
        with column:
            if st.button(label, use_container_width=True):
                send_message(prompt)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="T",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()
    login_gate()
    init_session()
    secrets = validate_secrets()
    render_sidebar(secrets)
    render_header(secrets)
    render_chat_history()
    render_quick_actions()

    prompt = st.chat_input("Ask anything or tell Toki-chan what to remember...")
    if prompt:
        send_message(prompt, st.session_state.get("uploaded_context"))


if __name__ == "__main__":
    main()
