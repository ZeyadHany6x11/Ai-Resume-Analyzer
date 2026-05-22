# AI Resume Analyzer & Job Matcher

Analyse a CV against a job description using NLP and semantic similarity.
Get a match score, skill gap report, and improvement suggestions.

## What changed in this version

- `app.py` — added a skill preview panel (shows skills detected in CV and JD before the full analysis) and fixed a PDF byte-stream bug that caused very low match scores.
- PDFs now extract reliably with PyPDF2.

---

## Local Setup

### Prerequisites
- Python 3.10 or newer

### 1. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

For a lighter install (CPU-only PyTorch, smaller download):
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## Files

```
resume-analyzer/
├── app.py                  # Streamlit UI
├── resume_analyzer.py      # Core analysis functions
├── skills_list.py          # 200+ skills database
├── requirements.txt        # Python dependencies
├── README.md
└── .streamlit/
    └── config.toml         # Streamlit server config (port 8501)
```

---

## Core Functions

| Function | Description |
|---|---|
| `extract_text(source)` | Read text from PDF bytes or plain string |
| `preprocess_text(text)` | Lowercase, remove punctuation, tokenise, remove stopwords, lemmatise |
| `extract_skills(text)` | Match against 200+ skills using keyword + regex |
| `compute_similarity(cv, jd)` | SentenceTransformers embeddings + cosine similarity (TF-IDF fallback) |
| `generate_report(...)` | Blended match score, skill breakdown, improvement tips |
| `analyze(cv_source, jd_text)` | Full end-to-end pipeline |

## Match Score Formula

```
Match Score = (0.6 x Semantic Similarity) + (0.4 x Skill Overlap Ratio)
```

---

## Sample Job Description for Testing

```
We are looking for a Senior Python Developer / Machine Learning Engineer.
Requirements:
- 5+ years of Python development experience
- Strong experience with Django or FastAPI for building REST APIs
- Machine learning experience using PyTorch, TensorFlow, or scikit-learn
- NLP or computer vision project experience is a strong plus
- Proficiency with PostgreSQL and Redis
- Experience with Docker, Kubernetes, and CI/CD pipelines
- Cloud experience on AWS or GCP (S3, EC2, Lambda, SageMaker)
- Familiarity with Apache Kafka or message queue systems
- Experience with Agile/Scrum workflows
- Strong knowledge of system design and microservices architecture
- Git-based collaboration and code review practices
```

Expected results with the two sample CVs:
- **Sarah Chen (Senior)** — ~80-90% match, 0 missing skills
- **Michael Torres (Junior)** — ~30-45% match, 15-19 missing skills
