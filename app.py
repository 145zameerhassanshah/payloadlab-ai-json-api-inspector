import json
from pathlib import Path

import streamlit as st

from config import (
    APP_NAME,
    APP_TAGLINE,
    APP_ENV,
    DEFAULT_MODEL,
    OPENROUTER_API_KEY,
    validate_config,
)
from payload_builder import build_chat_payload
from validators import validate_payload
from services.llm_service import send_llm_request
from services.batch_service import (
    TOTAL_NOTES,
    process_batch,
    get_batch_status,
)
from utils.checkpoint import (
    load_checkpoint,
    reset_checkpoint,
)


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "payload" not in st.session_state:
    st.session_state.payload = None

if "result" not in st.session_state:
    st.session_state.result = None


# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #E2E8F0;
    }

    .hero-kicker {
        color: #2563EB;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 750;
        color: #0F172A;
        margin-top: 0.2rem;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        color: #64748B;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }

    .status-ok {
        display: inline-block;
        background: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        border-radius: 999px;
        padding: 0.35rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .status-bad {
        display: inline-block;
        background: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
        border-radius: 999px;
        padding: 0.35rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .section-label {
        color: #64748B;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🧪 PayloadLab AI")
    st.caption("Inspect. Validate. Understand AI API Data.")

    st.divider()

    workspace = st.radio(
        "Workspace",
        [
            "JSON Inspector",
            "Batch Reliability",
        ],
    )

    st.divider()

    st.markdown("### Environment")
    st.write(f"**Mode:** {APP_ENV}")

    if OPENROUTER_API_KEY:
        st.success("API key loaded")
    else:
        st.error("API key missing")

    st.write(f"**Default Model:** `{DEFAULT_MODEL}`")

    st.divider()

    if workspace == "JSON Inspector":
        st.markdown("### What this tool does")
        st.caption(
            "Builds JSON payloads, validates required fields, sends "
            "LLM API requests, parses nested responses, and displays "
            "raw and parsed data."
        )
    else:
        st.markdown("### Reliability Lab")
        st.caption(
            "Processes a resumable batch of 50 synthetic patient notes "
            "with retry logic, exponential backoff, logging, and "
            "checkpoint recovery."
        )

    st.divider()

    st.markdown("### Security")
    st.caption(
        "Secrets are loaded from .env and should never be committed to Git."
    )


# --------------------------------------------------
# SHARED HEADER
# --------------------------------------------------

left, right = st.columns(
    [5, 1],
    vertical_alignment="center",
)

with left:
    st.markdown(
        '<div class="hero-kicker">AI API DEVELOPER TOOL</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="hero-title">{APP_NAME}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="hero-subtitle">{APP_TAGLINE}</div>',
        unsafe_allow_html=True,
    )

with right:
    config_errors = validate_config()

    if not config_errors:
        st.markdown(
            '<div class="status-ok">● Config Ready</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-bad">● Config Issue</div>',
            unsafe_allow_html=True,
        )


# ==================================================
# WORKSPACE 1: JSON INSPECTOR
# ==================================================

if workspace == "JSON Inspector":

    with st.container(border=True):
        st.markdown("### Build Request")

        system_prompt = st.text_area(
            "System Prompt",
            value=(
                "You are a helpful AI assistant. "
                "Answer clearly and concisely."
            ),
            height=100,
        )

        user_prompt = st.text_area(
            "User Prompt",
            placeholder="Example: Explain JSON payloads simply.",
            height=140,
        )

        settings_1, settings_2, settings_3 = st.columns(3)

        with settings_1:
            model = st.text_input(
                "Model",
                value=DEFAULT_MODEL,
            )

        with settings_2:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.2,
                step=0.1,
            )

        with settings_3:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=500,
                step=100,
                help="Use 300–500 or more for reasoning-capable models.",
            )

    button_1, button_2, button_3, spacer = st.columns(
        [1.2, 1.3, 1, 4]
    )

    with button_1:
        build_clicked = st.button(
            "Build Payload",
            use_container_width=True,
        )

    with button_2:
        send_clicked = st.button(
            "Send API Request",
            type="primary",
            use_container_width=True,
        )

    with button_3:
        clear_clicked = st.button(
            "Clear",
            use_container_width=True,
        )

    if clear_clicked:
        st.session_state.payload = None
        st.session_state.result = None
        st.rerun()

    if build_clicked or send_clicked:
        payload = build_chat_payload(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=int(max_tokens),
        )
        st.session_state.payload = payload

    if send_clicked:
        if not user_prompt.strip():
            st.warning("Please enter a user prompt.")
        else:
            with st.spinner(
                "Sending request and inspecting response..."
            ):
                result = send_llm_request(
                    st.session_state.payload
                )
            st.session_state.result = result

    if st.session_state.payload:
        st.write("")
        st.markdown("## Request Inspection")

        payload_errors = validate_payload(
            st.session_state.payload
        )

        left_col, right_col = st.columns(
            [2, 1],
            gap="large",
        )

        with left_col:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-label">JSON REQUEST PAYLOAD</div>',
                    unsafe_allow_html=True,
                )
                st.json(st.session_state.payload)

        with right_col:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-label">VALIDATION</div>',
                    unsafe_allow_html=True,
                )

                if not payload_errors:
                    st.success("Payload is valid.")
                    st.write("✓ model")
                    st.write("✓ messages")
                    st.write("✓ temperature")
                    st.write("✓ max_tokens")
                else:
                    st.error("Payload validation failed.")
                    for error in payload_errors:
                        st.write(f"• {error}")

    if st.session_state.result:
        result = st.session_state.result

        st.write("")
        st.markdown("## Response Inspection")

        if not result["success"]:
            st.error("The request could not be completed.")
            st.write(
                f"**Failure stage:** `{result['stage']}`"
            )

            for error in result["errors"]:
                st.write(f"• {error}")

            if result["raw_response"] is not None:
                with st.expander("View Raw Error Response"):
                    if isinstance(
                        result["raw_response"],
                        (dict, list),
                    ):
                        st.json(result["raw_response"])
                    else:
                        st.code(str(result["raw_response"]))

        else:
            st.success("API request completed successfully.")

            parsed_col, meta_col = st.columns(
                [2, 1],
                gap="large",
            )

            with parsed_col:
                with st.container(border=True):
                    st.markdown(
                        '<div class="section-label">'
                        'PARSED AI RESPONSE'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.write(result["parsed_content"])

            with meta_col:
                with st.container(border=True):
                    st.markdown(
                        '<div class="section-label">'
                        'RESPONSE METADATA'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    metadata = result["metadata"] or {}

                    st.write(
                        "**Response ID:**",
                        metadata.get("id") or "Not provided",
                    )
                    st.write(
                        "**Model:**",
                        metadata.get("model") or "Not provided",
                    )
                    st.write(
                        "**Prompt Tokens:**",
                        metadata.get("prompt_tokens")
                        if metadata.get("prompt_tokens") is not None
                        else "Not provided",
                    )
                    st.write(
                        "**Completion Tokens:**",
                        metadata.get("completion_tokens")
                        if metadata.get("completion_tokens") is not None
                        else "Not provided",
                    )
                    st.write(
                        "**Total Tokens:**",
                        metadata.get("total_tokens")
                        if metadata.get("total_tokens") is not None
                        else "Not provided",
                    )

            with st.expander("View Raw Nested API Response"):
                st.json(result["raw_response"])

    if (
        st.session_state.payload is None
        and st.session_state.result is None
    ):
        st.write("")
        with st.container(border=True):
            st.markdown(
                "### Start by building a JSON payload"
            )
            st.caption(
                "Enter a prompt, configure request settings, and "
                "select Build Payload to inspect the request before "
                "sending it to the API."
            )


# ==================================================
# WORKSPACE 2: BATCH RELIABILITY
# ==================================================

elif workspace == "Batch Reliability":

    st.markdown("## Batch Reliability Lab")
    st.caption(
        "Process 50 synthetic patient notes safely while handling "
        "rate limits, timeouts, connection failures, and temporary "
        "server errors without losing completed work."
    )

    checkpoint = load_checkpoint()
    status = get_batch_status(checkpoint)

    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

    metric_1.metric("Total Notes", TOTAL_NOTES)
    metric_2.metric("Completed", status["completed"])
    metric_3.metric("Failed / Retry", status["failed"])
    metric_4.metric("Not Yet Processed", status["not_processed"])
    metric_5.metric(
        "Success Rate",
        f"{status['success_rate']:.0f}%",
    )

    st.progress(
        min(
            status["completed"] / TOTAL_NOTES,
            1.0,
        )
    )

    st.divider()

    with st.container(border=True):
        st.markdown("### Processing Settings")

        mode_col, failure_col, retry_col, delay_col = st.columns(4)

        with mode_col:
            processing_mode = st.selectbox(
                "Processing Mode",
                [
                    "Simulation",
                    "Live LLM API",
                ],
                help=(
                    "Simulation deliberately creates failures. "
                    "Live mode sends real OpenRouter requests."
                ),
            )

        with failure_col:
            failure_mode = st.selectbox(
                "Simulated Failure Mode",
                [
                    "mixed",
                    "none",
                    "rate_limit",
                    "timeout",
                    "server_error",
                ],
                disabled=(processing_mode == "Live LLM API"),
            )

        with retry_col:
            max_retries = st.number_input(
                "Max Retries",
                min_value=0,
                max_value=10,
                value=3,
                step=1,
            )

        with delay_col:
            base_delay = st.number_input(
                "Base Delay (seconds)",
                min_value=0.1,
                max_value=30.0,
                value=0.5,
                step=0.1,
            )

        if processing_mode == "Live LLM API":
            st.warning(
                "Live mode can send up to 50 API requests. "
                "Use a valid API key and expect provider rate limits."
            )
        else:
            st.info(
                "Simulation mode intentionally creates temporary "
                "failures so retry and recovery logic can be tested."
            )

    start_col, reset_col = st.columns(2)

    with start_col:
        start_batch = st.button(
            "Start / Resume Batch",
            type="primary",
            use_container_width=True,
        )

    with reset_col:
        reset_batch = st.button(
            "Reset Batch Progress",
            use_container_width=True,
        )

    if reset_batch:
        reset_checkpoint()
        st.success("Saved batch progress was reset.")
        st.rerun()

    if start_batch:
        if processing_mode == "Live LLM API" and not OPENROUTER_API_KEY:
            st.error(
                "OPENROUTER_API_KEY is missing. "
                "Add it to .env before using Live LLM API mode."
            )
        else:
            selected_mode = (
                "live"
                if processing_mode == "Live LLM API"
                else "simulation"
            )

            with st.spinner(
                "Processing batch. Completed notes are saved after every success..."
            ):
                result = process_batch(
                    mode=selected_mode,
                    failure_mode=failure_mode,
                    max_retries=int(max_retries),
                    base_delay=float(base_delay),
                )

            st.success(
                "Batch run finished. Saved progress is ready for resume."
            )
            st.rerun()

    st.divider()

    checkpoint = load_checkpoint()
    status = get_batch_status(checkpoint)

    failed_col, results_col = st.columns(
        [1, 2],
        gap="large",
    )

    with failed_col:
        with st.container(border=True):
            st.markdown("### Failed / Retry Needed")

            failed_notes = checkpoint.get("failed", [])

            if failed_notes:
                st.warning(
                    "These notes can be retried by clicking "
                    "**Start / Resume Batch** again."
                )
                st.write(failed_notes)
            else:
                st.success("No failed notes.")

            st.markdown("### Recovery State")
            st.write(
                f"**Completed:** {status['completed']} / {TOTAL_NOTES}"
            )
            st.write(
                f"**Retry needed:** {status['failed']}"
            )
            st.write(
                f"**Not yet processed:** {status['not_processed']}"
            )

    with results_col:
        with st.container(border=True):
            st.markdown("### Saved Results")

            results = checkpoint.get("results", {})

            if results:
                st.caption(
                    "Results are checkpointed after each successful note."
                )
                st.json(results)
            else:
                st.info("No processed results yet.")

    log_file = Path("logs/batch_processing.log")

    if log_file.exists():
        with st.expander("View Recent Reliability Logs"):
            lines = log_file.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()

            recent_lines = lines[-60:]
            st.code(
                "\n".join(recent_lines)
                if recent_lines
                else "No log entries yet."
            )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.write("")
st.caption(
    "PayloadLab AI • JSON Inspection • API Reliability • Resumable Batch Processing"
)
