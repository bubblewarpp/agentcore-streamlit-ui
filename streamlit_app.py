import base64
import html
import uuid
from typing import Any

import boto3
import botocore.exceptions
import streamlit as st


APP_TITLE = "Ask Toki-chan anything"
APP_SUBTITLE = (
    "Enterprise AI assistant for AWS architecture, proposal review, troubleshooting, "
    "and memory-aware workflows."
)
BRAND_NAME = "TOKAICOM Mitra Indonesia"
MAX_UPLOAD_CHARS = 20_000

ASSISTANT_INSTRUCTION = (
    "You are Toki-chan, a personal AI assistant with strong AWS Solution Architect specialization. "
    "Help with AWS architecture, proposal review, pricing assumptions, troubleshooting, documentation, "
    "and safe memory-aware assistance. Keep answers concise, practical, structured, and enterprise-friendly. "
    "Do not store or expose secrets, credentials, tokens, passwords, private keys, or confidential data."
)

REQUIRED_SECRETS = (
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "HARNESS_ARN",
)

QUICK_ACTIONS = [
    (
        "Review AWS proposal",
        "Review this AWS proposal: identify risks, gaps, assumptions, pricing concerns, architecture issues, and readiness improvements.",
    ),
    (
        "Check architecture vs pricing",
        "Check the architecture against pricing assumptions. Highlight mismatches, cost drivers, caveats, and optimization options.",
    ),
    (
        "Create troubleshooting checklist",
        "Create a troubleshooting checklist with symptoms, likely causes, validation checks, console areas or commands to inspect, and recommended fixes.",
    ),
    (
        "Generate Notion documentation",
        "Generate clean Notion-ready documentation with headings, concise sections, and tables where useful.",
    ),
    (
        "What do you remember?",
        "Please recall what safe preferences or durable memories you have about me. Do not reveal secrets or sensitive data.",
    ),
]


def load_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #F6F8FB;
                --card: #FFFFFF;
                --primary: #2563EB;
                --primary-strong: #1D4ED8;
                --lavender: #7C3AED;
                --soft-blue: #EFF6FF;
                --text: #0F172A;
                --muted: #64748B;
                --border: #E2E8F0;
                --shadow: 0 24px 70px rgba(15, 23, 42, 0.08);
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
                    radial-gradient(circle at 50% 14%, rgba(124, 58, 237, 0.16), transparent 14rem),
                    radial-gradient(circle at 48% 42%, rgba(37, 99, 235, 0.12), transparent 18rem),
                    radial-gradient(circle at 78% 78%, rgba(34, 197, 94, 0.08), transparent 18rem),
                    var(--bg);
                color: var(--text);
            }

            .block-container {
                max-width: 1160px;
                padding: 1.05rem 2rem 2.4rem;
            }

            [data-testid="stSidebar"] {
                width: 19.5rem;
                border-right: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.84);
                backdrop-filter: blur(18px);
            }

            [data-testid="stSidebar"] > div:first-child {
                padding: 1.1rem 0.95rem;
            }

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p {
                color: var(--muted);
                font-size: 0.84rem;
            }

            [data-testid="stSidebar"] hr {
                margin: 0.8rem 0;
                border-color: var(--border);
            }

            .sidebar-section {
                color: var(--text);
                font-size: 0.75rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin: 1rem 0 0.35rem;
            }

            .sidebar-brand {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin-bottom: 0.9rem;
            }

            .sidebar-brand-copy {
                line-height: 1.2;
            }

            .sidebar-brand-title {
                color: var(--text);
                font-size: 0.9rem;
                font-weight: 800;
            }

            .sidebar-brand-subtitle {
                color: var(--muted);
                font-size: 0.74rem;
                margin-top: 0.1rem;
            }

            .tokai-logo {
                display: block;
                width: 8.2rem;
                height: auto;
            }

            .tokai-logo-sidebar {
                width: 6.8rem;
            }

            .top-status {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                flex-wrap: wrap;
                margin: 0.4rem auto 2.7rem;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                min-height: 1.85rem;
                padding: 0.34rem 0.72rem;
                border: 1px solid var(--border);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.82);
                color: var(--muted);
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
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
                margin: 0 auto 1.35rem;
                text-align: center;
            }

            .orb {
                width: 4.3rem;
                height: 4.3rem;
                margin: 0 auto 1.3rem;
                border-radius: 999px;
                background:
                    radial-gradient(circle at 32% 22%, rgba(255, 255, 255, 0.96), transparent 26%),
                    radial-gradient(circle at 36% 70%, rgba(125, 211, 252, 0.82), transparent 35%),
                    radial-gradient(circle at 68% 38%, rgba(124, 58, 237, 0.78), transparent 42%),
                    radial-gradient(circle at 76% 76%, rgba(37, 99, 235, 0.45), transparent 45%);
                filter: blur(0.15px);
                box-shadow: 0 18px 50px rgba(99, 102, 241, 0.24);
            }

            .hero h1 {
                color: var(--text);
                font-size: 2.85rem;
                line-height: 1.1;
                font-weight: 780;
                letter-spacing: 0;
                margin: 0 0 0.72rem;
            }

            .hero p {
                color: var(--muted);
                font-size: 1rem;
                line-height: 1.65;
                max-width: 680px;
                margin: 0 auto;
            }

            .composer-shell {
                max-width: 820px;
                margin: 1.65rem auto 0;
                border: 1px solid rgba(226, 232, 240, 0.95);
                border-radius: 26px;
                background: rgba(255, 255, 255, 0.9);
                box-shadow: var(--shadow);
                overflow: hidden;
            }

            .composer-top {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                padding: 0.82rem 1rem 0;
                color: var(--muted);
                font-size: 0.82rem;
                font-weight: 700;
            }

            [data-testid="stForm"] {
                max-width: 820px;
                margin: 0 auto;
                border: 1px solid rgba(226, 232, 240, 0.95);
                border-top: 0;
                border-radius: 0 0 26px 26px;
                background: rgba(255, 255, 255, 0.9);
                box-shadow: var(--shadow);
                padding: 0.45rem 0.95rem 0.9rem;
            }

            [data-testid="stForm"] textarea {
                min-height: 128px;
                border: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
                color: var(--text) !important;
                font-size: 1rem !important;
            }

            [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
                min-height: 2.45rem;
                border: 1px solid var(--primary);
                border-radius: 999px;
                background: linear-gradient(135deg, var(--primary), var(--lavender));
                color: #FFFFFF;
                font-weight: 800;
            }

            .quick-actions {
                max-width: 820px;
                margin: 1rem auto 0;
            }

            .quick-actions div.stButton > button {
                min-height: 2.55rem;
                border-radius: 999px;
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.84);
                color: var(--text);
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
                font-size: 0.88rem;
                font-weight: 700;
            }

            .quick-actions div.stButton > button:hover {
                border-color: #C7D2FE;
                background: #F8FAFF;
                color: var(--primary-strong);
            }

            .chat-history {
                max-width: 860px;
                margin: 2.25rem auto 0;
            }

            [data-testid="stChatMessage"] {
                border: 1px solid var(--border);
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.92);
                box-shadow: 0 12px 34px rgba(15, 23, 42, 0.055);
                padding: 0.58rem 0.74rem;
                margin-bottom: 0.9rem;
            }

            .message-card,
            .empty-card,
            .setup-card,
            .debug-card {
                border: 1px solid var(--border);
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.92);
                box-shadow: 0 12px 34px rgba(15, 23, 42, 0.055);
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

            div.stButton > button,
            div.stDownloadButton > button {
                border: 1px solid var(--border);
                border-radius: 10px;
                background: #FFFFFF;
                color: var(--text);
                font-weight: 700;
            }

            div.stButton > button:hover {
                border-color: #BFDBFE;
                color: var(--primary-strong);
                background: var(--soft-blue);
            }

            @media (max-width: 920px) {
                .block-container {
                    padding: 0.75rem 1rem 2rem;
                }

                .hero h1 {
                    font-size: 2.1rem;
                }

                .top-status {
                    justify-content: flex-start;
                    margin-bottom: 1.8rem;
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
                <div class="sidebar-brand-copy">
                    <div class="sidebar-brand-title">{html.escape(BRAND_NAME)}</div>
                    <div class="sidebar-brand-subtitle">Toki-chan setup</div>
                </div>
            </div>
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

    render_main_status({"AWS_REGION": "Not connected", "HARNESS_ARN": ""})
    render_hero()
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
    st.session_state.setdefault("show_short_session_id", False)


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
        "Respond in Indonesian or English following the user's message. "
        "Use Notion-ready formatting only when the user asks for documentation.\n\n"
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


def render_debug_expander(secrets: dict[str, str]) -> None:
    with st.expander("Debug", expanded=False):
        try:
            client = create_agentcore_client(secrets)
            method_available = hasattr(client, "invoke_harness")
        except Exception:
            method_available = False

        st.caption("Sensitive values are masked. Access keys, secret keys, and tokens are never displayed.")
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


def render_sidebar(secrets: dict[str, str]) -> dict[str, Any]:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                {render_tokai_logo("tokai-logo-sidebar")}
                <div class="sidebar-brand-copy">
                    <div class="sidebar-brand-title">{html.escape(BRAND_NAME)}</div>
                    <div class="sidebar-brand-subtitle">Toki-chan Assistant</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
        if st.button("New Session", use_container_width=True):
            st.session_state.runtime_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.last_event_summary = []
            st.rerun()
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown('<div class="sidebar-section">File Upload</div>', unsafe_allow_html=True)
        uploaded_context = None
        uploaded_file = st.file_uploader("Attach context", type=["txt", "md", "csv", "json", "py", "log"])
        if uploaded_file:
            uploaded_context, truncated = read_uploaded_text(uploaded_file)
            size_kb = len(uploaded_file.getvalue()) / 1024
            st.caption(f"{uploaded_file.name} - {size_kb:.1f} KB")
            if truncated:
                st.caption(f"Limited to {MAX_UPLOAD_CHARS:,} characters.")
            with st.expander("Preview", expanded=False):
                st.text(uploaded_context[:3_000])

        st.markdown('<div class="sidebar-section">Memory</div>', unsafe_allow_html=True)
        if st.button("What do you remember?", use_container_width=True):
            queue_prompt(
                "Please recall what safe preferences or durable memories you have about me. "
                "Do not reveal secrets or sensitive data."
            )

        preference = st.text_area("Preference to remember", height=84, placeholder="Example: Prefer concise AWS diagrams.")
        if st.button("Remember", use_container_width=True):
            if preference.strip():
                queue_prompt(
                    "Please remember this safe, non-sensitive preference for future help. "
                    f"Preference: {preference.strip()}"
                )
            else:
                st.warning("Add a preference first.")

        forget_target = st.text_input("Forget / mark inactive", placeholder="Optional memory or preference")
        if st.button("Forget / Mark inactive", use_container_width=True):
            target = forget_target.strip() or "the relevant preference I previously asked you to remember"
            queue_prompt(f"Please forget or mark inactive: {target}. If this is ambiguous, ask one clarifying question.")

        st.markdown('<div class="sidebar-section">Debug</div>', unsafe_allow_html=True)
        render_debug_expander(secrets)

        st.markdown('<div class="sidebar-section">Account</div>', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    return {"uploaded_context": uploaded_context, "region": secrets["AWS_REGION"]}


def render_main_status(secrets: dict[str, str]) -> None:
    region = secrets.get("AWS_REGION", "Not configured")
    session_short = shorten(st.session_state.get("runtime_session_id", ""), 8, 4)
    connected_label = "AgentCore Connected" if secrets.get("HARNESS_ARN") else "AgentCore Not Configured"

    st.markdown(
        f"""
        <div class="top-status">
            <span class="status-pill connected">{html.escape(connected_label)}</span>
            <span class="status-pill">{html.escape(region)}</span>
            <span class="status-pill">Session: {html.escape(session_short)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="orb"></div>
            <h1>{html.escape(APP_TITLE)}</h1>
            <p>{html.escape(APP_SUBTITLE)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def process_user_prompt(user_prompt: str, uploaded_context: str | None = None) -> None:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    final_prompt = build_prompt(user_prompt, uploaded_context)
    with st.spinner("Invoking AgentCore Harness..."):
        output = invoke_harness(final_prompt)
    st.session_state.messages.append({"role": "assistant", "content": output})
    st.rerun()


def render_composer(uploaded_context: str | None) -> None:
    st.markdown(
        """
        <div class="composer-shell">
            <div class="composer-top">
                <span>Initiate a query or send a command to Toki-chan</span>
                <span>AgentCore Harness</span>
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
        process_user_prompt(prompt.strip(), uploaded_context)


def render_quick_actions(uploaded_context: str | None) -> None:
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    columns = st.columns([1, 1, 1])
    for index, (label, instruction) in enumerate(QUICK_ACTIONS):
        with columns[index % 3]:
            context = None if label == "What do you remember?" else uploaded_context
            if st.button(label, key=f"quick_{index}", use_container_width=True):
                process_user_prompt(instruction, context)
    st.markdown("</div>", unsafe_allow_html=True)


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


def render_chat(uploaded_context: str | None = None) -> None:
    pending_prompt = st.session_state.pending_prompt
    pending_context = st.session_state.pending_context
    if pending_prompt:
        st.session_state.pending_prompt = None
        st.session_state.pending_context = None
        process_user_prompt(pending_prompt, pending_context)
        return

    render_hero()
    render_composer(uploaded_context)
    render_quick_actions(uploaded_context)
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
    render_main_status(secrets)
    render_chat(controls["uploaded_context"])


if __name__ == "__main__":
    main()
