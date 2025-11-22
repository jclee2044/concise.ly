import streamlit as st
import random
import base64
from pathlib import Path
import pandas as pd
from prompts import EXPLANATION_SCORING_PROMPT
from llm_client import generate_score

WORD_COUNTS = [15, 12, 10, 8, 6, 5, 4, 3, 2, 1]

# load concepts
concepts = pd.read_csv("concepts_db/concepts.csv")

# load logo
logo_path = Path(__file__).parent / "logo.png"
LOGO_B64 = ""
if logo_path.exists():
    LOGO_B64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

# load css
css_file = Path(__file__).parent / "style.css"
if css_file.exists():
    st.markdown(
        f"<style>{css_file.read_text()}</style>",
        unsafe_allow_html=True
    )

# initialize session state
if "mode" not in st.session_state:
    st.session_state.mode = "home"
if "round" not in st.session_state:
    st.session_state.round = 0

@st.dialog("Round Feedback", width="small", dismissible=False)
def feedback_popup():
    st.subheader("Score: 100/100")
    st.markdown("**Feedback:**")
    st.write(st.session_state.llm_feedback)
    st.markdown("**Improved version:**")
    st.write(st.session_state.improved_version)

    if st.button("Next Round"):
        for key in ("concept", "audience", "explanation", "llm_feedback", "improved_version", "show_feedback"):
            st.session_state.pop(key, None)
        st.session_state.explanation = ""
        st.session_state.round += 1
        st.rerun()


# ---------- HOME SCREEN ----------
if st.session_state.mode == "home":
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <img src="data:image/png;base64,{LOGO_B64}" alt="Concise.ly" style="height: 64px;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    tagline = random.choice([
        "Avoid the awkwardness.",
        "Communicate better.",
        "Say it right.",
        "No more tip-of-the-tongue.",
        "Blow them away with how well you speak.",
        "Make your words count."
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
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <img src="data:image/png;base64,{LOGO_B64}" alt="Concise.ly" style="height: 64px;"/>
            <p><b>Difficulty:</b> {st.session_state.difficulty}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("<br/>", unsafe_allow_html=True)

    # parameters
    difficulty = st.session_state.difficulty
    concept_list = concepts[difficulty].tolist()
    
    if "concept" not in st.session_state:
        st.session_state.concept = random.choice(concept_list)
    
    if "audience" not in st.session_state:
        st.session_state.audience = random.choice(
            ["5-year-old", "high schooler", "college professor", "beginner English learner", "friend", "love interest", "supervisor", "scientist", "investor", "grandma", "poet", "business colleague"]
        )
    
    concept = st.session_state.concept
    audience = st.session_state.audience

    st.info("Explain **" + concept + "** to " + "a **" + audience + "**.")
    # st.info("**Concept:** " + concept + "  \n"
    #     + "**Audience:** " + audience)

    # explanation
    explanation = st.text_area("Your explanation", key="explanation")

    # word count info
    word_limit = WORD_COUNTS[st.session_state.round]
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

    col1, col2, col3 = st.columns([3,4,2])
    with col3:
        if st.button("Submit") and explanation.strip():
            # Generate LLM feedback
            prompt = EXPLANATION_SCORING_PROMPT.format(
                concept=concept,
                audience=audience,
                explanation=explanation,
                word_count=current_word_count,
            )
            try:
                result = generate_score(prompt)
                
                # Parse the result: feedback (two sentences) followed by newline and improved version
                # Try splitting by double newline first
                if "\n\n" in result:
                    parts = result.split("\n\n", 1)
                    feedback = parts[0].strip()
                    improved_version = parts[1].strip()
                else:
                    # Fallback: split by single newline and take first part as feedback, rest as improved
                    lines = result.split("\n")
                    # Find the first empty line as separator
                    separator_idx = -1
                    for i, line in enumerate(lines):
                        if not line.strip():
                            separator_idx = i
                            break
                    
                    if separator_idx > 0:
                        feedback = "\n".join(lines[:separator_idx]).strip()
                        improved_version = "\n".join(lines[separator_idx+1:]).strip()
                    else:
                        # Last resort: take first two sentences as feedback, rest as improved
                        sentences = result.split(". ")
                        if len(sentences) >= 2:
                            feedback = ". ".join(sentences[:2]) + ("." if not sentences[1].endswith(".") else "")
                            improved_version = ". ".join(sentences[2:])
                        else:
                            feedback = result
                            improved_version = result
                
                # Store in session state
                st.session_state.llm_feedback = feedback
                st.session_state.improved_version = improved_version
                st.session_state.show_feedback = True
            except Exception as e:
                st.error(f"Error generating feedback: {str(e)}")
            st.rerun()
    
    # Display feedback as popup
    if st.session_state.get("show_feedback", False):
        feedback_popup()

