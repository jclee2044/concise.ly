def compute_content_score(brevity, accuracy, audience_fit, grammar, include_audience=True):
    """
    Persona mode (include_audience=True):
        accuracy*4 + audience_fit*3 + brevity*2 + grammar*1

    General mode (include_audience=False):
        accuracy*5 + brevity*3 + audience_fit*1 + grammar*1
    """
    if include_audience:
        # persona mode
        score = (
            accuracy * 4 +
            audience_fit * 3 +
            brevity * 2 +
            grammar * 1
        )
    else:
        # general audience mode (audience_fit ~= clarity)
        score = (
            accuracy * 5 +
            brevity * 3 +
            audience_fit * 1 +
            grammar * 1
        )

    return max(0, min(100, score))



def time_bonus(elapsed_seconds):
    """
    Compute a smooth linear time bonus in the range -10 to +10:
    - 0s → +10
    - 60s → 0
    - 120s+ → -10
    
    Args:
        elapsed_seconds: Time elapsed in seconds
    
    Returns:
        Time bonus between -10 and +10
    """
    if elapsed_seconds <= 0:
        return 10.0
    elif elapsed_seconds >= 120:
        return -10.0
    else:
        # Linear interpolation: 0s -> +10, 60s -> 0, 120s -> -10
        # Slope: (0 - 10) / (60 - 0) = -10/60 = -1/6
        # For 0-60s: bonus = 10 - (elapsed / 6)
        # For 60-120s: slope = (-10 - 0) / (120 - 60) = -10/60 = -1/6
        # For 60-120s: bonus = 0 - ((elapsed - 60) / 6) = -(elapsed - 60) / 6
        if elapsed_seconds <= 60:
            return 10.0 - (elapsed_seconds / 6.0)
        else:
            return -(elapsed_seconds - 60) / 6.0


def compute_final_score(content_score, elapsed_seconds):
    """
    Compute final score by adding time bonus to content score and clamping to 0-100.
    
    Args:
        content_score: Content score (0-100)
        elapsed_seconds: Time elapsed in seconds
    
    Returns:
        Final score
    """
    bonus = time_bonus(elapsed_seconds)
    final = content_score + bonus
    return final

