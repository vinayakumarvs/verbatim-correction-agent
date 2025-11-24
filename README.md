# Verbatim Correction Agent

A specialized document processing tool that combines deterministic rule-based transformations with LLM-powered grammar correction to edit DOCX files.

## Project Overview

This project provides a Streamlit-based web interface for processing Microsoft Word (`.docx`) documents. It applies a two-stage correction pipeline:
1.  **MCP (Model Context Protocol) Rules**: A set of deterministic, rule-based transformations (e.g., correcting "a/an" usage, specific phrase replacements).
2.  **LLM Grammar Correction**: An optional step that uses OpenAI's GPT models to correct grammar, punctuation, and phrasing while preserving the original meaning and named entities.

## Features

### 1. Rule-Based Transformations (MCP Tools)
The project utilizes the Model Context Protocol (MCP) to define and execute specific editing rules. These are implemented in `mcp_rules.py` and include:
-   **`correct_a_an_spacy_tool`**: Context-aware correction of indefinite articles ("a" vs "an") using SpaCy for phonetic analysis (e.g., handles "an hour", "a university").
-   **`replace_absent_the_tool`**: Automatically replaces the phrase "absent the" with "without the".
-   **`replace_abu_dhabi_expand_tool`**: Expands "Abu Dhabi" to "Abu Dhabi Sovereign".

### 2. LLM Grammar Correction
-   **Context-Aware Editing**: Uses OpenAI's GPT-4o-mini (default) to correct grammar and punctuation.
-   **Strict Output Control**: The LLM client is engineered to return *only* the corrected text, stripping away any conversational filler (e.g., "Here is the corrected text").
-   **Empty Line Handling**: Smart processing skips empty or whitespace-only lines to prevent unnecessary API calls and hallucinations.

### 3. User Interface
-   **Streamlit Web App**: A clean, responsive UI for uploading files and configuring options.
-   **Real-time Progress**: Visual progress bar and status updates during document processing.
-   **Configurable Pipeline**: Users can toggle MCP rules and LLM correction independently, and choose the order of execution.

## Architecture

-   **Frontend**: Streamlit (`streamlit_app.py`)
-   **Core Logic**: `DocProcessor` (`doc_processor.py`) orchestrates the pipeline.
-   **LLM Integration**: `LLMClient` (`llm_client.py`) handles communication with OpenAI, using the modern SDK patterns.
-   **Rules Engine**: `mcp_rules.py` defines the transformation tools using `FastMCP` and `spaCy`.

## Installation & Usage

1.  **Prerequisites**:
    -   Python 3.10+
    -   OpenAI API Key

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

3.  **Run the Application**:
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    streamlit run streamlit_app.py
    ```

## Project Plan & Roadmap

### Phase 1: Core Functionality (Completed)
-   [x] Basic DOCX reading and writing.
-   [x] Integration of MCP-based transformation rules.
-   [x] Initial LLM integration for grammar correction.
-   [x] Streamlit UI for file upload and processing.

### Phase 2: Refinement & Stability (Current Focus)
-   [x] **Fix LLM Client**: Updated to use modern OpenAI SDK (v1+).
-   [x] **Output Cleaning**: Implemented strict prompting to remove conversational filler from LLM outputs.
-   [x] **Empty Input Handling**: Added logic to skip empty lines, preventing LLM hallucinations.
-   [ ] **Error Handling**: Improve resilience against API timeouts or malformed documents.

### Phase 3: Advanced Features (Future)
-   **Custom Rule Builder**: Allow users to define simple find/replace rules via the UI.
-   **Diff View**: Show a side-by-side comparison of the original and processed text before downloading.
-   **Batch Processing**: Support uploading and processing multiple files simultaneously.
-   **Local LLM Support**: Add support for running local models (e.g., Llama 3 via Ollama) for privacy-focused grammar correction.
