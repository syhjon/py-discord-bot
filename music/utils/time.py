def format_time(seconds):
    if seconds is None or seconds == "未知時長":
        return "未知"
    seconds = int(seconds)
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


def create_progress_bar(current_time, duration):
    if duration == 0 or duration is None or duration == "未知時長":
        return "━" * 19 + "🔘"
    total_bars = 20
    current_bar = round((current_time / duration) * total_bars)
    current_bar = min(max(current_bar, 0), total_bars)

    if current_bar == total_bars:
        return "━" * 19 + "🔘"
    return "━" * current_bar + "🔘" + "─" * (total_bars - current_bar - 1)
