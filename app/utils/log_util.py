"""
Utility module for logging configurations and operations.
"""

from typing import Optional, Literal, Dict, Any
import json
from termcolor import colored
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter


def get_label(log_method: str) -> str:
    """
    Get a colored label for the log level.

    Args:
        log_method (str): The logging method (e.g., 'INFO', 'ERROR').

    Returns:
        str: The colored label for the log level.
    """
    lm_upper = log_method.upper()
    on_color: Optional[
        Literal[
            "on_black",
            "on_grey",
            "on_red",
            "on_green",
            "on_yellow",
            "on_blue",
            "on_magenta",
            "on_cyan",
            "on_light_grey",
            "on_dark_grey",
            "on_light_red",
            "on_light_green",
            "on_light_yellow",
            "on_light_blue",
            "on_light_magenta",
            "on_light_cyan",
            "on_white",
        ]
    ] = (
        "on_white" if lm_upper == "CRITICAL" else None
    )
    colors: Dict[
        str,
        Literal[
            "black",
            "grey",
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "light_grey",
            "dark_grey",
            "light_red",
            "light_green",
            "light_yellow",
            "light_blue",
            "light_magenta",
            "light_cyan",
            "white",
        ],
    ] = {
        "INFO": "green",
        "DEBUG": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }
    label: str = colored(lm_upper, colors[lm_upper], on_color)
    return label


def pretty_print_json(logger, log_method: str, event_dict: Dict[str, Any]) -> bytes:
    """
    Pretty print a JSON log event.

    Args:
        logger: The logger instance.
        log_method (str): The logging method (e.g., 'INFO', 'ERROR').
        event_dict (dict): The event dictionary to log.

    Returns:
        bytes: The formatted and colored JSON log event.
    """
    formatted_json = json.dumps(event_dict, indent=4, sort_keys=True)
    colorful_json = highlight(
        formatted_json,
        JsonLexer(),
        TerminalFormatter(),
    )
    return str.encode(colorful_json)


def filter_event(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out non-required fields for development mode logging.

    Args:
        event_dict (dict): The event dictionary to filter.

    Returns:
        dict: The filtered event dictionary.
    """
    non_required_for_dev = [
        "event",
        "level",
        "method",
        "request_id",
        "url",
        "timestamp",
    ]

    for key in non_required_for_dev:
        if key in event_dict:
            del event_dict[key]

    return event_dict


def pretty_print_for_dev(logger, log_method: str, event_dict: Dict[str, Any]) -> bytes:
    """
    Pretty print a log event for development mode.

    Args:
        logger: The logger instance.
        log_method (str): The logging method (e.g., 'INFO', 'ERROR').
        event_dict (dict): The event dictionary to log.

    Returns:
        bytes: The formatted and colored log event.
    """
    label = get_label(log_method)
    primary = f"{label}:{event_dict['event']}"
    secondary = ""

    filtered_event = filter_event(event_dict)
    if len(filtered_event):
        formatted_json = json.dumps(filtered_event, sort_keys=True)
        colored_event = highlight(
            formatted_json,
            JsonLexer(),
            TerminalFormatter(),
        )
        secondary = f"{colored_event or ''}"

    text = f"{primary}{secondary}"
    encoded = str.encode(text)

    return encoded
