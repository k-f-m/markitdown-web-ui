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

st.set_page_config(page_title="MarkItDown Web UI", layout="wide")
st.title("📄 MarkItDown Converter")
st.write(
    "Local conversions are enabled by default. Conversion paths that may send "
    "data outside your local environment require an explicit opt-in."
)

allowed_upload_types = list(LOCAL_UPLOAD_TYPES)
blocked_non_local_extensions: set[str] = set()

for path in NON_LOCAL_CONVERSION_PATHS:
    path_extensions = [extension.lower() for extension in path["extensions"]]
    enabled = st.checkbox(path["opt_in_label"], value=False, key=path["key"])

    if enabled:
        st.warning(path["enabled_warning"], icon="⚠️")
        allowed_upload_types.extend(path_extensions)
    else:
        st.caption(path["hidden_caption"])
        blocked_non_local_extensions.update(
            f".{extension}" for extension in path_extensions
        )

uploaded_file = st.file_uploader(
    "Choose a file", 
    type=allowed_upload_types,
)

if uploaded_file:
    if st.button("Convert to Markdown", type="primary"):
        with st.spinner("Converting..."):
            # Take only the file extension; ignore any user-supplied path component
            _, file_extension = os.path.splitext(uploaded_file.name)
            file_extension = file_extension.lower()
            file_bytes = uploaded_file.getvalue()

            if file_extension == ".zip" and blocked_non_local_extensions:
                blocked_members = find_blocked_zip_members(
                    file_bytes, blocked_non_local_extensions
                )
                if blocked_members:
                    st.error(
                        "This ZIP contains files that require a conversion path you "
                        "have not enabled, which may send data outside your local "
                        "environment. Enable the relevant opt-in above to process "
                        "this archive."
                    )
                    st.caption("Blocked files: " + ", ".join(blocked_members[:10]))
                    if len(blocked_members) > 10:
                        st.caption(
                            f"Plus {len(blocked_members) - 10} more blocked file(s) inside the archive."
                        )
                    st.stop()
            
            # Isolate file handling inside a unique temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Use a fixed safe filename inside the unique temp dir, ignoring the
                # user-supplied filename to avoid path traversal
                secure_temp_path = os.path.join(temp_dir, f"upload{file_extension}")

                with open(secure_temp_path, "wb") as f:
                    f.write(file_bytes)

                try:
                    md = MarkItDown()
                    # Use local conversion specifically
                    result = md.convert_local(secure_temp_path)

                    st.success("Done!")
                    st.subheader("Preview Output:")
                    st.text_area(
                        "Markdown output",
                        result.text_content,
                        height=350,
                        label_visibility="collapsed",
                    )

                    # Safe download generation
                    output_name = os.path.splitext(uploaded_file.name)[0] + ".md"
                    st.download_button(
                        label="📥 Download Markdown File",
                        data=result.text_content,
                        file_name=output_name,
                        mime="text/markdown"
                    )
                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")
                # The 'with' context manager automatically removes the directory and its contents here