# streamlit_app.py
import streamlit as st
import tempfile
import os
import importlib
import inspect
import asyncio
from typing import List, Callable, Any

from llm_client import LLMClient
from doc_processor import DocProcessor
from dotenv import load_dotenv
import threading
# Load environment variables from .env if present
load_dotenv()

# Config: module name for MCP tools (default: mcp_rules.py)
MCP_MODULE_NAME = os.environ.get("MCP_MODULE", "mcp_rules")

# LLM model to use for grammar correction
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

st.set_page_config(page_title="DOCX: MCP-only Rules + Grammar Processor", layout="wide")
st.title("DOCX Processor — MCP-only custom rules + LLM grammar")
st.write("This app applies **only** MCP-provided transformation tools (from `mcp_rules.py`) and optional LLM grammar correction. "
         "Local replacement rules are intentionally excluded.")



# Discover MCP tool functions from the MCP module (functions that end with '_tool')
mcp_funcs: List[Callable[[str], Any]] = []
mcp_available = False
mcp_import_errors = None
mcp_mod = None

try:
    # reload if already imported (development friendliness)
    if MCP_MODULE_NAME in importlib.sys.modules:
        importlib.reload(importlib.import_module(MCP_MODULE_NAME))
    mcp_mod = importlib.import_module(MCP_MODULE_NAME)

    # collect async and sync functions named *_tool
    for name, obj in inspect.getmembers(mcp_mod, inspect.iscoroutinefunction):
        if name.endswith("_tool"):
            mcp_funcs.append(obj)
    for name, obj in inspect.getmembers(mcp_mod, inspect.isfunction):
        if name.endswith("_tool") and obj not in mcp_funcs:
            mcp_funcs.append(obj)

    if mcp_funcs:
        mcp_available = True
except Exception as e:
    mcp_import_errors = str(e)
    mcp_mod = None

# UI: show discovered tools and options on left, file upload on right
left, right = st.columns([1, 2])

with left:
    st.header("MCP Rules (tools)")
    if mcp_available:
        st.success(f"Found MCP module '{MCP_MODULE_NAME}' with {len(mcp_funcs)} tool(s).")
        st.write("Discovered MCP tool functions (executed sequentially on each text block):")
        for f in mcp_funcs:
            st.markdown(f"- **{f.__name__}**")
        st.markdown("---")
        st.info("Only MCP transforms from the above functions will be applied. Local replacement rules are disabled in this UI.")
    else:
        st.warning("No MCP module loaded. Place 'mcp_rules.py' in the app folder (or set MCP_MODULE env var).")
        if mcp_import_errors:
            st.write("Import error:", mcp_import_errors)
        st.write("You can still use the LLM grammar correction step if configured.")

    st.markdown("---")
    st.header("Options")
    apply_mcp = st.checkbox("Apply MCP transforms", value=True, help="If disabled, MCP tools will not be run.")
    apply_grammar = st.checkbox("Apply LLM grammar correction (requires OPENAI_API_KEY)", value=False)
    apply_mcp_first = st.checkbox("Apply MCP transforms before LLM grammar correction", value=True)

with right:
    st.header("Process a .docx")
    uploaded_file = st.file_uploader("Upload .docx", type=["docx"])
    if uploaded_file:
        st.info(f"Uploaded: {uploaded_file.name}")
        # Save upload to temp file
        t_in = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        t_in.write(uploaded_file.read())
        t_in.flush()
        t_in.close()

        if st.button("Process file"):
            # Prepare transform functions (possibly wrapped to handle async)
            transforms = []
            if apply_mcp and mcp_available:
                transforms = list(mcp_funcs)

            # Prepare LLM client if requested and key exists
            llm = None
            if apply_grammar:
                if os.getenv("OPENAI_API_KEY"):
                    llm = LLMClient(model=OPENAI_MODEL)
                else:
                    st.warning("OPENAI_API_KEY not set — grammar step will be skipped.")
                    llm = None

            # Create DocProcessor that uses only MCP transforms and LLM; no local rules manager
            dp = DocProcessor(
                rules_manager=None,  # explicit: no local replacement rules
                llm_client=llm,
                apply_grammar=apply_grammar,
                mcp_transform_funcs=transforms
            )

            out_fd = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            out_path = out_fd.name
            out_fd.close()

            try:
                dp.process_docx(t_in.name, out_path, apply_rules_first=apply_mcp_first)
                st.success("Processing finished.")
                with open(out_path, "rb") as f:
                    data = f.read()
                    st.download_button(
                        "Download processed .docx",
                        data=data,
                        file_name=f"processed_{uploaded_file.name}",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            except Exception as e:
                st.error(f"Processing failed: {e}")
            finally:
                # cleanup upload temp
                try:
                    os.unlink(t_in.name)
                except Exception:
                    pass

    else:
        st.info("Upload a .docx file to enable processing options.")

st.markdown("---")
st.write("Notes:")
st.write("- This app intentionally excludes local replacement rules; only MCP tool functions (from `mcp_rules.py`) are applied.")
st.write("- MCP tool functions must follow the naming convention `*_tool` and accept a single `text: str` argument and return transformed text (sync or async).")
st.write("- MCP transforms are executed sequentially for each paragraph/cell/header/footer in the document.")
st.write("- LLM grammar correction is applied per text block and may incur API costs (if enabled).")
