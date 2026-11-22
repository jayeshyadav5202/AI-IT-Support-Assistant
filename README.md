# AI IT Support Assistant

A simple chatbot for IT support engineers. Describe a problem in plain English and
get troubleshooting steps taken **only** from `IT_Support_Knowledge_Base.csv`.

- Search: TF-IDF + cosine similarity (scikit-learn)
- Interface: Streamlit
- Optional AI wording: Claude API (works fine without it, in demo mode)

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit chat interface |
| `knowledge_base.py` | Loads the CSV and finds the best matching issue |
| `ai_engine.py` | Builds answers (Claude if API key exists, template if not) |
| `IT_Support_Knowledge_Base.csv` | The knowledge base |
| `requirements.txt` | Python libraries |
| `.env.example` | Example API key settings |

## Install and run on Windows (VS Code)

Open the project folder in VS Code, then open a terminal (**Terminal > New Terminal**,
choose **Command Prompt** or **PowerShell**) and run:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks `activate`, run this once and try again:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

The app opens at http://localhost:8501.

To stop it, press `Ctrl + C` in the terminal.

## Optional: use Claude

1. Copy `.env.example` to `.env`:
   ```
   copy .env.example .env
   ```
2. Open `.env` and paste your key after `ANTHROPIC_API_KEY=`
3. Restart the app. The sidebar will show **Claude AI mode is ON**.

Claude only receives the retrieved knowledge-base entry and is told not to add anything
else. If the API fails, the app falls back to the template answer automatically.

## How it works

1. The engineer types a problem.
2. `knowledge_base.py` compares it with every KB entry (TF-IDF + cosine similarity).
3. If the best score is below `MIN_SCORE` (0.12), no answer is invented. The bot asks for more details.
4. Otherwise `ai_engine.py` formats the matching entry as the answer.

## Demo ideas (5 minutes)

- "My Wi-Fi is connected but there is no internet"
- "Outlook keeps crashing"
- "Payment API is returning HTTP 500 error"
- "My monitor is flickering" (not in the KB, so the bot asks for more information)
- Click **Clear chat** in the sidebar to reset.
