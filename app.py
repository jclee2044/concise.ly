import streamlit as st
import random
from pathlib import Path
import pandas as pd
from prompts import EXPLANATION_SCORING_PROMPT
from llm_client import generate_score

# setup
concepts = pd.read_csv("concepts_db/concepts.csv")

css_file = Path(__file__).parent / "style.css"
if css_file.exists():
    st.markdown(
        f"<style>{css_file.read_text()}</style>",
        unsafe_allow_html=True
    )

# initialize session state
if "mode" not in st.session_state:
    st.session_state.mode = "home"

# ---------- HOME SCREEN ----------
if st.session_state.mode == "home":
    st.write("<h1 class='pop'>Concise.ly️</h1>", unsafe_allow_html=True)
    
    tagline = random.choice([
        "Avoid the awkwardness. Communicate better.",
        "Say it right. No more tip-of-the-tongue.",
        "Blow them away with how well you speak.",
    ])
    st.write("<h4>" + tagline + "</h4>", unsafe_allow_html=True)

    st.write("""
**Instructions:** You will be given a concept, an audience, and a word limit. Within these parameters, you must explain or define the concept to match the context. 
             
We will evaluate your response, give you points, and suggestions if you wish.
""")
    
    difficulty = st.selectbox("Choose difficulty", ["easy", "medium", "hard"])
    st.session_state.difficulty = difficulty
    
    col1, col2, col3 = st.columns([3,3,2])
    with col3:
        if st.button("Start game"):
            st.session_state.mode = "gameplay"
            st.rerun()


# ---------- GAMEPLAY SCREEN ----------
elif st.session_state.mode == "gameplay":
    # header
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1 style="margin: 0" class="pop">Concise.ly️</h1>
            <p><b>Time remaining:</b> 00:39</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # parameters
    difficulty = st.session_state.difficulty
    concept_list = concepts[difficulty].tolist()
    concept = random.choice(concept_list)
    audience = random.choice(["8-year-old", "high schooler", "college student", "foreigner", "business colleague"])
    word_limit = 15 # 15 -> 13 -> 11 -> 10 -> 9 -> 8 -> 7 -> 6 -> 5 -> 4 -> 3 -> 2
    st.info("**Concept:** " + concept + "  \n"
        + "**Audience:** " + audience)

    # explanation
    explanation = st.text_area("Your explanation")

    # word count info
    current_word_count = len(explanation.split())
    words_left = word_limit - current_word_count
    st.markdown(
        f"""
        <div style="text-align: right; line-height: 1.1;">
            <p style="margin: 0; opacity: 0.7;">
                Current word count: {current_word_count}
            </p>
            <p style="margin: 0; font-weight: 700;">
                Words left: {words_left}
            </p>
            <br/>
        </div>
        """,
        unsafe_allow_html=True,
    )  

    # submit button
    if st.button("Submit") and explanation.strip():
        prompt = EXPLANATION_SCORING_PROMPT.format(
            concept=concept,
            audience=audience,
            explanation=explanation,
            word_count=current_word_count,
        )
        result = generate_score(prompt)
        print(prompt)
        print(result)

        st.subheader(f"Score: {result['score']}/100")
        st.markdown("**Strengths:**")
        for s in result["strengths"]:
            st.write(f"- {s}")
        st.markdown("**Weaknesses:**")
        for w in result["weaknesses"]:
            st.write(f"- {w}")
        st.markdown("**Improved version:**")
        st.write(result["improved_version"])
