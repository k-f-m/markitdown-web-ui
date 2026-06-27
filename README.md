# Secure MarkItDown Web UI

Welcome! This is an independent, privacy-focused graphical web interface for Microsoft's `MarkItDown` engine. It provides an intuitive, local drag-and-drop workspace to convert your documents (such as PDF, DOCX, PPTX, XLSX, images, and audio) into clean Markdown optimized for LLMs, writing assistants, and text-analysis workflows.

---

## ✨ Privacy-Focused Design

This application is built with local-first, privacy-oriented practices in mind to help keep you in control of your data:

* **🛡️ Local-First & Offline Processing:** The application is configured to call `convert_local()`. This design ensures that processing occurs on your local machine rather than routing your documents through external public web APIs.
* **💻 Sandboxed File Handling:** To reduce path risks, the original filenames of your uploaded files are bypassed and replaced with randomized temporary IDs. This helps keep your local directory organized and minimizes the risk of file conflicts.
* **🧹 Automated Temporary Cleanup:** Once your file is processed, the system-level wrapper is designed to automatically remove the temporary working files from your storage drive.
* **⚙️ Configurable Upload Limits:** Helps protect your system's memory and CPU resources by restricting the default accepted file size (set to 10MB by default).

---

## 📂 Project Structure

This project is lightweight and designed to be easy to explore:

```text
my-markitdown-ui/
├── .streamlit/
│   └── config.toml      # Configures safe local file uploading parameters
├── .gitignore           # Keeps your repository clean from temporary test files
├── LICENSE              # Standard open-source MIT license
├── README.md            # You are here! Getting started guide
├── app.py               # The clean, security-hardened Streamlit app
└── requirements.txt     # App package dependencies
```

---

## 🛠️ Prerequisites & Setup

### 1. Requirements

* **Python 3.10** or higher.
* A standard virtual environment (`.venv`) to keep your system clean.

### 2. Installation & Setup

Clone the repository and jump in:

```bash
git clone [https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git)
cd YOUR-REPO-NAME
```

Create and activate your virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the App

Ready to convert? Fire up the interface:

```bash
streamlit run app.py
```

A browser window will automatically launch at `http://localhost:8501` showing your conversion workspace. Drag in a file, click convert, and download your Markdown output.

---

## ⚖️ License, Disclaimers & Terms

* **License:** This project is open-source software distributed under the terms of the permissive **MIT License**.
* **Warranty & Liability Disclaimer:** This software is provided "as-is" without warranty of any kind, express or implied. By using this software, you agree that the creators, authors, and contributors are not liable for any issues, data loss, performance degradation, security incidents, or system anomalies resulting from its execution or deployment. Please see the accompanying `LICENSE` file for the standard open-source legal terms.
* **Trademarks:** This is an independent, community-contributed wrapper tool. It is not officially associated with, sponsored by, or endorsed by Microsoft Corporation. All trademarks belong to their respective owners.