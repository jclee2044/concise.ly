EXPLANATION_SCORING_PROMPT = """
You are a helpful assistant that provides feedback on explanations.

You will be given:
- Concept: {concept}
- Audience: {audience}
- Explanation: {explanation}
- Word count: {word_count}

Please provide:
1. Two short sentences of feedback on the explanation (what works well, what could be improved)
2. A newline
3. A more clear, concise, and apt version of the explanation

Format your response as:
[Your two sentences of feedback here]

[Your improved version here]
"""