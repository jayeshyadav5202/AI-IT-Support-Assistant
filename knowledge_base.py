"""
knowledge_base.py
-----------------
Loads the IT support CSV and finds the most relevant entry for a user's
problem using TF-IDF + cosine similarity (scikit-learn).
"""

import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CSV_FILE = Path(__file__).parent / "IT_Support_Knowledge_Base.csv"

# Below this similarity score we say "no relevant entry found".
# Raise it for stricter matching, lower it for more lenient matching.
MIN_SCORE = 0.12

# Small synonym list so everyday wording matches the knowledge base wording.
# If the user types the word on the left, we also add the words on the right.
SYNONYMS = {
    "wifi": "wi-fi wireless internet",
    "wi-fi": "wi-fi wireless internet",
    "login": "sign in",
    "log in": "sign in",
    "logon": "sign in",
    "locked": "account locked sign in",
    "bsod": "blue screen restart",
    "crash": "crashing restart not responding",
    "crashes": "crashing restart not responding",
    "freezing": "not responding",
    "frozen": "not responding",
    "hang": "not responding",
    "hangs": "not responding",
    "slow": "running slowly",
    "lag": "running slowly",
    "laggy": "running slowly",
    "sluggish": "running slowly",
    "ethernet": "wired network cable",
    "lan": "wired network cable",
    "otp": "mfa code",
    "2fa": "mfa code",
    "mapped drive": "network drive shared folder",
    "permission": "access denied",
    "permissions": "access denied",
    "email": "outlook email",
    "mail": "outlook email",
    "internal server error": "http 500 api",
    "500": "http 500 api",
}


def expand_query(text: str) -> str:
    """Add synonym words to the user's text (simple, beginner-friendly)."""
    text = text.lower()
    extra = []
    for word, replacement in SYNONYMS.items():
        # \b makes sure we match whole words only
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            extra.append(replacement)
    return text + " " + " ".join(extra)


def split_items(text: str) -> list:
    """Turn 'a; b; c' from the CSV into a clean list ['A', 'B', 'C']."""
    items = []
    for part in str(text).split(";"):
        part = part.strip().rstrip(".")
        if part:
            items.append(part[0].upper() + part[1:])
    return items


class KnowledgeBase:
    def __init__(self, csv_path=CSV_FILE):
        # utf-8-sig removes the hidden BOM character at the start of the file
        self.df = pd.read_csv(csv_path, encoding="utf-8-sig").fillna("")

        # Text used for searching. The issue title is repeated so that it
        # counts more than the other columns.
        self.df["search_text"] = (
            (self.df["issue"] + " ") * 3
            + self.df["category"] + " "
            + (self.df["symptoms"] + " ") * 2
            + self.df["possible_causes"]
        )

        self.vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )
        self.matrix = self.vectorizer.fit_transform(self.df["search_text"])

    def search(self, query: str):
        """
        Return (entry, score).
        entry is None when nothing relevant was found.
        """
        query = query.strip()
        if not query:
            return None, 0.0

        query_vector = self.vectorizer.transform([expand_query(query)])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        best = int(scores.argmax())
        best_score = float(scores[best])

        if best_score < MIN_SCORE:
            return None, best_score

        row = self.df.iloc[best]
        entry = {
            "kb_id": row["kb_id"],
            "issue": row["issue"],
            "category": row["category"],
            "symptoms": row["symptoms"],
            "possible_causes": split_items(row["possible_causes"]),
            "diagnostic_checks": split_items(row["diagnostic_checks"]),
            "resolution_steps": split_items(row["resolution_steps"]),
            "escalation_team": row["escalation_team"],
            "escalation_condition": row["escalation_condition"],
            "severity": row["severity"],
            "source": CSV_FILE.name,
        }
        return entry, best_score

    def topics(self) -> list:
        """List of issue titles in the knowledge base."""
        return self.df["issue"].tolist()


if __name__ == "__main__":
    # Quick test:  python knowledge_base.py
    kb = KnowledgeBase()
    for q in ["my wifi has no internet", "outlook keeps crashing", "pizza recipe"]:
        result, score = kb.search(q)
        print(q, "->", result["kb_id"] if result else "NOT FOUND", round(score, 2))
