from datetime import datetime, timedelta
from typing import Tuple


def get_date_range(hours: int = 24) -> Tuple[datetime, datetime]:
    """
    Get start and end datetime for a time range.

    Args:
        hours: Number of hours to look back from now

    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    end = datetime.now()
    start = end - timedelta(hours=hours)
    return start, end


def datetime_to_unix_ms(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp in milliseconds.

    Args:
        dt: Datetime object

    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def unix_ms_to_datetime(timestamp: int) -> datetime:
    """
    Convert Unix timestamp in milliseconds to datetime.

    Args:
        timestamp: Unix timestamp in milliseconds

    Returns:
        Datetime object
    """
    return datetime.fromtimestamp(timestamp / 1000)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        format_str: Format string (default: YYYY-MM-DD HH:MM)

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def get_today_date_string() -> str:
    """
    Get today's date as YYYY-MM-DD string.

    Returns:
        Date string
    """
    return datetime.now().strftime("%Y-%m-%d")


def is_within_hours(timestamp: int, hours: int = 24) -> bool:
    """
    Check if a Unix timestamp (ms) is within the last N hours.

    Args:
        timestamp: Unix timestamp in milliseconds
        hours: Number of hours to check

    Returns:
        True if timestamp is within the time range
    """
    cutoff = datetime_to_unix_ms(datetime.now() - timedelta(hours=hours))
    return timestamp >= cutoff
