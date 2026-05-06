import uuid
import boto3
import streamlit as st

st.set_page_config(
    page_title="AgentCore Chat",
    page_icon="🤖",
    layout="centered"
)

APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")

if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("AgentCore Chat Login")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password")

        st.stop()

st.title("AgentCore Chat")
st.caption("Simple Streamlit UI for Amazon Bedrock AgentCore Harness")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "runtime_session_id" not in st.session_state:
    st.session_state.runtime_session_id = str(uuid.uuid4())

client = boto3.client(
    "bedrock-agentcore",
    region_name=st.secrets["AWS_REGION"],
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
)

HARNESS_ARN = st.secrets["HARNESS_ARN"]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Ask AgentCore...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.invoke_harness(
                    harnessArn=HARNESS_ARN,
                    runtimeSessionId=st.session_state.runtime_session_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )

                output = ""

                for event in response.get("stream", []):
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"].get("delta", {})
                        if "text" in delta:
                            output += delta["text"]

                    elif "runtimeClientError" in event:
                        output += f"\nError: {event['runtimeClientError'].get('message', '')}"

                    elif "validationException" in event:
                        output += f"\nValidation error: {event['validationException']}"

                if not output:
                    output = "No response from AgentCore Harness."

                st.write(output)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": output
                })

            except Exception as e:
                st.error(f"Error invoking AgentCore Harness: {e}")
