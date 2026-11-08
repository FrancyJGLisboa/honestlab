def predict(history, target):
    """Per-user ticket rate on the same weekday (last 10 non-release days) x latest users, release lift from past releases."""
    wd, rel = target[1], target[2]
    users_now = history[-1][3]
    base = [h[4] / h[3] for h in history if h[1] == wd and h[2] == 0][-10:]
    level = sum(base) / len(base) * users_now
    if not rel:
        return level
    n = [h for h in history if h[2] == 0]
    ratios = []
    for h in [h for h in history if h[2] == 1][-12:]:
        same = [x[4] / x[3] for x in n if x[1] == h[1] and x[0] < h[0]][-10:]
        if same:
            ratios.append((h[4] / h[3]) / (sum(same) / len(same)))
    lift = sum(ratios) / len(ratios) if ratios else 1.0
    return level * lift
