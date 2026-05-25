from __future__ import annotations

import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


def ensure_nltk_resources() -> None:
    resources = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


class TextPreprocessingService:
    """Normalize resume and job-description text for similarity scoring."""

    def __init__(self) -> None:
        ensure_nltk_resources()
        self._stop_words = set(stopwords.words("english"))
        self._lemmatizer = WordNetLemmatizer()

    def preprocess(self, text: str) -> list[str]:
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\d+", "", text)

        tokens = word_tokenize(text)
        tokens = [token for token in tokens if token not in self._stop_words and len(token) > 1]
        return [self._lemmatizer.lemmatize(token) for token in tokens]
