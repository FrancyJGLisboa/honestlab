def predict(history, target):
    """Average of the same weekday over the last 4 weeks (today's method)."""
    vals = [h[4] for h in history if h[1] == target[1]][-4:]
    return sum(vals) / len(vals)
