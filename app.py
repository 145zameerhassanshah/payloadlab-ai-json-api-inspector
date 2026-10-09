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



from utils.context_utils import (

    analyze_context,

    count_tokens,

)



from services.context_service import (

    apply_truncation,

    apply_chunking,

    apply_summarization,

)



from services.structured_prompt_service import (

    build_dynamic_system_prompt,

    build_dynamic_user_prompt,

    get_expected_schema,

    send_dynamic_structured_request,

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



default_state = {

    "payload": None,

    "result": None,

    "context_result": None,

    "dynamic_prompt_preview": None,

    "dynamic_result": None,

}



for key, value in default_state.items():

    if key not in st.session_state:

        st.session_state[key] = value





# --------------------------------------------------

# STYLING

# --------------------------------------------------



st.markdown(

    """

    <style>



    .block-container {

        max-width: 1450px;

        padding-top: 1.3rem;

        padding-bottom: 3rem;

    }



    [data-testid="stSidebar"] {

        border-right: 1px solid #E2E8F0;

    }



    .hero {

        background:

            linear-gradient(

                135deg,

                #F8FAFC 0%,

                #EFF6FF 100%

            );

        border: 1px solid #E2E8F0;

        border-radius: 18px;

        padding: 1.25rem 1.45rem;

        margin-bottom: 1rem;

    }



    .hero-kicker {

        color: #2563EB;

        font-size: 0.76rem;

        font-weight: 800;

        letter-spacing: 0.08em;

        text-transform: uppercase;

    }



    .hero-title {

        color: #0F172A;

        font-size: 2rem;

        font-weight: 800;

        margin: 0.15rem 0;

    }



    .hero-subtitle {

        color: #64748B;

        font-size: 0.98rem;

        margin: 0;

    }



    .pill {

        display: inline-block;

        border-radius: 999px;

        padding: 0.36rem 0.68rem;

        font-size: 0.77rem;

        font-weight: 800;

    }



    .pill-ok {

        background: #ECFDF5;

        color: #059669;

        border: 1px solid #A7F3D0;

    }



    .pill-bad {

        background: #FEF2F2;

        color: #DC2626;

        border: 1px solid #FECACA;

    }



    .section-note {

        color: #64748B;

        font-size: 0.92rem;

        margin-top: -0.25rem;

        margin-bottom: 0.9rem;

    }



    .section-label {

        color: #64748B;

        font-size: 0.74rem;

        font-weight: 800;

        letter-spacing: 0.07em;

        text-transform: uppercase;

        margin-bottom: 0.4rem;

    }



    .stButton > button {

        border-radius: 10px;

        font-weight: 700;

        min-height: 42px;

    }



    div[data-testid="stMetric"] {

        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 14px;

        padding: 0.8rem 1rem;

    }



    div[data-testid="stExpander"] {

        border-radius: 12px;

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



    st.caption(

        "Inspect • Recover • Optimize • Structure"

    )



    st.divider()



    workspace = st.radio(

        "Workspace",

        [

            "JSON Inspector",

            "Batch Reliability",

            "Context Management",

            "Dynamic Prompt Lab",

        ],

    )



    st.divider()



    st.markdown("### Environment")



    st.write(

        f"**Mode:** `{APP_ENV}`"

    )



    if OPENROUTER_API_KEY:

        st.success(

            "API key loaded"

        )

    else:

        st.error(

            "API key missing"

        )



    st.write(

        f"**Default Model:** `{DEFAULT_MODEL}`"

    )



    st.divider()



    workspace_descriptions = {



        "JSON Inspector": (

            "Build, validate, send, and inspect "

            "structured LLM API requests."

        ),



        "Batch Reliability": (

            "Process batches with retries, backoff, "

            "logging, checkpointing, and recovery."

        ),



        "Context Management": (

            "Analyze token budgets, detect overflow, "

            "and process long inputs safely."

        ),



        "Dynamic Prompt Lab": (

            "Build role-aware prompts and validate "

            "structured JSON output."

        ),

    }



    st.markdown(

        "### Workspace Purpose"

    )



    st.caption(

        workspace_descriptions[

            workspace

        ]

    )



    st.divider()



    st.markdown(

        "### Security"

    )



    st.caption(

        "Secrets are loaded from `.env` "

        "and should never be committed to Git."

    )





# --------------------------------------------------

# HEADER

# --------------------------------------------------



config_errors = validate_config()



if not config_errors:



    status_pill = (

        '<span class="pill pill-ok">'

        '● Config Ready'

        '</span>'

    )



else:



    status_pill = (

        '<span class="pill pill-bad">'

        '● Config Issue'

        '</span>'

    )





st.markdown(

    f"""

    <div class="hero">



        <div style="

            display:flex;

            justify-content:space-between;

            align-items:center;

            gap:1rem;

        ">



            <div>



                <div class="hero-kicker">

                    LLM ENGINEERING TOOLKIT

                </div>



                <div class="hero-title">

                    {APP_NAME}

                </div>



                <p class="hero-subtitle">

                    {APP_TAGLINE}

                </p>



            </div>



            <div>

                {status_pill}

            </div>



        </div>



    </div>

    """,

    unsafe_allow_html=True,

)





# ==================================================

# WORKSPACE 1 — JSON INSPECTOR

# ==================================================



if workspace == "JSON Inspector":



    st.markdown(

        "## JSON Inspector"

    )



    st.markdown(

        """

        <div class="section-note">

        Build → validate → send → inspect.

        Understand exactly what the application sends

        to and receives from an LLM API.

        </div>

        """,

        unsafe_allow_html=True,

    )





    with st.container(

        border=True

    ):



        st.markdown(

            "### 1) Build Request"

        )



        system_prompt = st.text_area(

            "System Prompt",

            value=(

                "You are a helpful AI assistant. "

                "Answer clearly and concisely."

            ),

            height=95,

        )



        user_prompt = st.text_area(

            "User Prompt",

            placeholder=(

                "Example: Explain JSON payloads simply."

            ),

            height=125,

        )





        c1, c2, c3 = st.columns(

            3

        )





        with c1:



            model = st.text_input(

                "Model",

                value=DEFAULT_MODEL,

            )





        with c2:



            temperature = st.slider(

                "Temperature",

                min_value=0.0,

                max_value=2.0,

                value=0.2,

                step=0.1,

            )





        with c3:



            max_tokens = st.number_input(

                "Max Tokens",

                min_value=100,

                max_value=4000,

                value=500,

                step=100,

            )





    button_1, button_2, button_3, spacer = st.columns(

        [

            1.1,

            1.25,

            0.8,

            4,

        ]

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





    if (

        build_clicked

        or send_clicked

    ):



        st.session_state.payload = (

            build_chat_payload(

                model=model,

                system_prompt=system_prompt,

                user_prompt=user_prompt,

                temperature=temperature,

                max_tokens=int(

                    max_tokens

                ),

            )

        )





    if send_clicked:



        if not user_prompt.strip():



            st.warning(

                "Please enter a user prompt."

            )



        else:



            with st.spinner(

                "Sending request and inspecting response..."

            ):



                st.session_state.result = (

                    send_llm_request(

                        st.session_state.payload

                    )

                )





    if st.session_state.payload:



        st.markdown(

            "### 2) Request Inspection"

        )





        payload_errors = (

            validate_payload(

                st.session_state.payload

            )

        )





        left_col, right_col = st.columns(

            [

                2,

                1,

            ],

            gap="large",

        )





        with left_col:



            with st.container(

                border=True

            ):



                st.markdown(

                    """

                    <div class="section-label">

                    JSON REQUEST PAYLOAD

                    </div>

                    """,

                    unsafe_allow_html=True,

                )



                st.json(

                    st.session_state.payload

                )





        with right_col:



            with st.container(

                border=True

            ):



                st.markdown(

                    """

                    <div class="section-label">

                    VALIDATION

                    </div>

                    """,

                    unsafe_allow_html=True,

                )





                if not payload_errors:



                    st.success(

                        "Payload is valid."

                    )





                    for field in [

                        "model",

                        "messages",

                        "temperature",

                        "max_tokens",

                    ]:



                        st.write(

                            f"✓ {field}"

                        )



                else:



                    st.error(

                        "Payload validation failed."

                    )





                    for error in payload_errors:



                        st.write(

                            f"• {error}"

                        )





    if st.session_state.result:



        st.markdown(

            "### 3) Response Inspection"

        )





        result = (

            st.session_state.result

        )





        if not result[

            "success"

        ]:



            st.error(

                "The request could not be completed."

            )



            st.write(

                f"**Failure stage:** "

                f"`{result['stage']}`"

            )





            for error in result[

                "errors"

            ]:



                st.write(

                    f"• {error}"

                )





            if (

                result[

                    "raw_response"

                ]

                is not None

            ):



                with st.expander(

                    "View Raw Error Response"

                ):



                    if isinstance(

                        result[

                            "raw_response"

                        ],

                        (

                            dict,

                            list,

                        ),

                    ):



                        st.json(

                            result[

                                "raw_response"

                            ]

                        )



                    else:



                        st.code(

                            str(

                                result[

                                    "raw_response"

                                ]

                            )

                        )





        else:



            st.success(

                "API request completed successfully."

            )





            parsed_col, meta_col = st.columns(

                [

                    2,

                    1,

                ],

                gap="large",

            )





            with parsed_col:



                with st.container(

                    border=True

                ):



                    st.markdown(

                        """

                        <div class="section-label">

                        PARSED AI RESPONSE

                        </div>

                        """,

                        unsafe_allow_html=True,

                    )



                    st.write(

                        result[

                            "parsed_content"

                        ]

                    )





            with meta_col:



                with st.container(

                    border=True

                ):



                    st.markdown(

                        """

                        <div class="section-label">

                        RESPONSE METADATA

                        </div>

                        """,

                        unsafe_allow_html=True,

                    )





                    metadata = (

                        result[

                            "metadata"

                        ]

                        or {}

                    )





                    metadata_items = [

                        (

                            "Response ID",

                            metadata.get(

                                "id"

                            ),

                        ),

                        (

                            "Model",

                            metadata.get(

                                "model"

                            ),

                        ),

                        (

                            "Prompt Tokens",

                            metadata.get(

                                "prompt_tokens"

                            ),

                        ),

                        (

                            "Completion Tokens",

                            metadata.get(

                                "completion_tokens"

                            ),

                        ),

                        (

                            "Total Tokens",

                            metadata.get(

                                "total_tokens"

                            ),

                        ),

                    ]





                    for (

                        label,

                        value,

                    ) in metadata_items:



                        st.write(

                            f"**{label}:**",

                            (

                                value

                                if value

                                is not None

                                else "Not provided"

                            ),

                        )





            with st.expander(

                "View Raw Nested API Response"

            ):



                st.json(

                    result[

                        "raw_response"

                    ]

                )





# ==================================================

# WORKSPACE 2 — BATCH RELIABILITY

# ==================================================



elif workspace == "Batch Reliability":



    st.markdown(

        "## 🛡️ Batch Reliability Lab"

    )



    st.markdown(

        """

        <div class="section-note">

        Process 50 synthetic patient notes safely

        while handling rate limits, timeouts,

        server errors, and interrupted workloads.

        </div>

        """,

        unsafe_allow_html=True,

    )





    checkpoint = (

        load_checkpoint()

    )



    status = (

        get_batch_status(

            checkpoint

        )

    )





    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(

        5

    )





    metric_1.metric(

        "Total Notes",

        TOTAL_NOTES,

    )



    metric_2.metric(

        "Completed",

        status[

            "completed"

        ],

    )



    metric_3.metric(

        "Failed / Retry",

        status[

            "failed"

        ],

    )



    metric_4.metric(

        "Not Yet Processed",

        status[

            "not_processed"

        ],

    )



    metric_5.metric(

        "Success Rate",

        f"{status['success_rate']:.0f}%",

    )





    st.progress(

        min(

            status[

                "completed"

            ]

            / TOTAL_NOTES,

            1.0,

        )

    )





    batch_tabs = st.tabs(

        [

            "Run Batch",

            "Recovery & Results",

            "Logs",

            "How It Works",

        ]

    )





    with batch_tabs[

        0

    ]:



        with st.container(

            border=True

        ):



            st.markdown(

                "### Processing Settings"

            )





            c1, c2, c3, c4 = st.columns(

                4

            )





            with c1:



                processing_mode = st.selectbox(

                    "Processing Mode",

                    [

                        "Simulation",

                        "Live LLM API",

                    ],

                )





            with c2:



                failure_mode = st.selectbox(

                    "Failure Mode",

                    [

                        "mixed",

                        "none",

                        "rate_limit",

                        "timeout",

                        "server_error",

                    ],

                    disabled=(

                        processing_mode

                        == "Live LLM API"

                    ),

                )





            with c3:



                max_retries = st.number_input(

                    "Max Retries",

                    min_value=0,

                    max_value=10,

                    value=3,

                    step=1,

                )





            with c4:



                base_delay = st.number_input(

                    "Base Delay (seconds)",

                    min_value=0.1,

                    max_value=30.0,

                    value=0.5,

                    step=0.1,

                )





        start_col, reset_col = st.columns(

            2

        )





        with start_col:



            start_batch = st.button(

                "▶ Start / Resume Batch",

                type="primary",

                use_container_width=True,

            )





        with reset_col:



            reset_batch = st.button(

                "↺ Reset Batch Progress",

                use_container_width=True,

            )





        if reset_batch:



            reset_checkpoint()



            st.success(

                "Saved batch progress was reset."

            )



            st.rerun()





        if start_batch:



            if (

                processing_mode

                == "Live LLM API"

                and not OPENROUTER_API_KEY

            ):



                st.error(

                    "OPENROUTER_API_KEY is missing."

                )



            else:



                selected_mode = (

                    "live"

                    if processing_mode

                    == "Live LLM API"

                    else "simulation"

                )





                with st.spinner(

                    "Processing batch..."

                ):



                    process_batch(

                        mode=selected_mode,

                        failure_mode=failure_mode,

                        max_retries=int(

                            max_retries

                        ),

                        base_delay=float(

                            base_delay

                        ),

                    )





                st.success(

                    "Batch run finished."

                )



                st.rerun()





    with batch_tabs[

        1

    ]:



        checkpoint = (

            load_checkpoint()

        )



        status = (

            get_batch_status(

                checkpoint

            )

        )





        left, right = st.columns(

            [

                1,

                1.6,

            ],

            gap="large",

        )





        with left:



            with st.container(

                border=True

            ):



                st.markdown(

                    "### Recovery State"

                )



                st.write(

                    f"**Completed:** "

                    f"{status['completed']} "

                    f"/ {TOTAL_NOTES}"

                )



                st.write(

                    f"**Retry needed:** "

                    f"{status['failed']}"

                )



                st.write(

                    f"**Not yet processed:** "

                    f"{status['not_processed']}"

                )





                failed_notes = (

                    checkpoint.get(

                        "failed",

                        [],

                    )

                )





                if failed_notes:



                    st.warning(

                        f"Failed note IDs: "

                        f"{failed_notes}"

                    )



                else:



                    st.success(

                        "No unresolved failed notes."

                    )





        with right:



            with st.container(

                border=True

            ):



                st.markdown(

                    "### Saved Summaries"

                )





                results = (

                    checkpoint.get(

                        "results",

                        {},

                    )

                )





                if results:



                    rows = [

                        {

                            "Note ID": note_id,

                            "Summary": summary,

                        }

                        for (

                            note_id,

                            summary,

                        )

                        in results.items()

                    ]





                    st.dataframe(

                        rows,

                        use_container_width=True,

                        hide_index=True,

                    )



                else:



                    st.info(

                        "No saved summaries yet."

                    )





    with batch_tabs[

        2

    ]:



        st.markdown(

            "### Recent Reliability Logs"

        )





        log_file = Path(

            "logs/batch_processing.log"

        )





        if log_file.exists():



            lines = (

                log_file.read_text(

                    encoding="utf-8",

                    errors="replace",

                )

                .splitlines()

            )





            st.code(

                "\n".join(

                    lines[

                        -80:

                    ]

                )

                if lines

                else "No log entries yet."

            )



        else:



            st.info(

                "No log file exists yet."

            )





    with batch_tabs[

        3

    ]:



        st.markdown(

            """

            ### Reliability Flow



            1. Load synthetic patient notes.

            2. Send or simulate the request.

            3. Retry temporary failures.

            4. Apply exponential backoff and jitter.

            5. Save every successful result.

            6. Resume without reprocessing completed notes.

            7. Log failure and recovery activity.

            """

        )





# ==================================================

# WORKSPACE 3 — CONTEXT MANAGEMENT

# ==================================================



elif workspace == "Context Management":



    st.markdown(

        "## Context Management Lab"

    )



    st.markdown(

        """

        <div class="section-note">

        Count tokens, detect context-window overflow,

        and prepare long inputs safely.

        </div>

        """,

        unsafe_allow_html=True,

    )





    with st.container(

        border=True

    ):



        st.markdown(

            "### 1) Input & Context Budget"

        )





        system_prompt_context = st.text_area(

            "System Prompt",

            value=(

                "You are a helpful assistant. "

                "Preserve important facts "

                "and respond clearly."

            ),

            height=80,

            key="context_system_prompt",

        )





        long_text = st.text_area(

            "Long Input",

            placeholder=(

                "Paste a long document, report, "

                "transcript, or article here..."

            ),

            height=220,

            key="context_long_text",

        )





        c1, c2, c3, c4 = st.columns(

            4

        )





        with c1:



            context_limit = st.number_input(

                "Context Window",

                min_value=512,

                max_value=200000,

                value=8192,

                step=512,

            )





        with c2:



            reserved_output = st.number_input(

                "Reserved Output Tokens",

                min_value=64,

                max_value=16000,

                value=1000,

                step=100,

            )





        with c3:



            other_context = st.number_input(

                "Other Context Tokens",

                min_value=0,

                max_value=50000,

                value=0,

                step=100,

            )





        with c4:



            safety_margin = st.number_input(

                "Safety Margin",

                min_value=0,

                max_value=4000,

                value=128,

                step=64,

            )





    analysis = analyze_context(

        text=long_text,

        context_limit=int(

            context_limit

        ),

        reserved_output_tokens=int(

            reserved_output

        ),

        system_prompt=system_prompt_context,

        other_context_tokens=int(

            other_context

        ),

        safety_margin=int(

            safety_margin

        ),

    )





    st.markdown(

        "### 2) Context Safety Analyzer"

    )





    m1, m2, m3, m4, m5 = st.columns(

        5

    )





    m1.metric(

        "Input Tokens",

        analysis[

            "input_tokens"

        ],

    )



    m2.metric(

        "Available Budget",

        analysis[

            "available_input_budget"

        ],

    )



    m3.metric(

        "Overflow",

        analysis[

            "overflow_tokens"

        ],

    )



    m4.metric(

        "Utilization",

        (

            f"{analysis['utilization_percent']:.1f}%"

        ),

    )



    m5.metric(

        "Status",

        analysis[

            "status"

        ],

    )





    budget = max(

        analysis[

            "available_input_budget"

        ],

        1,

    )





    st.progress(

        min(

            analysis[

                "input_tokens"

            ]

            / budget,

            1.0,

        )

    )





    if (

        analysis[

            "status"

        ]

        == "SAFE"

    ):



        st.success(

            "Input fits safely inside "

            "the calculated context budget."

        )





    elif (

        analysis[

            "status"

        ]

        == "WARNING"

    ):



        st.warning(

            "Input is close to the context limit."

        )





    else:



        st.error(

            f"Input exceeds the available budget by "

            f"{analysis['overflow_tokens']} tokens."

        )





    st.markdown(

        "### 3) Handling Strategy"

    )





    strategy = st.radio(

        "Strategy",

        [

            "Truncation",

            "Chunking",

            "Summarization",

        ],

        horizontal=True,

    )





    if strategy == "Truncation":



        keep = st.selectbox(

            "Keep which part?",

            [

                "start",

                "end",

            ],

        )





    elif strategy == "Chunking":



        c1, c2 = st.columns(

            2

        )





        with c1:



            chunk_size = st.number_input(

                "Chunk Size (tokens)",

                min_value=100,

                max_value=10000,

                value=1800,

                step=100,

            )





        with c2:



            overlap = st.number_input(

                "Chunk Overlap (tokens)",

                min_value=0,

                max_value=2000,

                value=150,

                step=50,

            )





    else:



        c1, c2 = st.columns(

            2

        )





        with c1:



            summary_chunk_size = st.number_input(

                "Summary Chunk Size",

                min_value=200,

                max_value=10000,

                value=1800,

                step=100,

            )





        with c2:



            summary_overlap = st.number_input(

                "Summary Overlap",

                min_value=0,

                max_value=2000,

                value=150,

                step=50,

            )





    process_context = st.button(

        "Process Long Input",

        type="primary",

        use_container_width=True,

    )





    if process_context:



        try:



            if not long_text.strip():



                raise ValueError(

                    "Paste some input text first."

                )





            if (

                analysis[

                    "available_input_budget"

                ]

                <= 0

            ):



                raise ValueError(

                    "No input token budget remains."

                )





            if strategy == "Truncation":



                result = apply_truncation(

                    text=long_text,

                    token_budget=(

                        analysis[

                            "available_input_budget"

                        ]

                    ),

                    keep=keep,

                )





            elif strategy == "Chunking":



                if overlap >= chunk_size:



                    raise ValueError(

                        "Chunk overlap must be smaller "

                        "than chunk size."

                    )





                result = apply_chunking(

                    text=long_text,

                    chunk_size=int(

                        chunk_size

                    ),

                    overlap=int(

                        overlap

                    ),

                )





            else:



                if not OPENROUTER_API_KEY:



                    raise ValueError(

                        "OPENROUTER_API_KEY is required "

                        "for summarization."

                    )





                if (

                    summary_overlap

                    >= summary_chunk_size

                ):



                    raise ValueError(

                        "Summary overlap must be smaller "

                        "than summary chunk size."

                    )





                result = apply_summarization(

                    text=long_text,

                    token_budget=(

                        analysis[

                            "available_input_budget"

                        ]

                    ),

                    chunk_size=int(

                        summary_chunk_size

                    ),

                    overlap=int(

                        summary_overlap

                    ),

                )





            st.session_state.context_result = (

                result

            )





            st.success(

                f"{strategy} completed successfully."

            )





        except Exception as error:



            st.error(

                f"Context processing failed: "

                f"{error}"

            )





    if st.session_state.context_result:



        result = (

            st.session_state.context_result

        )





        st.markdown(

            "### 4) Processed Result"

        )





        r1, r2, r3 = st.columns(

            3

        )





        r1.metric(

            "Original Tokens",

            result[

                "original_tokens"

            ],

        )



        r2.metric(

            "Processed Tokens",

            result[

                "processed_tokens"

            ],

        )



        r3.metric(

            "Chunks",

            len(

                result.get(

                    "chunks",

                    [],

                )

            ),

        )





        if (

            result[

                "strategy"

            ]

            == "chunking"

        ):



            for (

                index,

                chunk,

            ) in enumerate(

                result.get(

                    "chunks",

                    [],

                ),

                start=1,

            ):



                with st.expander(

                    f"Chunk {index} • "

                    f"{count_tokens(chunk)} tokens"

                ):



                    st.write(

                        chunk

                    )





        else:



            st.text_area(

                "Processed Text",

                value=(

                    result.get(

                        "processed_text",

                        "",

                    )

                    or ""

                ),

                height=280,

                disabled=True,

            )





# ==================================================
# WORKSPACE 4 — DYNAMIC PROMPT LAB
# ==================================================

else:

    st.markdown(
        "## 🧩 Dynamic Prompt & Structured Output Lab"
    )

    st.markdown(
        """
        <div class="section-note">
        Build context-aware prompts from runtime variables,
        request JSON-only model output,
        and validate the response against a schema.
        </div>
        """,
        unsafe_allow_html=True,
    )

    dynamic_tabs = st.tabs(
        [
            "Build & Send",
            "Prompt Preview",
            "Schema",
            "Validated Output",
        ]
    )

    # ----------------------------------------------
    # TAB 1 — BUILD & SEND
    # ----------------------------------------------

    with dynamic_tabs[0]:

        with st.container(border=True):

            st.markdown("### 1) Runtime Context")

            c1, c2, c3 = st.columns(3)

            with c1:
                user_role = st.selectbox(
                    "User Role",
                    [
                        "Patient",
                        "Physician",
                        "Nurse",
                        "Researcher",
                        "Healthcare Administrator",
                    ],
                )

            with c2:
                note_type = st.selectbox(
                    "Note Type",
                    [
                        "Progress Note",
                        "Discharge Summary",
                        "Radiology Report",
                        "Lab Report",
                        "Consultation Note",
                        "Emergency Note",
                    ],
                )

            with c3:
                output_style = st.selectbox(
                    "Output Style",
                    [
                        "Patient-Friendly JSON",
                        "Clinical JSON",
                        "Research JSON",
                    ],
                )

            patient_context = st.text_area(
                "Patient Context",
                value=(
                    "Adult outpatient with a "
                    "history of hypertension."
                ),
                height=95,
                help=(
                    "Use synthetic or de-identified "
                    "information only."
                ),
            )

            clinical_note = st.text_area(
                "Clinical Note",
                value=(
                    "Pt presents with SOB x 2 days. "
                    "CXR shows RLL infiltrate. "
                    "BP 150/95 mmHg. "
                    "Possible lower respiratory "
                    "tract infection."
                ),
                height=150,
            )

        button_1, button_2, button_3 = st.columns(3)

        with button_1:
            build_dynamic_clicked = st.button(
                "Build Dynamic Prompt",
                use_container_width=True,
            )

        with button_2:
            send_dynamic_clicked = st.button(
                "Send & Validate JSON",
                type="primary",
                use_container_width=True,
            )

        with button_3:
            clear_dynamic_clicked = st.button(
                "Clear Result",
                use_container_width=True,
            )

        if clear_dynamic_clicked:
            st.session_state.dynamic_prompt_preview = None
            st.session_state.dynamic_result = None
            st.rerun()

        # Build and save prompt before displaying it.
        if build_dynamic_clicked or send_dynamic_clicked:

            system_prompt_dynamic = build_dynamic_system_prompt(
                user_role=user_role,
                patient_context=patient_context,
                note_type=note_type,
                output_style=output_style,
            )

            user_prompt_dynamic = build_dynamic_user_prompt(
                clinical_note=clinical_note,
            )

            st.session_state.dynamic_prompt_preview = {
                "system_prompt": system_prompt_dynamic,
                "user_prompt": user_prompt_dynamic,
            }

        # Immediate visible feedback for Build Dynamic Prompt.
        if build_dynamic_clicked:

            st.success(
                "Dynamic prompt built successfully."
            )

            st.markdown(
                "### Generated Prompt Preview"
            )

            with st.expander(
                "View Dynamic System Prompt",
                expanded=True,
            ):
                st.code(
                    st.session_state.dynamic_prompt_preview[
                        "system_prompt"
                    ],
                    language="text",
                )

            with st.expander(
                "View User Prompt"
            ):
                st.code(
                    st.session_state.dynamic_prompt_preview[
                        "user_prompt"
                    ],
                    language="text",
                )

        # Real API call + structured JSON validation.
        if send_dynamic_clicked:

            if not clinical_note.strip():
                st.warning(
                    "Enter a clinical note first."
                )

            elif not patient_context.strip():
                st.warning(
                    "Enter patient context first."
                )

            elif not OPENROUTER_API_KEY:
                st.error(
                    "OPENROUTER_API_KEY is missing. "
                    "Add it to `.env` before sending."
                )

            else:
                with st.spinner(
                    "Building prompt, calling the LLM, "
                    "parsing JSON, and validating schema..."
                ):
                    st.session_state.dynamic_result = (
                        send_dynamic_structured_request(
                            user_role=user_role,
                            patient_context=patient_context,
                            note_type=note_type,
                            output_style=output_style,
                            clinical_note=clinical_note,
                        )
                    )

                result = st.session_state.dynamic_result

                if result["success"]:
                    st.success(
                        "Valid JSON returned and "
                        "schema validation passed."
                    )

                else:
                    st.error(
                        f"Structured output failed at stage: "
                        f"`{result['stage']}`"
                    )

                    if result.get("errors"):
                        st.markdown(
                            "#### What went wrong"
                        )

                        for error in result["errors"]:
                            st.code(
                                str(error),
                                language="text",
                            )

                    if result.get("raw_output"):
                        with st.expander(
                            "Inspect Raw Model Output",
                            expanded=True,
                        ):
                            st.code(
                                result["raw_output"],
                                language="text",
                            )

    # ----------------------------------------------
    # TAB 2 — PROMPT PREVIEW
    # ----------------------------------------------

    with dynamic_tabs[1]:

        st.markdown(
            "### Dynamic Prompt Preview"
        )

        preview = st.session_state.dynamic_prompt_preview

        if preview:

            st.success(
                "Prompt is ready."
            )

            with st.expander(
                "System Prompt",
                expanded=True,
            ):
                st.code(
                    preview["system_prompt"],
                    language="text",
                )

            with st.expander(
                "User Prompt",
                expanded=True,
            ):
                st.code(
                    preview["user_prompt"],
                    language="text",
                )

        else:
            st.info(
                "Build the dynamic prompt first."
            )

    # ----------------------------------------------
    # TAB 3 — SCHEMA
    # ----------------------------------------------

    with dynamic_tabs[2]:

        st.markdown(
            "### Expected JSON Schema"
        )

        st.caption(
            "The model response must match this schema "
            "before the application accepts it."
        )

        st.json(
            get_expected_schema()
        )

    # ----------------------------------------------
    # TAB 4 — VALIDATED OUTPUT
    # ----------------------------------------------

    with dynamic_tabs[3]:

        st.markdown(
            "### Structured Validation Result"
        )

        result = st.session_state.dynamic_result

        if not result:
            st.info(
                "Send a structured request "
                "to see validation results."
            )

        elif not result["success"]:

            st.error(
                f"Validation failed at stage: "
                f"`{result['stage']}`"
            )

            if result.get("errors"):
                st.markdown(
                    "#### Validation Details"
                )

                for error in result["errors"]:
                    st.code(
                        str(error),
                        language="text",
                    )

            if result.get("parsed_json") is not None:
                with st.expander(
                    "Parsed JSON Before Schema Validation"
                ):
                    st.json(
                        result["parsed_json"]
                    )

            if result.get("raw_output"):
                with st.expander(
                    "Raw Model Output",
                    expanded=True,
                ):
                    st.code(
                        result["raw_output"],
                        language="text",
                    )

        else:

            validated = result["validated_output"]

            st.success(
                "JSON parsed successfully and "
                "matched the expected schema."
            )

            metric_1, metric_2, metric_3 = st.columns(3)

            metric_1.metric(
                "Key Findings",
                len(
                    validated.get(
                        "key_findings",
                        [],
                    )
                ),
            )

            metric_2.metric(
                "Measurements",
                len(
                    validated.get(
                        "measurements",
                        [],
                    )
                ),
            )

            metric_3.metric(
                "Uncertainties",
                len(
                    validated.get(
                        "uncertainties",
                        [],
                    )
                ),
            )

            with st.container(border=True):
                st.markdown(
                    "### Summary"
                )
                st.write(
                    validated["summary"]
                )

            left, right = st.columns(2)

            with left:

                with st.container(border=True):
                    st.markdown(
                        "### Key Findings"
                    )

                    findings = validated.get(
                        "key_findings",
                        [],
                    )

                    if findings:
                        for finding in findings:
                            st.write(
                                f"• {finding}"
                            )
                    else:
                        st.caption(
                            "No key findings returned."
                        )

                with st.container(border=True):
                    st.markdown(
                        "### Measurements"
                    )

                    measurements = validated.get(
                        "measurements",
                        [],
                    )

                    if measurements:
                        st.dataframe(
                            measurements,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.caption(
                            "No measurements returned."
                        )

            with right:

                with st.container(border=True):
                    st.markdown(
                        "### Uncertainties"
                    )

                    uncertainties = validated.get(
                        "uncertainties",
                        [],
                    )

                    if uncertainties:
                        for uncertainty in uncertainties:
                            st.write(
                                f"• {uncertainty}"
                            )
                    else:
                        st.caption(
                            "No uncertainties returned."
                        )

                with st.container(border=True):
                    st.markdown(
                        "### Important Terms"
                    )

                    important_terms = validated.get(
                        "important_terms",
                        [],
                    )

                    if important_terms:
                        st.dataframe(
                            important_terms,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.caption(
                            "No important terms returned."
                        )

            st.info(
                validated["safety_note"]
            )

            with st.expander(
                "Validated JSON"
            ):
                st.json(
                    validated
                )

            with st.expander(
                "Raw Model Output"
            ):
                st.code(
                    result["raw_output"],
                    language="json",
                )


# --------------------------------------------------

# FOOTER

# --------------------------------------------------



st.write("")



st.caption(

    "PayloadLab AI • JSON Inspection • "

    "Reliability • Context Management • "

    "Structured Prompting"

)