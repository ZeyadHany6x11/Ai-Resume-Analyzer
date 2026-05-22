"""
AI Resume Analyzer and Job Matching System
==========================================
Core analysis module with modular functions for:
- Text extraction from PDF/text
- NLP preprocessing (lowercase, punctuation removal, tokenisation, stopwords, lemmatisation)
- Skill extraction via keyword matching + regex
- Semantic similarity (SentenceTransformers with TF-IDF fallback)
- Report generation
"""

import re
import string
import io
import warnings
from typing import Union

warnings.filterwarnings("ignore")

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import PyPDF2

from skills_list import SKILLS_DATABASE


# ── NLTK resource bootstrap ──────────────────────────────────────────────────

def _ensure_nltk_resources() -> None:
    """Download required NLTK data if not already present."""
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


_ensure_nltk_resources()

# ── Sentence-Transformer model (lazy-loaded with TF-IDF fallback) ────────────

_MODEL = None
_USE_SBERT = False


def _try_load_sbert():
    """Attempt to load the SentenceTransformer model; silently fail if unavailable."""
    global _MODEL, _USE_SBERT
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        _USE_SBERT = True
    except Exception:
        _USE_SBERT = False
        _MODEL = None


# ── 1. Text Extraction ───────────────────────────────────────────────────────

def extract_text(source: Union[bytes, str, io.BytesIO]) -> str:
    """
    Extract plain text from a PDF (bytes / BytesIO) or a raw text string.

    Parameters
    ----------
    source : bytes | str | BytesIO
        PDF binary content, a BytesIO wrapping PDF bytes, or a plain-text string.

    Returns
    -------
    str
        Extracted text.
    """
    if isinstance(source, str):
        return source

    if isinstance(source, (bytes, io.BytesIO)):
        stream = io.BytesIO(source) if isinstance(source, bytes) else source
        try:
            reader = PyPDF2.PdfReader(stream)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except Exception as exc:
            raise ValueError(f"Failed to read PDF: {exc}") from exc

    raise TypeError(f"Unsupported source type: {type(source)}")


# ── 2. Text Preprocessing ────────────────────────────────────────────────────

def preprocess_text(text: str) -> list:
    """
    Clean and normalise text through an NLP pipeline:
    lowercase → remove punctuation → tokenise → remove stopwords → lemmatise.

    Parameters
    ----------
    text : str
        Raw text to process.

    Returns
    -------
    list[str]
        List of clean lemmatised tokens.
    """
    # Lowercase
    text = text.lower()

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Remove extra whitespace / digits
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\d+", "", text)

    # Tokenise
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    tokens = [t for t in tokens if t not in stop_words and len(t) > 1]

    # Lemmatise
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    return tokens


# ── 3. Skill Extraction ──────────────────────────────────────────────────────

def extract_skills(text: str, extra_skills=None) -> set:
    """
    Identify skills from text using keyword matching against the predefined
    SKILLS_DATABASE.  Supports multi-word skill phrases via substring matching
    and regex-based pattern extraction.

    Parameters
    ----------
    text : str
        Raw (un-preprocessed) text to scan.
    extra_skills : list[str] | None
        Additional custom skill keywords to match.

    Returns
    -------
    set[str]
        Normalised set of detected skill names.
    """
    text_lower = text.lower()
    skill_pool = SKILLS_DATABASE[:]
    if extra_skills:
        skill_pool += [s.lower() for s in extra_skills]

    found: set = set()

    for skill in skill_pool:
        skill_lower = skill.lower()
        if " " not in skill_lower:
            # Whole-word match for single-word skills
            pattern = r"\b" + re.escape(skill_lower) + r"\b"
            if re.search(pattern, text_lower):
                found.add(skill_lower)
        else:
            # Substring match for multi-word skills
            if skill_lower in text_lower:
                found.add(skill_lower)

    # Regex bonus: catch "X years of Python" patterns
    pattern_years = re.compile(
        r"\d+\+?\s+years?\s+(?:of\s+)?([a-z][a-z0-9+#.\-/]+)", re.IGNORECASE
    )
    for match in pattern_years.finditer(text_lower):
        candidate = match.group(1).strip().lower()
        if candidate in SKILLS_DATABASE:
            found.add(candidate)

    return found


# ── 4. Semantic Similarity ───────────────────────────────────────────────────

def compute_similarity(cv_text: str, jd_text: str) -> float:
    """
    Compute semantic similarity between the CV and job description.

    Primary method: SentenceTransformers (all-MiniLM-L6-v2) + cosine similarity.
    Fallback method: TF-IDF vectorisation + cosine similarity (if SBERT unavailable).

    Parameters
    ----------
    cv_text : str
        Preprocessed CV tokens joined as a string.
    jd_text : str
        Preprocessed job description tokens joined as a string.

    Returns
    -------
    float
        Cosine similarity in [0, 1].
    """
    global _USE_SBERT, _MODEL

    # Try to load SBERT on first call
    if _MODEL is None and not _USE_SBERT:
        _try_load_sbert()

    if _USE_SBERT and _MODEL is not None:
        embeddings = _MODEL.encode([cv_text, jd_text])
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(score)

    # TF-IDF fallback
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([cv_text, jd_text])
    score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return float(score)


def similarity_method() -> str:
    """Return which similarity method was used."""
    return "SentenceTransformers (all-MiniLM-L6-v2)" if _USE_SBERT else "TF-IDF Cosine Similarity"


# ── 5. Report Generation ─────────────────────────────────────────────────────

def generate_report(
    similarity_score: float,
    cv_skills: set,
    jd_skills: set,
    cv_tokens: list,
) -> dict:
    """
    Compile a structured analysis report from the intermediate results.

    Parameters
    ----------
    similarity_score : float
        Cosine similarity between CV and job description embeddings.
    cv_skills : set[str]
        Skills found in the CV.
    jd_skills : set[str]
        Skills required by the job description.
    cv_tokens : list[str]
        Preprocessed tokens from the CV (used for experience hints).

    Returns
    -------
    dict
        Report with:
        - match_score       : int  (percentage 0-100)
        - matched_skills    : list[str]
        - missing_skills    : list[str]
        - extra_skills      : list[str]
        - suggestions       : list[str]
        - strength          : str
        - similarity_score  : float
        - skill_overlap     : float
    """
    matched_skills = sorted(cv_skills & jd_skills)
    missing_skills = sorted(jd_skills - cv_skills)
    extra_skills = sorted(cv_skills - jd_skills)

    # Blend: semantic similarity (60%) + skill overlap (40%)
    skill_ratio = len(matched_skills) / len(jd_skills) if jd_skills else 0.0
    blend = 0.6 * similarity_score + 0.4 * skill_ratio
    match_score = min(100, round(blend * 100))

    if match_score >= 80:
        strength = "Excellent"
    elif match_score >= 60:
        strength = "Good"
    elif match_score >= 40:
        strength = "Fair"
    else:
        strength = "Needs Work"

    suggestions: list = []

    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(
            f"Acquire or highlight these key skills: **{', '.join(top_missing)}**."
        )
        suggestions.append(
            "Add relevant personal or open-source projects that showcase the missing skills."
        )
        suggestions.append(
            "Consider online courses (Coursera, Udemy, edX, freeCodeCamp) or certifications for skill gaps."
        )

    if match_score < 60:
        suggestions.append(
            "Tailor your CV summary/objective to mirror the exact language and keywords in the job description."
        )

    if not any(kw in cv_tokens for kw in ["project", "projects", "built", "developed", "created", "implemented"]):
        suggestions.append(
            "Add a dedicated **Projects** section with brief descriptions and technologies used."
        )

    if not any(kw in cv_tokens for kw in ["certificate", "certification", "certified", "credential"]):
        suggestions.append(
            "Listing relevant certifications can significantly strengthen your application."
        )

    if len(extra_skills) > 10:
        suggestions.append(
            "You have many skills — make sure the most job-relevant ones are prominently placed near the top of your CV."
        )

    if not suggestions:
        suggestions.append(
            "Great fit! Ensure your CV is concise, well-formatted, ATS-friendly, and free of typos."
        )

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "suggestions": suggestions,
        "strength": strength,
        "similarity_score": round(similarity_score * 100, 1),
        "skill_overlap": round(skill_ratio * 100, 1),
    }


# ── Public pipeline ──────────────────────────────────────────────────────────

def analyze(
    cv_source: Union[bytes, str, io.BytesIO],
    jd_text: str,
) -> dict:
    """
    Full pipeline:
      extract_text → preprocess_text → extract_skills →
      compute_similarity → generate_report.

    Parameters
    ----------
    cv_source : bytes | str | BytesIO
        CV as PDF bytes, BytesIO, or plain text.
    jd_text : str
        Job description as plain text.

    Returns
    -------
    dict
        Complete report dict including 'cv_text', 'jd_text', and 'method'.
    """
    # Step 1 — Extract text
    cv_text = extract_text(cv_source)

    # Step 2 — Preprocess
    cv_tokens = preprocess_text(cv_text)
    jd_tokens = preprocess_text(jd_text)

    # Step 3 — Extract skills
    cv_skills = extract_skills(cv_text)
    jd_skills = extract_skills(jd_text)

    # Step 4 — Compute similarity
    joined_cv = " ".join(cv_tokens)
    joined_jd = " ".join(jd_tokens)
    sim_score = compute_similarity(joined_cv, joined_jd)

    # Step 5 — Generate report
    report = generate_report(sim_score, cv_skills, jd_skills, cv_tokens)
    report["cv_text"] = cv_text
    report["jd_text"] = jd_text
    report["method"] = similarity_method()
    return report
