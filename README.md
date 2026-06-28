# MarkItDown Web UI

MarkItDown Web UI is a local Streamlit interface for the [MarkItDown](https://github.com/microsoft/markitdown) conversion engine. It provides a simple browser-based workflow for turning documents such as PDF, DOCX, PPTX, XLSX, images, and audio files into Markdown for LLM, search, and knowledge-management workflows.

![MarkItDown Web UI screenshot](./screenshot.JPG)

## Overview

This project packages a lightweight web front end around [MarkItDown](https://github.com/microsoft/markitdown) so files can be converted without using the command line directly. The application is designed for local use and emphasizes straightforward setup, predictable file handling, and a clear conversion flow.

## Key Capabilities

- Browser-based interface built with Streamlit
- Local document conversion through MarkItDown
- Drag-and-drop upload flow for common file types
- Explicit opt-in for formats that may trigger third-party transcription
- Markdown output that can be reviewed and downloaded immediately
- Temporary file cleanup after processing
- Configurable upload limits to protect local system resources

## Supported File Types

The current web UI exposes the following local file types by default through the browser picker:

- Documents: PDF, DOCX, PPTX, XLSX, EPUB, MSG, ZIP
- Web and structured text: HTML, HTM, CSV, JSON, JSONL, XML
- Plain text and Markdown: TXT, TEXT, MD, MARKDOWN
- Notebooks: IPYNB
- Images: JPG, JPEG, PNG

Audio and video formats are available only after an explicit UI opt-in:

- Audio and video: WAV, MP3, M4A, MP4

The underlying MarkItDown engine supports a broader set of formats and integrations when the relevant optional dependencies are installed. In this repository, `markitdown[all]` is included in the root requirements, so the backend engine is provisioned with broad converter support and the current UI now exposes a larger subset of those local file-based converters.

ZIP uploads are inspected before conversion. If an archive contains audio or video files, the app blocks conversion unless the transcription opt-in has been enabled.

## How It Works

```mermaid
flowchart LR
	A[Upload file in browser] --> B[Streamlit web interface]
	B --> C[Temporary local working file]
	C --> D[MarkItDown conversion engine]
	D --> E[Markdown result]
	E --> F[Preview and download]
```

## Privacy and Local Processing

The application is intended for local-first use. Files are processed on the local machine through the MarkItDown engine rather than being sent to a public conversion API, except for the opt-in conversion paths described below. Uploaded files are written to a unique temporary directory and processed without using the original file path, which avoids path-traversal and naming conflicts. Temporary working files are removed after processing completes.

Audio and video transcription are treated separately in the UI. Those formats are hidden by default and require an explicit opt-in because the underlying transcription path may send media content to a third-party speech recognition service.

## Project Structure

This repository is an extended clone of the upstream MarkItDown project. The root contains the Streamlit web UI, while the `packages/` directory retains the upstream Python packages and related extensions.

```text
markitdown-web-ui/
├── .devcontainer/
├── .github/
├── .streamlit/
│   └── config.toml
├── app.py
├── Dockerfile
├── packages/
│   ├── markitdown/
│   ├── markitdown-mcp/
│   ├── markitdown-ocr/
│   └── markitdown-sample-plugin/
├── README.md
├── requirements.txt
└── screenshot.JPG
```

For this project, this structure is more accurate than a minimal single-app layout because the repository is not just a standalone Streamlit app; it also vendors the upstream MarkItDown workspace that the UI depends on and extends.

## Requirements

- Python 3.10 or later
- A virtual environment such as `.venv`

## Installation

```bash
git clone https://github.com/k-f-m/markitdown-web-ui.git
cd markitdown-web-ui
```

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app.py
```

After startup, open `http://localhost:8501` in your browser if Streamlit does not open it automatically.

## Typical Workflow

1. Start the Streamlit application.
2. Upload a supported file through the web interface.
3. Run the conversion.
4. Review the generated Markdown.
5. Download or copy the result for downstream use.

For audio and video files, enable the transcription opt-in first and review the privacy warning before uploading.

## Known Limitations

- The current Streamlit upload whitelist is still narrower than the full MarkItDown engine capability.
- The UI focuses on local file-based conversions and does not expose URL-driven or service-backed flows such as YouTube URLs or Azure-backed conversion paths.
- Audio and video transcription are opt-in because the current backend path may rely on third-party speech recognition rather than fully local processing.
- ZIP archives that contain audio or video files are blocked unless the transcription opt-in is enabled.
- Some accepted file types may depend on optional native tools or libraries at runtime for best results, even though `markitdown[all]` is installed.

## Notes

- This repository is an independent web UI wrapper around the upstream [MarkItDown](https://github.com/microsoft/markitdown) project.
- It is not officially affiliated with or endorsed by Microsoft.
- The software is provided under the MIT License.

## License

This project is distributed under the MIT License. See the `LICENSE` file for details.