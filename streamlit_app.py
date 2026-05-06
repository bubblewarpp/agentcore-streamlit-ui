import base64
import html
import uuid
from typing import Any

import boto3
import botocore.exceptions
import streamlit as st


APP_TITLE = "Toki-chan AgentCore Assistant"
APP_SUBTITLE = "Enterprise AI workbench for AWS architecture, proposal review, pricing, and troubleshooting."
BRAND_NAME = "TOKAICOM Mitra Indonesia"
MAX_UPLOAD_CHARS = 20_000

REQUIRED_SECRETS = (
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "HARNESS_ARN",
)

MODE_PROMPTS = {
    "General Assistant": "Act as a helpful, practical personal AI assistant.",
    "AWS Solution Architect": (
        "Act as an AWS Solution Architect. Apply AWS Well-Architected best practices, "
        "call out tradeoffs, reliability, security, cost, and operational considerations."
    ),
    "Proposal Reviewer": (
        "Review proposal content. Identify risks, gaps, assumptions, missing details, "
        "improvements, and questions that should be resolved before approval."
    ),
    "Pricing Estimator": (
        "Focus on assumptions, cost drivers, pricing caveats, sizing uncertainty, "
        "optimization options, and what data is needed for a more accurate estimate."
    ),
    "Troubleshooting Assistant": (
        "Diagnose the issue. Provide likely root causes, checks to run, evidence to gather, "
        "and the recommended fix path."
    ),
    "Documentation Generator": (
        "Produce clean, well-structured Notion-ready documentation with clear headings, "
        "tables where useful, and concise operational detail."
    ),
    "Memory Manager": (
        "Help with safe memory actions such as remember, recall, and forget. Do not store "
        "or request sensitive information such as secrets, credentials, tokens, account IDs, "
        "private keys, or personal data that should not be retained."
    ),
}

FORMAT_PROMPTS = {
    "Concise Answer": "Use a concise answer with only the most important details.",
    "Executive Summary": "Use an executive-summary format with decision-ready bullets.",
    "Technical Guide": "Use a technical guide format with steps, caveats, and implementation notes.",
    "Notion-ready Documentation": "Use Notion-ready documentation with headings and clean structure.",
    "Meeting Notes": "Use meeting notes format with summary, decisions, risks, and follow-ups.",
    "Action Items": "Use action items with owners, priorities, and next steps when possible.",
    "Table Format": "Use tables where possible and keep supporting notes short.",
}


def load_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #F6F8FB;
                --card: #FFFFFF;
                --primary: #2563EB;
                --primary-strong: #1D4ED8;
                --soft-blue: #EFF6FF;
                --text: #0F172A;
                --muted: #64748B;
                --border: #E2E8F0;
                --shadow: 0 18px 44px rgba(15, 23, 42, 0.07);
            }

            header[data-testid="stHeader"],
            [data-testid="stToolbar"],
            #MainMenu,
            footer {
                visibility: hidden;
                height: 0;
            }

            .stApp {
                background: var(--bg);
                color: var(--text);
            }

            .block-container {
                max-width: 1220px;
                padding: 1rem 2rem 2.5rem;
            }

            [data-testid="stSidebar"] {
                width: 21rem;
                border-right: 1px solid var(--border);
                background: #FFFFFF;
            }

            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1.2rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            [data-testid="stSidebar"] h3 {
                color: var(--text);
                font-size: 0.86rem;
                font-weight: 750;
                letter-spacing: 0.02em;
                margin-bottom: 0.35rem;
            }

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p {
                color: var(--muted);
                font-size: 0.86rem;
            }

            [data-testid="stSidebar"] hr {
                margin: 0.85rem 0;
                border-color: var(--border);
            }

            .top-nav {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                min-height: 3.4rem;
                padding: 0.5rem 0 0.95rem;
                border-bottom: 1px solid var(--border);
            }

            .top-nav-left,
            .top-nav-links,
            .top-nav-right {
                display: flex;
                align-items: center;
                gap: 0.85rem;
            }

            .top-nav-links {
                justify-content: center;
                flex: 1;
                color: var(--muted);
                font-size: 0.92rem;
                font-weight: 650;
            }

            .top-nav-links span {
                padding: 0.35rem 0.55rem;
                border-radius: 999px;
            }

            .top-nav-links span:first-child {
                color: var(--primary-strong);
                background: var(--soft-blue);
            }

            .brand-name {
                color: var(--text);
                font-size: 0.94rem;
                font-weight: 750;
                white-space: nowrap;
            }

            .tokai-logo {
                display: block;
                width: 8.8rem;
                height: auto;
            }

            .tokai-logo-sidebar {
                width: 7.4rem;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                min-height: 1.85rem;
                padding: 0.32rem 0.66rem;
                border: 1px solid var(--border);
                border-radius: 999px;
                background: #FFFFFF;
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 700;
                line-height: 1;
                white-space: nowrap;
            }

            .status-pill.connected {
                border-color: #BFDBFE;
                background: var(--soft-blue);
                color: var(--primary-strong);
            }

            .hero {
                max-width: 820px;
                margin: 6.6rem auto 1.4rem;
                text-align: center;
            }

            .hero h1 {
                color: var(--text);
                font-size: 2.55rem;
                line-height: 1.14;
                font-weight: 760;
                letter-spacing: 0;
                margin: 0 0 0.7rem;
            }

            .hero p {
                color: var(--muted);
                font-size: 1.04rem;
                line-height: 1.6;
                max-width: 650px;
                margin: 0 auto;
            }

            .pill-row {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 1.15rem;
            }

            .chat-shell {
                max-width: 780px;
                margin: 0 auto;
                border: 1px solid var(--border);
                border-radius: 18px;
                background: var(--card);
                box-shadow: var(--shadow);
                overflow: hidden;
            }

            .composer-titlebar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                padding: 0.72rem 1rem;
                background: #F8FAFC;
                border-bottom: 1px solid var(--border);
                color: var(--text);
                font-size: 0.92rem;
                font-weight: 750;
            }

            .composer-titlebar span:last-child {
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 650;
            }

            [data-testid="stForm"] {
                max-width: 780px;
                margin: 0 auto;
                border: 1px solid var(--border);
                border-top: 0;
                border-radius: 0 0 18px 18px;
                background: var(--card);
                box-shadow: var(--shadow);
                padding: 0.75rem 0.85rem 0.85rem;
            }

            [data-testid="stForm"] textarea {
                min-height: 118px;
                border: 0 !important;
                box-shadow: none !important;
                background: #FFFFFF !important;
                color: var(--text) !important;
                font-size: 1rem !important;
            }

            [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
                background: var(--primary);
                border: 1px solid var(--primary);
                color: #FFFFFF;
                border-radius: 999px;
                font-weight: 750;
                min-height: 2.35rem;
            }

            .quick-actions-grid {
                max-width: 780px;
                margin: 1.1rem auto 0.65rem;
            }

            .quick-action-card {
                display: flex;
                align-items: center;
                gap: 0.55rem;
                min-height: 2.5rem;
                padding: 0.62rem 0.78rem;
                border: 1px solid var(--border);
                border-radius: 999px;
                background: #FFFFFF;
                color: var(--text);
                box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
                font-size: 0.9rem;
                font-weight: 650;
            }

            .quick-actions-grid div.stButton > button {
                min-height: 2.65rem;
                border-radius: 999px;
                background: #FFFFFF;
                box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
                text-align: left;
            }

            .quick-actions-grid div.stButton > button::before {
                content: "+";
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 1.25rem;
                height: 1.25rem;
                margin-right: 0.45rem;
                border-radius: 999px;
                background: var(--soft-blue);
                color: var(--primary-strong);
                font-weight: 800;
            }

            .quick-action-card .dot {
                width: 1.3rem;
                height: 1.3rem;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: var(--soft-blue);
                color: var(--primary-strong);
                font-weight: 800;
            }

            .chat-history {
                max-width: 850px;
                margin: 2.25rem auto 0;
            }

            .message-card {
                border: 1px solid var(--border);
                border-radius: 16px;
                background: #FFFFFF;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
                padding: 0.85rem 1rem;
                margin-bottom: 0.85rem;
            }

            [data-testid="stChatMessage"] {
                border: 1px solid var(--border);
                border-radius: 16px;
                background: #FFFFFF;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
                padding: 0.55rem 0.7rem;
                margin-bottom: 0.85rem;
            }

            .empty-card,
            .setup-card,
            .debug-card {
                border: 1px solid var(--border);
                border-radius: 16px;
                background: #FFFFFF;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
                padding: 0.95rem 1rem;
                margin: 0.8rem 0;
            }

            .empty-card h3,
            .setup-card h3,
            .debug-card h3 {
                color: var(--text);
                font-size: 1rem;
                margin: 0 0 0.25rem;
            }

            .muted {
                color: var(--muted);
            }

            .sidebar-section {
                color: var(--text);
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin: 0.95rem 0 0.35rem;
            }

            div.stButton > button,
            div.stDownloadButton > button {
                border: 1px solid var(--border);
                border-radius: 10px;
                background: #FFFFFF;
                color: var(--text);
                font-weight: 650;
            }

            div.stButton > button:hover {
                border-color: #BFDBFE;
                color: var(--primary-strong);
                background: var(--soft-blue);
            }

            .sidebar-brand {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin-bottom: 0.65rem;
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

            @media (max-width: 920px) {
                .block-container {
                    padding: 0.75rem 1rem 2rem;
                }

                .top-nav {
                    align-items: flex-start;
                    flex-direction: column;
                }

                .top-nav-links,
                .top-nav-right {
                    justify-content: flex-start;
                    flex-wrap: wrap;
                }

                .hero {
                    margin-top: 3.5rem;
                }

                .hero h1 {
                    font-size: 2rem;
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


def render_setup_top_nav() -> None:
    st.markdown(
        f"""
        <div class="top-nav">
            <div class="top-nav-left">
                {render_tokai_logo()}
                <div class="brand-name">{html.escape(BRAND_NAME)}</div>
            </div>
            <div class="top-nav-links">
                <span>Solutions</span><span>Workbench</span><span>Memory</span><span>Docs</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def validate_secrets() -> dict[str, str]:
    missing = [key for key in REQUIRED_SECRETS if not st.secrets.get(key)]
    if missing:
        render_setup_top_nav()
        st.markdown(
            """
            <div class="setup-card">
                <h3>Setup Required</h3>
                <div class="muted">
                    Add the missing Streamlit Secrets below, then redeploy or rerun the app.
                    Secrets are intentionally not read from source code.
                </div>
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

    render_setup_top_nav()
    st.markdown(
        f"""
        <section class="hero">
            <h1>{html.escape(APP_TITLE)}</h1>
            <p>{html.escape(APP_SUBTITLE)}</p>
        </section>
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
    st.session_state.setdefault("debug_enabled", False)
    st.session_state.setdefault("show_short_session_id", False)
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("pending_context", None)
    st.session_state.setdefault("last_event_summary", [])
    st.session_state.setdefault("last_invocation_error", None)
    st.session_state.setdefault("attach_upload_to_prompt", False)


def build_prompt(
    user_prompt: str,
    mode: str,
    output_format: str,
    uploaded_context: str | None = None,
) -> str:
    context_block = ""
    if uploaded_context:
        context_block = (
            "\n\nUploaded or sidebar context follows. Use it only for this request.\n"
            "--- BEGIN CONTEXT ---\n"
            f"{uploaded_context[:MAX_UPLOAD_CHARS]}\n"
            "--- END CONTEXT ---"
        )

    return (
        f"Assistant mode: {mode}\n"
        f"Mode instruction: {MODE_PROMPTS[mode]}\n\n"
        f"Output format: {output_format}\n"
        f"Format instruction: {FORMAT_PROMPTS[output_format]}\n\n"
        "Safety and privacy: never expose secrets, credentials, access keys, tokens, or raw sensitive values. "
        "If the user asks to remember information, only retain safe non-sensitive preferences.\n\n"
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


def queue_prompt(prompt: str, context: str | None = None) -> None:
    st.session_state.pending_prompt = prompt
    st.session_state.pending_context = context


def render_sidebar(secrets: dict[str, str]) -> dict[str, Any]:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                {render_tokai_logo("tokai-logo-sidebar")}
            </div>
            <div class="sidebar-brand-title">Toki-chan Workbench</div>
            <div class="sidebar-brand-subtitle">AgentCore Harness session controls</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">Assistant Mode</div>', unsafe_allow_html=True)
        mode = st.selectbox("Assistant Mode", list(MODE_PROMPTS.keys()), label_visibility="collapsed")

        st.markdown('<div class="sidebar-section">Output Format</div>', unsafe_allow_html=True)
        output_format = st.selectbox("Output Format", list(FORMAT_PROMPTS.keys()), label_visibility="collapsed")

        st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("New", use_container_width=True):
                st.session_state.runtime_session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.last_event_summary = []
                st.rerun()
        with col_b:
            if st.button("Clear", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        if st.button("Show Short Session ID", use_container_width=True):
            st.session_state.show_short_session_id = not st.session_state.show_short_session_id
        if st.session_state.show_short_session_id:
            st.code(shorten(st.session_state.runtime_session_id, 8, 4), language="text")

        st.markdown('<div class="sidebar-section">File Upload</div>', unsafe_allow_html=True)
        uploaded_context = None
        uploaded_file = st.file_uploader("Attach context", type=["txt", "md", "csv", "json", "py", "log"])
        if uploaded_file:
            uploaded_context, truncated = read_uploaded_text(uploaded_file)
            size_kb = len(uploaded_file.getvalue()) / 1024
            st.caption(f"{uploaded_file.name} - {size_kb:.1f} KB")
            st.session_state.attach_upload_to_prompt = st.checkbox(
                "Attach to next composer prompt",
                value=st.session_state.attach_upload_to_prompt,
            )
            if truncated:
                st.caption(f"Limited to {MAX_UPLOAD_CHARS:,} characters.")
            with st.expander("Preview", expanded=False):
                st.text(uploaded_context[:3_000])

            file_task = st.selectbox(
                "Send file with task",
                [
                    "Summarize this file",
                    "Review AWS proposal",
                    "Create meeting notes",
                    "Create troubleshooting checklist",
                    "Generate Notion documentation",
                ],
            )
            if st.button("Send File to Agent", use_container_width=True):
                queue_prompt(file_task, uploaded_context)

        st.markdown('<div class="sidebar-section">Memory Action</div>', unsafe_allow_html=True)
        if st.button("What do you remember?", use_container_width=True):
            queue_prompt(
                "Please recall what safe preferences or durable memories you have about me. "
                "Do not reveal secrets or sensitive data."
            )
        preference = st.text_area("Preference to remember", height=78, placeholder="Example: Prefer concise AWS diagrams.")
        if st.button("Remember preference", use_container_width=True):
            if preference.strip():
                queue_prompt(
                    "Please remember this safe, non-sensitive preference for future help. "
                    f"Preference: {preference.strip()}"
                )
            else:
                st.warning("Add a preference first.")
        forget_target = st.text_input("Preference to forget", placeholder="Optional")
        if st.button("Forget preference", use_container_width=True):
            target = forget_target.strip() or "the relevant preference I previously asked you to remember"
            queue_prompt(f"Please forget {target}. If this is ambiguous, ask one clarifying question.")

        st.markdown('<div class="sidebar-section">Proposal Review</div>', unsafe_allow_html=True)
        proposal_text = st.text_area("Proposal text", height=96, placeholder="Paste proposal content for review.")
        if st.button("Review proposal text", use_container_width=True):
            context = uploaded_context or proposal_text.strip()
            if context:
                queue_prompt("Review this AWS proposal for risks, gaps, assumptions, and improvements.", context)
            else:
                st.warning("Upload a file or paste proposal content first.")

        st.markdown('<div class="sidebar-section">Debug</div>', unsafe_allow_html=True)
        st.session_state.debug_enabled = st.toggle("Debug Panel", value=st.session_state.debug_enabled)
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    return {
        "mode": mode,
        "output_format": output_format,
        "uploaded_context": uploaded_context,
        "region": secrets["AWS_REGION"],
    }


def render_header(secrets: dict[str, str], mode: str) -> None:
    region = secrets.get("AWS_REGION", "Not configured")
    session_short = shorten(st.session_state.runtime_session_id, 8, 4)
    safe_mode = html.escape(mode)

    st.markdown(
        f"""
        <nav class="top-nav">
            <div class="top-nav-left">
                {render_tokai_logo()}
                <div class="brand-name">{html.escape(BRAND_NAME)}</div>
            </div>
            <div class="top-nav-links">
                <span>Solutions</span>
                <span>Workbench</span>
                <span>Memory</span>
                <span>Docs</span>
            </div>
            <div class="top-nav-right">
                <span class="status-pill connected">AgentCore Connected</span>
                <span class="status-pill">{html.escape(region)}</span>
                <span class="status-pill">Session: {html.escape(session_short)}</span>
                <span class="status-pill">Mode: {safe_mode}</span>
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )


def render_debug_panel(secrets: dict[str, str]) -> None:
    if not st.session_state.debug_enabled:
        return

    try:
        client = create_agentcore_client(secrets)
        method_available = hasattr(client, "invoke_harness")
    except Exception:
        method_available = False

    with st.expander("Debug Panel", expanded=False):
        st.markdown(
            """
            <div class="debug-card">
                <h3>Harness Diagnostics</h3>
                <div class="muted">Sensitive values are masked. Access keys, secret keys, and tokens are never displayed.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
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


def render_hero(mode: str, output_format: str) -> None:
    st.markdown(
        f"""
        <section class="hero">
            <h1>{html.escape(APP_TITLE)}</h1>
            <p>{html.escape(APP_SUBTITLE)}</p>
            <div class="pill-row">
                <span class="status-pill">Mode: {html.escape(mode)}</span>
                <span class="status-pill">Format: {html.escape(output_format)}</span>
                <span class="status-pill connected">Harness ready</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_composer(mode: str, output_format: str, uploaded_context: str | None) -> None:
    st.markdown(
        """
        <div class="chat-shell">
            <div class="composer-titlebar">
                <span>Toki-chan AgentCore Assistant</span>
                <span>New conversation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("assistant_composer", clear_on_submit=True):
        prompt = st.text_area(
            "Ask Toki-chan",
            placeholder="Ask Toki-chan to review a proposal, estimate AWS cost, or troubleshoot an issue...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and prompt.strip():
        context = uploaded_context if st.session_state.attach_upload_to_prompt else None
        process_user_prompt(prompt.strip(), mode, output_format, context)


def render_quick_actions(mode: str, output_format: str, uploaded_context: str | None) -> None:
    actions = [
        (
            "Review AWS proposal",
            "Review this AWS proposal deeply: scope, architecture, pricing, risks, assumptions, and readiness.",
            uploaded_context,
        ),
        (
            "Check architecture vs pricing",
            "Check the architecture against pricing assumptions. Identify mismatches, cost drivers, caveats, and optimization options.",
            uploaded_context,
        ),
        (
            "Create troubleshooting checklist",
            "Create a troubleshooting checklist with symptoms, likely causes, checks, commands or console areas to inspect, and fixes.",
            uploaded_context,
        ),
        (
            "Generate Notion documentation",
            "Generate clean Notion-ready documentation with headings, tables where useful, and action-oriented sections.",
            uploaded_context,
        ),
        (
            "What do you remember?",
            "Please recall what safe preferences or durable memories you have about me. Do not reveal secrets or sensitive data.",
            None,
        ),
    ]

    st.markdown('<div class="quick-actions-grid">', unsafe_allow_html=True)
    columns = st.columns([1, 1, 1])
    for index, (label, prompt, context) in enumerate(actions):
        with columns[index % 3]:
            if st.button(label, key=f"quick_{index}", use_container_width=True):
                process_user_prompt(prompt, mode, output_format, context)
    st.markdown("</div>", unsafe_allow_html=True)


def process_user_prompt(user_prompt: str, mode: str, output_format: str, context: str | None = None) -> None:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    final_prompt = build_prompt(user_prompt, mode, output_format, context)
    with st.spinner("Invoking AgentCore Harness..."):
        output = invoke_harness(final_prompt)
    st.session_state.messages.append({"role": "assistant", "content": output})
    st.rerun()


def render_chat_history() -> None:
    st.markdown('<section class="chat-history">', unsafe_allow_html=True)
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-card">
                <h3>Start with a question or choose a quick action.</h3>
                <div class="muted">Your conversation will appear here after Toki-chan responds.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    st.markdown("</section>", unsafe_allow_html=True)


def render_chat(mode: str, output_format: str, uploaded_context: str | None = None) -> None:
    pending_prompt = st.session_state.pending_prompt
    pending_context = st.session_state.pending_context
    if pending_prompt:
        st.session_state.pending_prompt = None
        st.session_state.pending_context = None
        process_user_prompt(pending_prompt, mode, output_format, pending_context)
        return

    render_hero(mode, output_format)
    render_composer(mode, output_format, uploaded_context)
    render_quick_actions(mode, output_format, uploaded_context)
    render_chat_history()


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
    controls = render_sidebar(secrets)
    render_header(secrets, controls["mode"])
    render_debug_panel(secrets)
    render_chat(controls["mode"], controls["output_format"], controls["uploaded_context"])


if __name__ == "__main__":
    main()
