def format_active_time_uz(seconds: int) -> str:
    """Format seconds as Uzbek-friendly duration (e.g. 3661 -> '1 soat 1 daqiqa')."""
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return f"{seconds} soniya"

    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        if sec:
            return f"{minutes} daqiqa {sec} soniya"
        return f"{minutes} daqiqa"

    hours, minutes = divmod(minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours} soat")
    if minutes:
        parts.append(f"{minutes} daqiqa")
    if sec and not hours:
        parts.append(f"{sec} soniya")
    return " ".join(parts) if parts else "0 soniya"
