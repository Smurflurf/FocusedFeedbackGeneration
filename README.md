# Automated Focused Feedback Generation (Modernized)

> **Disclaimer:** This is a cloned, slightly rewritten, and modernized version of the original [FocusedFeedbackGeneration repository by Eric Chamoun](https://github.com/ericchamoun/FocusedFeedbackGeneration). This codebase is intended purely for educational purposes.

---

## Installation & Setup

> **Note:** Step 1 is only required for the initial setup. For any subsequent runs, you only need to activate the virtual environment (`source .venv/bin/activate`) and run the script.

### 1. Create a Virtual Environment and Install Dependencies

```bash
# 1.1: Create the virtual environment
python3 -m venv .venv

# 1.2: Activate the virtual environment
source .venv/bin/activate

# 1.3: Upgrade pip to the latest version
pip install --upgrade pip

# 1.4: Install all required python packages
pip install -r requirements.txt
```

### 1.5: Download the Reranking Model (Required)
The neural network model used for planning is too large for GitHub's file limits and must be downloaded manually. 

* **1.5.1:** Download the model file from the original authors' Google Drive: [Google Drive Link](https://drive.google.com/file/d/1wRrown4YhKN3PiUdTm689sV-w9wiCdBC/view)
* **1.5.2:** Place the downloaded `reranking_model.pt` file directly into the `plan_reranking_inference/` folder.


---

## Configuration

### 2. Add Your API Keys

1. Open `config.py` in your text editor.
2. Add your Gemini API keys to `gemini_api_keys` (follow the instructions provided inside `config.py`).
3. *(Optional)* Change the default LLM or the embedding model if needed.

---

## How to Run

### 3. Executing the Tool

To start the feedback assistant, run:
```bash
python3 run.py
```

* **Paragraph input:** The terminal will ask you for a paragraph to review. **Crucial:** Make sure to copy and paste the paragraph as a single line without any `\n` (line breaks), otherwise the terminal input stream might break.
* **Paper link:** Paste the link to the paper. This can be a local file path on your system (e.g. `documents/paper.pdf`) or an online URL (e.g., an ArXiv PDF link).
* **Wait:** The pipeline will execute, retrieve context, and generate its scientific feedback.

### 4. Running it Again
* If you want to use cached/downloaded files for faster subsequent runs, comment in the respective lines inside `run.py`.
* Always remember to activate the virtual environment before running the tool:
  ```bash
  source .venv/bin/activate
  ```
