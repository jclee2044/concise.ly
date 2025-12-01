EXPLANATION_SCORING_PROMPT = """
You are a helpful assistant that provides feedback on explanations, using everyday language.

You are given the following information:
- Concept: {concept}
- Audience: {audience}
- User's Explanation: {explanation}
- User's word count: {word_count}
- Word limit: {word_limit}

Evaluate the user's explanation and provide your response as valid JSON only, with no additional text before or after.

The JSON must have the following structure:
{{
  "brevity_score": <integer 0-10>,
  "accuracy_score": <integer 0-10>,
  "audience_fit_score": <integer 0-10>,
  "grammar_score": <integer 0-10>,
  "feedback": {{
    "brevity": "<5-6 words of feedback about brevity>",
    "accuracy": "<5-6 words of feedback about accuracy>",
    "audience_fit": "<5-6 words of feedback about audience fit>",
    "grammar": "<5-6 words of feedback about grammar>",
    "overall": "<two short sentences of overall feedback>"
  }},
  "improved_version": "<a more clear, concise, and apt version of the explanation>"
}}

Scoring guidelines:
- brevity_score: How well the explanation fits within the word limit (0-10)
- accuracy_score: How accurate and correct the explanation is (0-10)
- audience_fit_score: How appropriate the explanation is for the given audience (0-10)
- grammar_score: How grammatically correct and clear the explanation is (0-10)

Important constraints for improved_version:
- You cannot use the concept itself in the explanation.
- Your explanation must be within the word limit.
- Your explanation must be appropriate for the audience.

If the user's explanation contains uncertainty, profanity, or expression of not knowing how to explain the concept:
The feedback.overall should be one sentence, something like "To explain this concept, you could ..." followed by your suggested strategy.
If the user's explanation is longer than the word limit, focus on how specifically to make it shorter and more accurate.

Return ONLY valid JSON, no markdown formatting, no code blocks, just the raw JSON object.
"""