import streamlit as st
import random
import base64
from pathlib import Path
import pandas as pd
import time
import json
from datetime import datetime
from prompts import EXPLANATION_SCORING_PROMPT
from llm_client import generate_score
from scoring import compute_content_score, time_bonus, compute_final_score

# WORD_COUNTS = [20, 17, 14, 12, 10, 9, 8, 7, 6, 6, 5, 5, 4, 4, 4, 3]
# WORD_COUNTS = [18, 15, 12, 10, 8, 7, 6, 5, 5, 4, 4, 4, 3, 3, 3] # 15 rounds
WORD_COUNTS = [18, 15, 12, 10, 8, 7, 6, 5, 4, 3] # 10 rounds

AUDIENCE_LISTS = {
    "easy": ["5-year-old", "beginner English learner", "friend", "grandma", "general audience"],
    "medium": ["5-year-old", "high schooler", "college professor", "beginner English learner",
               "friend", "supervisor", "grandma", "business colleague"],
    "hard": ["5-year-old", "high schooler", "college professor", "beginner English learner", 
             "friend", "love interest", "supervisor", "scientist", "investor", "grandma", "poet",
             "business colleague"]
}

# set page config
logo_path = Path(__file__).parent / "img/thumbnail.png"
st.set_page_config(
    page_title="Concise.ly",
    page_icon=str(logo_path),
    layout="centered",
)

# load concepts
concepts = pd.read_csv("concepts_db/concepts.csv")

# load logo
logo_path = Path(__file__).parent / "img/logo.png"
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
st.session_state.setdefault("include_audience", True)
st.session_state.setdefault("total_points", 0)
st.session_state.setdefault("round_start_time", None)
st.session_state.setdefault("start_time", None)
st.session_state.setdefault("round_durations", [])  # list of seconds per round - for overall tracking
st.session_state.setdefault("last_round_time", None)
st.session_state.setdefault("word_limit_penalty", 0)

# --- logo home/reset via query param ---
page = (
    st.query_params.get("page")
    if hasattr(st, "query_params")
    else st.experimental_get_query_params().get("page", [None])[0]
)

if page == "home":
    st.session_state.clear()
    st.session_state.mode = "home"
    st.session_state.round = 0
    st.session_state.setdefault("include_audience", True)

    if hasattr(st, "query_params"):
        st.query_params.clear()
    else:
        st.experimental_set_query_params()

    st.rerun()



@st.dialog("Round Feedback", width="small", dismissible=False)
def feedback_popup():
    final_score = st.session_state.get("final_score", 0)
    content_score = st.session_state.get("content_score", 0)
    time_bonus_val = st.session_state.get("time_bonus", 0)
    elapsed_seconds = st.session_state.get("elapsed_seconds", 0)
    word_limit_penalty = st.session_state.get("word_limit_penalty", 0)
    
    # Determine score color
    if final_score >= 90:
        score_color = "normal"  # green in streamlit
    elif final_score >= 70:
        score_color = "off"  # gray/neutral
    else:
        score_color = "inverse"  # red
    
    # Main score display with st.metric
    st.metric(
        label="You scored",
        value=f"{final_score:.1f} points",
        delta=None,
        delta_color=score_color
    )
    
    # Context line (subdued, like in the React version)
    context_parts = [f"Content: {content_score:.1f}"]
    
    if time_bonus_val != 0:
        if time_bonus_val > 0:
            time_text = f" Time bonus: +{time_bonus_val:.1f} pts"
        else:
            time_text = f" Time penalty: -{time_bonus_val:.1f} pts"
        context_parts.append(time_text)
    
    if word_limit_penalty > 0:
        context_parts.append(f"Words: -{word_limit_penalty:.1f} pts")
    
    st.markdown(
        f"<p style='color: #94a3b8; font-size: 0.9em; margin-top: -10px;'>{' · '.join(context_parts)}</p>",
        unsafe_allow_html=True
    )
    
    # Score breakdown as expandable section
    with st.expander("Score Breakdown"):
        feedback_dict = st.session_state.get("feedback_dict", {})
        brevity_score = st.session_state.get("brevity_score", 0)
        accuracy_score = st.session_state.get("accuracy_score", 0)
        audience_fit_score = st.session_state.get("audience_fit_score", 0)
        grammar_score = st.session_state.get("grammar_score", 0)
        
        st.markdown(f"**Brevity:** {brevity_score}/10 - {feedback_dict.get('brevity', 'N/A')}")
        st.markdown(f"**Accuracy:** {accuracy_score}/10 - {feedback_dict.get('accuracy', 'N/A')}")
        label = "Audience Fit" if st.session_state.get("include_audience", True) else "Clarity"
        st.markdown(f"**{label}:** {audience_fit_score}/10 - {feedback_dict.get('audience_fit', 'N/A')}")
        st.markdown(f"**Grammar:** {grammar_score}/10 - {feedback_dict.get('grammar', 'N/A')}")
        
        # Show time/word details in breakdown if they apply
        if time_bonus_val != 0 or word_limit_penalty > 0:
            st.divider()
        
        if time_bonus_val != 0:
            bonus_type = "Bonus" if time_bonus_val > 0 else "Penalty"
            st.markdown(f"**Time {bonus_type}:** {time_bonus_val:+.1f} pts ({elapsed_seconds:.1f}s)")
        
        if word_limit_penalty > 0:
            st.markdown(f"**Word Limit Penalty:** -{word_limit_penalty:.1f} pts (exceeded word limit)")
    
    # Overall feedback
    st.markdown("**Overall Feedback:**")
    feedback_dict = st.session_state.get("feedback_dict", {})
    st.write(feedback_dict.get('overall', 'N/A'))
    
    st.markdown("**Improved version:**")
    st.write(st.session_state.get("improved_version", ""))
    
    if st.button("Next Round", use_container_width=True, type="primary"):
        # Clear all scoring-related keys
        keys_to_clear = (
            "concept", "audience", "explanation", "improved_version", 
            "show_feedback", "final_score", "content_score", "time_bonus", "elapsed_seconds",
            "brevity_score", "accuracy_score", "audience_fit_score", "grammar_score",
            "feedback_dict", "last_round_time", "word_limit_penalty"
        )
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.session_state.explanation = ""
        st.session_state.round += 1

        # Check if game is complete
        if st.session_state.round >= len(WORD_COUNTS):
            st.session_state.mode = "summary"
        else:
            # Reset start_time for the new round
            st.session_state.start_time = None
            st.session_state.round_start_time = None

        # Reset start_time for the new round
        st.session_state.start_time = None
        st.session_state.round_start_time = None
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
        "Avoid the awkwardness.", "Communicate better.", "Say it right.", "No more tip-of-the-tongue.",
         "Blow them away with how well you speak.", "Make your words count.", "No more confusion."
    ])
    st.write("<h4>" + tagline + "</h4>", unsafe_allow_html=True)

    st.write("""
**Instructions:** You will be given a concept, an audience, and a word limit. Within these parameters, you must explain or define the concept to match the context. 
             
We will evaluate your response and give you suggestions.
""")
    
    difficulty = st.radio("Choose difficulty", ["easy", "medium", "hard"], horizontal=True)
    st.session_state.difficulty = difficulty

    include_audience = st.toggle(
        "Include audience",
        value=st.session_state.include_audience,
        key="include_audience_toggle"
    )
    st.session_state.include_audience = include_audience
    
    col1, col2, col3 = st.columns([3,3,2])
    with col3:
        if st.button("Start game", use_container_width=True, type="primary"):
            st.session_state.mode = "gameplay"
            st.rerun()


# ---------- GAMEPLAY SCREEN ----------
elif st.session_state.mode == "gameplay":
    # header
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <a href="?page=home" target="_self" style="text-decoration:none;">
                <img src="data:image/png;base64,{LOGO_B64}" alt="Concise.ly" style="height: 64px;"/>
            </a>
            <div style="display: flex; flex-direction: column; align-items: flex-start; line-height: 1.2;">
                <p style="margin: 0;"><b>Difficulty:</b> {st.session_state.difficulty.title()}</p>
                <p style="margin: 0;"><b>Round:</b> {st.session_state.round + 1}/{len(WORD_COUNTS)}</p>
                <p style="margin: 0;"><b>Total points:</b> {st.session_state.total_points:.1f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.space("small")

    # parameters
    difficulty = st.session_state.difficulty
    concept_list = concepts[difficulty].tolist()
    
    if "concept" not in st.session_state:
        st.session_state.concept = random.choice(concept_list)
    
    # always (re)create an audience for the round
    if "audience" not in st.session_state:
        if st.session_state.include_audience:
            st.session_state.audience = random.choice(AUDIENCE_LISTS[difficulty])
        else:
            st.session_state.audience = "General audience"
    
    # Start timer for this round if not already started and no feedback is being shown
    if st.session_state.round_start_time is None and not st.session_state.get("show_feedback", False):
        st.session_state.round_start_time = time.time()
        st.session_state.start_time = datetime.now()

    # always define local variable
    audience = st.session_state.audience
    concept = st.session_state.concept

    if st.session_state.include_audience:
        st.info("Explain what **" + concept + "** is to " + "a **" + audience + "**.")
    else:
        st.info("Explain what **" + concept + "** is.")

    # explanation
    explanation = st.text_area("Your explanation", key="explanation")

    # word count info
    if st.session_state.round > len(WORD_COUNTS) - 1:
        word_limit = WORD_COUNTS[len(WORD_COUNTS) - 1]
    else:
        word_limit = WORD_COUNTS[st.session_state.round]
    current_word_count = len(explanation.split())
    words_left = word_limit - current_word_count
    if words_left <= 0:
        wl_color = "#E74C3C" # red
    elif words_left <= max(2, min(word_limit - 1, int(round(word_limit * 0.3)) + 1)):
        wl_color = "#FFB627" # yellow
    else:
        wl_color = "white"
    st.markdown(
        f"""
        <div style="text-align: right; line-height: 1.1;">
            <p style="margin: 0; opacity: 0.7;">
                Current word count: {current_word_count}
            </p>
            <p style="margin: 0; font-weight: 700;">
                <span style="color: {wl_color};">Words left: {words_left}</span>
            </p>
            <br/>
        </div>
        """,
        unsafe_allow_html=True,
    )  

    # submit button

    col1, col2, col3 = st.columns([3,4,2])
    with col3:
        if st.button("Submit", use_container_width=True, type="primary"):
            if not explanation.strip():
                st.error("Please enter an explanation.")
                st.stop()

            if current_word_count > word_limit:
                st.error("Word limit exceeded (-10 points). Please try again.")
                st.session_state.word_limit_penalty += 10
                st.stop()
            
            # Calculate elapsed time
            elapsed_seconds = 0
            if st.session_state.start_time is not None:
                elapsed_seconds = (datetime.now() - st.session_state.start_time).total_seconds()
                st.session_state.round_durations.append(elapsed_seconds)
                # reset so next round can set a new start time
                st.session_state.round_start_time = None
                st.session_state.start_time = None

            with st.status("Scoring your explanation...", expanded=False) as s:
                # Generate LLM feedback
                prompt = EXPLANATION_SCORING_PROMPT.format(
                    concept=concept,
                    audience=audience,
                    explanation=explanation,
                    word_count=current_word_count,
                    word_limit=word_limit,
                )
                try:
                    result = generate_score(prompt)
                    
                    # Parse JSON response
                    # Try to extract JSON if it's wrapped in markdown code blocks
                    result_clean = result.strip()
                    if result_clean.startswith("```"):
                        # Remove markdown code block markers
                        lines = result_clean.split("\n")
                        result_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else result_clean
                    elif result_clean.startswith("```json"):
                        lines = result_clean.split("\n")
                        result_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else result_clean
                    
                    # Parse JSON
                    score_data = json.loads(result_clean)
                    
                    # Extract and clamp subscores to [0, 10]
                    brevity_score = max(0, min(10, int(score_data.get("brevity_score", 0))))
                    accuracy_score = max(0, min(10, int(score_data.get("accuracy_score", 0))))
                    audience_fit_score = max(0, min(10, int(score_data.get("audience_fit_score", 0))))
                    grammar_score = max(0, min(10, int(score_data.get("grammar_score", 0))))
                    
                    # Compute content score
                    content_score = compute_content_score(
                        brevity_score,
                        accuracy_score,
                        audience_fit_score,
                        grammar_score,
                        include_audience=st.session_state.include_audience
                    )

                    # Word limit penalty for THIS round
                    penalty = st.session_state.get("word_limit_penalty", 0)

                    # Compute final score with time bonus and penalty
                    final_score = compute_final_score(content_score, elapsed_seconds, penalty=penalty)

                    # If accuracy is 0, final score should be 0
                    if accuracy_score == 0:
                        final_score = 0.0

                    # Compute time bonus (for display)
                    bonus = time_bonus(elapsed_seconds)

                    
                    # Round all scores to one decimal place
                    content_score = round(content_score, 1)
                    final_score = round(final_score, 1)
                    bonus = round(bonus, 1)
                    elapsed_seconds = round(elapsed_seconds, 1)
                    
                    # Store feedback dict for display
                    feedback_dict = score_data.get("feedback", {})
                    
                    # Store in session state
                    st.session_state.final_score = final_score
                    st.session_state.content_score = content_score
                    st.session_state.time_bonus = bonus
                    st.session_state.elapsed_seconds = elapsed_seconds
                    st.session_state.brevity_score = brevity_score
                    st.session_state.accuracy_score = accuracy_score
                    st.session_state.audience_fit_score = audience_fit_score
                    st.session_state.grammar_score = grammar_score
                    st.session_state.feedback_dict = feedback_dict
                    st.session_state.improved_version = score_data.get("improved_version", "")
                    st.session_state.show_feedback = True
                    st.session_state.total_points += final_score

                    s.update(label="Done!", state="complete")
                except json.JSONDecodeError as e:
                    st.error(f"Error parsing JSON response: {str(e)}\n\nResponse was: {result[:500]}")
                except Exception as e:
                    st.error(f"Error generating feedback: {str(e)}")
                st.rerun()
        
        # Display feedback as popup
        if st.session_state.get("show_feedback", False):
            feedback_popup()

# ---------- SUMMARY SCREEN ----------
elif st.session_state.mode == "summary":
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <a href="?page=home" target="_self" style="text-decoration:none;">
                <img src="data:image/png;base64,{LOGO_B64}" alt="Concise.ly" style="height: 64px;"/>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Calculate performance message
    total_points = st.session_state.total_points
    number_of_rounds = len(WORD_COUNTS)
    max_possible = 100 * number_of_rounds
    
    if total_points > max_possible * 0.90:
        performance_msg = "You're a master!"
    elif total_points > max_possible * 0.75:
        performance_msg = "Nice work!"
    elif total_points > max_possible * 0.5:
        performance_msg = "Good job!"
    elif total_points > max_possible * 0.25:
        performance_msg = "Keep practicing!"
    else:
        performance_msg = "Better luck next time!"
    
    # Display total score with performance message
    st.write("<h2>" + performance_msg + "</h2>", unsafe_allow_html=True)
    st.metric(
        label="Final Score",
        value=f"{total_points:.1f} points",
    )
    
    # Placeholder for skill ratings
    # skill ratings
    # will use a session_state dictionary round number -> points earned, each skill rating, time elapsed
    
    # Return home button
    if st.button("Return Home", use_container_width=True):
        st.session_state.clear()
        st.session_state.mode = "home"
        st.session_state.round = 0
        st.session_state.setdefault("include_audience", True)
        st.rerun() 