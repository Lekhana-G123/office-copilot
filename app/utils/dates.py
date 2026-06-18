import re
from datetime import datetime, timedelta

_TODAY = datetime.now().date()
_TOMORROW = (_TODAY + timedelta(days=1)).isoformat()
_TODAY_STR = _TODAY.isoformat()


def today_str() -> str:
    return _TODAY_STR


def tomorrow_str() -> str:
    return _TOMORROW


def resolve_date(date_str: str) -> str:
    """Convert 'today', 'tomorrow', or YYYY-MM-DD to ISO date string."""
    raw = (date_str or "").strip().lower()
    if raw in ("today",):
        return _TODAY_STR
    if raw in ("tomorrow",):
        return _TOMORROW
    if raw in ("day after tomorrow",):
        return (_TODAY + timedelta(days=2)).isoformat()
    if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
        return raw[:10]
    raise ValueError(
        f"Invalid date '{date_str}'. Use YYYY-MM-DD, 'today', or 'tomorrow'."
    )


def parse_time_range(date_str: str, start_hour: int, end_hour: int) -> tuple[datetime, datetime]:
    date = resolve_date(date_str)
    start_time = datetime.fromisoformat(f"{date}T{int(start_hour):02d}:00:00")
    end_time = datetime.fromisoformat(f"{date}T{int(end_hour):02d}:00:00")
    return start_time, end_time


def parse_due_date(date_str: str) -> datetime:
    date = resolve_date(date_str)
    return datetime.fromisoformat(f"{date}T18:00:00")


def parse_hour_range(text: str, default_start: int = 9, default_end: int = 17) -> tuple[int, int]:
    """Parse times like 3-7pm, 3pm to 7pm, 15-19."""
    t = text.lower().strip()
    m = re.search(
        r"(\d{1,2})(?::\d{2})?\s*(am|pm)?\s*(?:-|–|to)\s*(\d{1,2})(?::\d{2})?\s*(am|pm)?",
        t,
    )
    if not m:
        return default_start, default_end

    def to_24(h: str, ampm: str | None, fallback_ampm: str | None) -> int:
        hour = int(h)
        mer = (ampm or fallback_ampm or "").lower()
        if mer == "pm" and hour < 12:
            hour += 12
        if mer == "am" and hour == 12:
            hour = 0
        if not mer and hour <= 7:
            hour += 12
        return hour

    end_mer = m.group(4) or m.group(2)
    start = to_24(m.group(1), m.group(2), end_mer)
    end = to_24(m.group(3), m.group(4), m.group(2))
    if end <= start:
        end = start + 1
    return start, end
