"""
AI Resume Analyzer — Streamlit UI
==================================
Upload a CV (PDF or plain text) and paste a job description to get an
instant semantic match score, skill gap analysis, and improvement tips.
"""

import io
import streamlit as st
from resume_analyzer.container import get_analysis_service


analysis_service = get_analysis_service()

# ── Page configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────

st.title("📄 AI Resume Analyzer & Job Matcher")
st.markdown(
    "Upload your CV and paste a job description. The system will compute a "
    "**semantic similarity score**, identify matched and missing skills, and "
    "give you actionable improvement tips."
)
st.divider()

# ── Input columns ────────────────────────────────────────────────────────────

col_cv, col_jd = st.columns(2, gap="large")

with col_cv:
    st.subheader("Your CV")
    uploaded_file = st.file_uploader(
        "Upload PDF or paste text below",
        type=["pdf", "txt"],
        help="Accepted formats: PDF (.pdf) or plain text (.txt)",
    )
    cv_text_input = st.text_area(
        "Or paste CV text here",
        height=280,
        placeholder="Paste your CV content here if you don't want to upload a file…",
    )

with col_jd:
    st.subheader("Job Description")
    jd_text_input = st.text_area(
        "Paste the job description",
        height=380,
        placeholder="Paste the full job description here…",
    )

st.divider()

# ── Analyse button ───────────────────────────────────────────────────────────

analyse_clicked = st.button("🔍 Analyse Match", type="primary", use_container_width=True)

if analyse_clicked:
    # Resolve CV source — prefer uploaded file, fall back to pasted text
    cv_source = None
    file_bytes = None

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        if uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
            cv_source = io.BytesIO(file_bytes)
        else:
            cv_source = file_bytes.decode("utf-8", errors="replace")
    
    if cv_source is None and cv_text_input.strip():
        cv_source = cv_text_input.strip()

    # Validate inputs
    if cv_source is None:
        st.error("Please upload a CV file or paste your CV text.")
        st.stop()

    if not jd_text_input.strip():
        st.error("Please paste a job description.")
        st.stop()

    # ── Pre-analysis skill preview (helps debug & shows transparency) ─────────
    try:
        if isinstance(cv_source, io.BytesIO):
            cv_source.seek(0)
            preview_text = analysis_service.extract_text(io.BytesIO(cv_source.read()))
            cv_source.seek(0)
        else:
            preview_text = analysis_service.extract_text(cv_source)

        preview_cv_skills = analysis_service.extract_skills(preview_text)
        preview_jd_skills = analysis_service.extract_skills(jd_text_input.strip())

        with st.expander(
            f"🔎 Skills detected before analysis — CV: {len(preview_cv_skills)}  |  JD: {len(preview_jd_skills)}"
        ):
            dc, dj = st.columns(2)
            with dc:
                st.markdown("**Skills found in your CV:**")
                st.write(", ".join(sorted(preview_cv_skills)) if preview_cv_skills else "None detected")
            with dj:
                st.markdown("**Skills found in the Job Description:**")
                st.write(", ".join(sorted(preview_jd_skills)) if preview_jd_skills else "None detected")
    except Exception:
        pass  # Non-critical; don't block the analysis

    # Reset BytesIO position before passing to analyze()
    if isinstance(cv_source, io.BytesIO):
        cv_source.seek(0)

    # Run analysis
    with st.spinner("Analysing your CV… (first run may take ~30 s to load the AI model)"):
        try:
            report = analysis_service.analyze(cv_source, jd_text_input.strip())
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.stop()

    st.divider()

    # ── Results ──────────────────────────────────────────────────────────────

    st.header("📊 Analysis Results")

    # Top-level metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Match Score", f"{report['match_score']}%")
    m2.metric("Semantic Similarity", f"{report['similarity_score']}%")
    m3.metric("Skill Overlap", f"{report['skill_overlap']}%")
    m4.metric("Fit Rating", report["strength"])

    st.markdown(f"**Match Score: {report['match_score']}%**")
    st.progress(report["match_score"] / 100)
    st.caption(f"Similarity method: {report.get('method', 'TF-IDF Cosine Similarity')}")

    st.divider()

    # Skill breakdown
    col_match, col_miss, col_extra = st.columns(3, gap="medium")

    with col_match:
        st.subheader(f"✅ Matched Skills ({len(report['matched_skills'])})")
        if report["matched_skills"]:
            for skill in report["matched_skills"]:
                st.markdown(f"- {skill}")
        else:
            st.info("No matching skills detected.")

    with col_miss:
        st.subheader(f"❌ Missing Skills ({len(report['missing_skills'])})")
        if report["missing_skills"]:
            for skill in report["missing_skills"]:
                st.markdown(f"- {skill}")
        else:
            st.success("You have all required skills!")

    with col_extra:
        st.subheader(f"➕ Extra CV Skills ({len(report['extra_skills'])})")
        if report["extra_skills"]:
            for skill in report["extra_skills"][:20]:
                st.markdown(f"- {skill}")
            if len(report["extra_skills"]) > 20:
                st.caption(f"…and {len(report['extra_skills']) - 20} more")
        else:
            st.info("No additional skills beyond the JD requirements.")

    st.divider()

    # Suggestions
    st.subheader("💡 Suggestions for Improvement")
    for i, suggestion in enumerate(report["suggestions"], start=1):
        st.markdown(f"**{i}.** {suggestion}")

    st.divider()

    # Expandable raw text & methodology
    with st.expander("📝 Extracted CV Text"):
        st.text(report["cv_text"][:5000] + ("…" if len(report["cv_text"]) > 5000 else ""))

    with st.expander("📋 How the Score is Calculated"):
        st.markdown(
            """
The **Overall Match Score** is a weighted blend of two signals:

| Signal | Weight | Description |
|---|---|---|
| Semantic Similarity | 60 % | Cosine similarity of sentence embeddings (`all-MiniLM-L6-v2`) |
| Skill Overlap | 40 % | `matched skills ÷ total JD skills` |

**Semantic Similarity** captures meaning beyond keyword matching — a CV that
uses synonyms or describes experience in different words will still score well
if the underlying concepts match.

**Skill Overlap** rewards explicit coverage of the skills listed in the JD.
            """
        )

# ── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Built with Python · PyPDF2 · NLTK · SentenceTransformers · scikit-learn · Streamlit"
)
