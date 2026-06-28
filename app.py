import streamlit as st
import io
import os
import tempfile
import zipfile
from markitdown import MarkItDown

LOCAL_UPLOAD_TYPES = [
    "pdf",
    "docx",
    "pptx",
    "xlsx",
    "csv",
    "html",
    "htm",
    "txt",
    "text",
    "md",
    "markdown",
    "json",
    "jsonl",
    "xml",
    "epub",
    "msg",
    "ipynb",
    "zip",
    "jpg",
    "jpeg",
    "png",
]

# Registry of conversion paths that may send data outside the local environment.
# Each path is opt-in and disabled by default. To add a future non-local path
# (e.g., cloud OCR, Azure Document Intelligence, or LLM image captioning), append
# an entry here; the opt-in UI, upload whitelist, and ZIP inspection below all
# enforce every registered path automatically.
NON_LOCAL_CONVERSION_PATHS = [
    {
        "key": "audio_video_transcription",
        "extensions": ["wav", "mp3", "m4a", "mp4"],
        "opt_in_label": (
            "Enable audio and video transcription that may send media data to "
            "third-party speech recognition services"
        ),
        "enabled_warning": (
            "Audio and video transcription is enabled. Files such as WAV, MP3, "
            "M4A, and MP4 may be processed by third-party speech recognition "
            "services rather than staying fully local."
        ),
        "hidden_caption": (
            "Audio and video uploads are hidden until you explicitly enable "
            "third-party transcription."
        ),
    },
]


# Bound recursion when inspecting nested archives to limit zip-bomb exposure.
MAX_ZIP_INSPECTION_DEPTH = 16


def find_blocked_zip_members(
    file_bytes: bytes, blocked_extensions: set[str]
) -> list[str]:
    blocked_members: list[str] = []

    def inspect_zip_bytes(zip_bytes: bytes, prefix: str = "", depth: int = 0) -> None:
        if depth >= MAX_ZIP_INSPECTION_DEPTH:
            return

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zip_file:
            for member_name in zip_file.namelist():
                if member_name.endswith("/"):
                    continue

                member_path = f"{prefix}{member_name}"
                member_extension = os.path.splitext(member_name)[1].lower()

                if member_extension in blocked_extensions:
                    blocked_members.append(member_path)
                    continue

                if member_extension == ".zip":
                    try:
                        inspect_zip_bytes(
                            zip_file.read(member_name),
                            prefix=f"{member_path} -> ",
                            depth=depth + 1,
                        )
                    except zipfile.BadZipFile:
                        continue

    try:
        inspect_zip_bytes(file_bytes)
    except zipfile.BadZipFile:
        return []
    return blocked_members


def convert_uploaded_file(
    uploaded_file, blocked_non_local_extensions: set[str]
) -> dict:
    """Convert a single uploaded file to Markdown.

    Returns a result dict with a ``status`` of ``success``, ``blocked``, or
    ``error`` so the UI can render per-file outcomes without raising.
    """
    name = uploaded_file.name
    _, file_extension = os.path.splitext(name)
    file_extension = file_extension.lower()
    file_bytes = uploaded_file.getvalue()

    result: dict = {
        "name": name,
        "status": "error",
        "markdown": None,
        "error": None,
        "blocked_members": None,
        "size": len(file_bytes),
    }

    if file_extension == ".zip" and blocked_non_local_extensions:
        blocked_members = find_blocked_zip_members(
            file_bytes, blocked_non_local_extensions
        )
        if blocked_members:
            result["status"] = "blocked"
            result["blocked_members"] = blocked_members
            return result

    # Isolate file handling inside a unique temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use a fixed safe filename inside the unique temp dir, ignoring the
        # user-supplied filename to avoid path traversal
        secure_temp_path = os.path.join(temp_dir, f"upload{file_extension}")

        with open(secure_temp_path, "wb") as f:
            f.write(file_bytes)

        try:
            converter = MarkItDown()
            # Use local conversion specifically
            converted = converter.convert_local(secure_temp_path)
            result["status"] = "success"
            result["markdown"] = converted.text_content
        except Exception as exc:  # noqa: BLE001 - surfaced to the user per file
            result["error"] = str(exc)
        # The 'with' context manager removes the directory and its contents here

    return result


def markdown_filename(name: str) -> str:
    """Map an uploaded filename to a ``.md`` output name."""
    return os.path.splitext(os.path.basename(name))[0] + ".md"


def build_markdown_zip(results: list[dict]) -> bytes:
    """Bundle all successful Markdown outputs into a single in-memory ZIP."""
    buffer = io.BytesIO()
    used_names: set[str] = set()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in results:
            if item["status"] != "success":
                continue
            out_name = markdown_filename(item["name"])
            base, ext = os.path.splitext(out_name)
            counter = 1
            while out_name in used_names:
                out_name = f"{base}_{counter}{ext}"
                counter += 1
            used_names.add(out_name)
            zip_file.writestr(out_name, item["markdown"])
    buffer.seek(0)
    return buffer.getvalue()


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


st.set_page_config(
    page_title="MarkItDown Web UI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.5rem; max-width: 1100px; }
      h1, h2, h3 { letter-spacing: -0.01em; }
      div[data-testid="stFileUploaderDropzone"] {
          border: 1.5px dashed rgba(120, 120, 160, 0.45);
          border-radius: 14px;
          padding: 0.5rem 0.25rem;
          transition: border-color 0.15s ease, background-color 0.15s ease;
      }
      div[data-testid="stFileUploaderDropzone"]:hover {
          border-color: rgba(110, 120, 240, 0.85);
          background-color: rgba(110, 120, 240, 0.04);
      }
      div[data-testid="stMetric"] {
          background: rgba(130, 130, 160, 0.07);
          border: 1px solid rgba(130, 130, 160, 0.14);
          border-radius: 14px;
          padding: 0.85rem 1rem;
      }
      .stButton > button, .stDownloadButton > button {
          border-radius: 10px;
          font-weight: 600;
      }
      .stDownloadButton > button { width: 100%; }
      div[data-testid="stExpander"] {
          border-radius: 12px;
          border: 1px solid rgba(130, 130, 160, 0.18);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar: settings, privacy opt-ins, and reference -----------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.caption(
        "Conversions run locally by default. Paths that may send data to a "
        "third party are off until you opt in."
    )

    blocked_non_local_extensions: set[str] = set()
    allowed_upload_types = list(LOCAL_UPLOAD_TYPES)

    with st.expander("Privacy and conversion paths", expanded=True):
        for path in NON_LOCAL_CONVERSION_PATHS:
            path_extensions = [ext.lower() for ext in path["extensions"]]
            enabled = st.toggle(
                path["opt_in_label"], value=False, key=path["key"]
            )
            if enabled:
                st.warning(path["enabled_warning"], icon="⚠️")
                allowed_upload_types.extend(path_extensions)
            else:
                st.caption(path["hidden_caption"])
                blocked_non_local_extensions.update(
                    f".{ext}" for ext in path_extensions
                )

    with st.expander("Supported file types", expanded=False):
        st.markdown(
            "- **Documents:** PDF, DOCX, PPTX, XLSX, EPUB, MSG\n"
            "- **Web & data:** HTML, CSV, JSON, JSONL, XML\n"
            "- **Text:** TXT, MD, MARKDOWN\n"
            "- **Notebooks:** IPYNB\n"
            "- **Images:** JPG, PNG\n"
            "- **Archives:** ZIP (inspected before conversion)\n"
            "- **Audio/Video (opt-in):** WAV, MP3, M4A, MP4"
        )

    st.divider()
    st.caption(
        "Built on [MarkItDown](https://github.com/microsoft/markitdown). "
        "Files are processed in a temporary directory that is wiped after each run."
    )

# --- Main area ---------------------------------------------------------------
st.title("📄 MarkItDown Converter")
st.caption(
    "Convert documents, spreadsheets, notebooks, and images into clean Markdown — "
    "one file or many at once."
)

if "results" not in st.session_state:
    st.session_state["results"] = None

uploaded_files = st.file_uploader(
    "Drag and drop files here, or browse",
    type=allowed_upload_types,
    accept_multiple_files=True,
)

if uploaded_files:
    total_size = sum(len(f.getvalue()) for f in uploaded_files)
    info_col, action_col = st.columns([3, 1], vertical_alignment="center")
    with info_col:
        st.caption(
            f"**{len(uploaded_files)}** file(s) selected · {human_size(total_size)} total"
        )
    with action_col:
        convert_clicked = st.button(
            "Convert to Markdown", type="primary", use_container_width=True
        )

    if convert_clicked:
        results: list[dict] = []
        progress = st.progress(0.0, text="Starting…")
        for index, uploaded_file in enumerate(uploaded_files, start=1):
            progress.progress(
                index / len(uploaded_files),
                text=f"Converting {uploaded_file.name} ({index}/{len(uploaded_files)})",
            )
            results.append(
                convert_uploaded_file(uploaded_file, blocked_non_local_extensions)
            )
        progress.empty()
        st.session_state["results"] = results
else:
    # Clear stale results once the uploader is emptied.
    st.session_state["results"] = None

results = st.session_state.get("results")

if results:
    success = [r for r in results if r["status"] == "success"]
    blocked = [r for r in results if r["status"] == "blocked"]
    failed = [r for r in results if r["status"] == "error"]

    st.divider()
    metric_cols = st.columns(3)
    metric_cols[0].metric("Converted", len(success))
    metric_cols[1].metric("Blocked", len(blocked))
    metric_cols[2].metric("Failed", len(failed))

    if len(success) > 1:
        st.download_button(
            label=f"📦 Download all {len(success)} as ZIP",
            data=build_markdown_zip(results),
            file_name="markdown_outputs.zip",
            mime="application/zip",
            type="primary",
        )

    st.write("")

    for index, item in enumerate(results):
        if item["status"] == "success":
            icon, state = "✅", "complete"
        elif item["status"] == "blocked":
            icon, state = "⚠️", "error"
        else:
            icon, state = "❌", "error"

        with st.status(f"{icon}  {item['name']}", state=state, expanded=False):
            if item["status"] == "success":
                st.caption(f"{human_size(item['size'])} · converted locally")
                st.text_area(
                    "Markdown output",
                    item["markdown"],
                    height=300,
                    label_visibility="collapsed",
                    key=f"preview_{index}",
                )
                st.download_button(
                    label="📥 Download Markdown",
                    data=item["markdown"],
                    file_name=markdown_filename(item["name"]),
                    mime="text/markdown",
                    key=f"download_{index}",
                )
            elif item["status"] == "blocked":
                st.error(
                    "This archive contains files that need a conversion path you "
                    "have not enabled, which may send data outside your local "
                    "environment. Enable the relevant opt-in in the sidebar to "
                    "process it."
                )
                members = item["blocked_members"] or []
                st.caption("Blocked files: " + ", ".join(members[:10]))
                if len(members) > 10:
                    st.caption(f"Plus {len(members) - 10} more inside the archive.")
            else:
                st.error(f"Conversion failed: {item['error']}")
else:
    st.info(
        "Upload one or more files to get started. You can select multiple files "
        "and convert them in a single run.",
        icon="💡",
    )