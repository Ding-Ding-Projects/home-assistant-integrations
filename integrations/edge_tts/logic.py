"""Pure helpers for Edge TTS: option parsing, voice labels and locale grouping.

This module has no Home Assistant imports so it can be tested on its own.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

DEFAULT_VOICE = "en-US-AriaNeural"
RATE_RANGE = (-50, 100)
PITCH_RANGE = (-50, 50)
VOLUME_RANGE = (-50, 50)

_NUMBER = re.compile(r"^([+-]?)\s*(\d+(?:\.\d+)?)$")


def _parse_amount(value: Any, unit: str, name: str, bounds: tuple[int, int]) -> int:
    """Parse "+10%", "10", 10 or 10.0 into a validated integer."""
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()
        if text.lower().endswith(unit.lower()):
            text = text[: -len(unit)].strip()
        match = _NUMBER.match(text)
        if not match:
            raise ValueError(f"{name} must look like +10{unit} or 10, got {value!r}")
        number = float(match.group(2))
        if match.group(1) == "-":
            number = -number
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be a finite number")
    result = int(round(number))
    low, high = bounds
    if not low <= result <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {result}")
    return result


def parse_rate(value: Any) -> int:
    """Speaking rate change in percent, -50 to +100."""
    return _parse_amount(value, "%", "rate", RATE_RANGE)


def parse_volume(value: Any) -> int:
    """Volume change in percent, -50 to +50."""
    return _parse_amount(value, "%", "volume", VOLUME_RANGE)


def parse_pitch(value: Any) -> int:
    """Pitch change in hertz, -50 to +50."""
    return _parse_amount(value, "Hz", "pitch", PITCH_RANGE)


def format_percent(amount: int) -> str:
    """Format a percent change the way edge-tts expects, such as +10% or -5%."""
    return f"{amount:+d}%"


def format_hertz(amount: int) -> str:
    """Format a pitch change the way edge-tts expects, such as +0Hz or -20Hz."""
    return f"{amount:+d}Hz"


_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")


def _split_camel(text: str) -> str:
    return _CAMEL.sub(" ", text).strip()


def voice_locale(voice: dict[str, Any]) -> str:
    """Return the locale of a voice, for example en-CA."""
    locale = voice.get("Locale")
    if locale:
        return str(locale)
    parts = str(voice.get("ShortName", "")).split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else ""


def voice_name(voice: dict[str, Any]) -> str:
    """Return a friendly first name such as Clara or William Multilingual."""
    friendly = str(voice.get("FriendlyName", ""))
    match = re.match(r"^Microsoft (.+?) Online", friendly)
    if match:
        return _split_camel(match.group(1))
    short = str(voice.get("ShortName", ""))
    locale = voice_locale(voice)
    if locale and short.startswith(locale + "-"):
        short = short[len(locale) + 1 :]
    short = short.rsplit("-", 1)[-1]
    if short.endswith("Neural"):
        short = short[: -len("Neural")]
    return _split_camel(short) or str(voice.get("ShortName", ""))


def locale_label(voice: dict[str, Any]) -> str:
    """Return a readable locale such as English (Canada)."""
    name = voice.get("LocaleName")
    if name:
        return str(name)
    friendly = str(voice.get("FriendlyName", ""))
    if " - " in friendly:
        return friendly.rsplit(" - ", 1)[-1].strip()
    return voice_locale(voice)


def voice_label(voice: dict[str, Any]) -> str:
    """Return a label such as 'English (Canada), Clara, Female'."""
    parts = [locale_label(voice), voice_name(voice)]
    gender = voice.get("Gender")
    if gender:
        parts.append(str(gender))
    return ", ".join(parts)


def _sort_key(voice: dict[str, Any]) -> tuple[str, str, str]:
    return (locale_label(voice).lower(), voice_name(voice).lower(), str(voice.get("ShortName", "")))


def sort_voices(voices: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort voices by locale label, then name."""
    return sorted(voices, key=_sort_key)


def group_voices_by_locale(voices: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group voices by locale code, locales in label order, voices in name order."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for voice in sort_voices(voices):
        grouped.setdefault(voice_locale(voice), []).append(voice)
    return grouped


def voice_options(voices: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Selector options sorted so voices of one locale sit together."""
    return [
        {"value": str(v["ShortName"]), "label": voice_label(v)}
        for v in sort_voices(voices)
        if v.get("ShortName")
    ]


def locales_from_voices(voices: Iterable[dict[str, Any]]) -> list[str]:
    """Sorted unique locale codes."""
    return sorted({voice_locale(v) for v in voices if voice_locale(v)})


def _norm(locale: str) -> str:
    return locale.replace("_", "-").lower()


def voices_for_language(voices: Iterable[dict[str, Any]], language: str) -> list[dict[str, Any]]:
    """Voices for a language tag: exact locale match, or by primary language such as 'en'."""
    wanted = _norm(language)
    voices = list(voices)
    exact = [v for v in voices if _norm(voice_locale(v)) == wanted]
    if exact:
        return sort_voices(exact)
    if "-" not in wanted:
        return sort_voices(v for v in voices if _norm(voice_locale(v)).split("-")[0] == wanted)
    return []


def find_voice(voices: Iterable[dict[str, Any]], short_name: str) -> dict[str, Any] | None:
    for voice in voices:
        if voice.get("ShortName") == short_name:
            return voice
    return None


def default_language_for(voices: Iterable[dict[str, Any]], short_name: str) -> str:
    """Locale of the chosen voice, from the voice list or from the name itself."""
    voices = list(voices)
    voice = find_voice(voices, short_name)
    if voice:
        return voice_locale(voice)
    match = re.match(r"^([a-z]{2,3}(?:-[A-Za-z]{4})?-[A-Z]{2})-", short_name)
    return match.group(1) if match else "en-US"


def choose_voice(
    voices: Iterable[dict[str, Any]],
    language: str | None,
    requested: str | None,
    default: str,
) -> str:
    """Pick the voice for one call.

    An explicit voice always wins. Otherwise the default voice is used when it speaks the
    requested language; if not, the first voice for that language; if none, the default.
    """
    if requested:
        return requested
    voices = list(voices)
    if not language:
        return default
    default_voice = find_voice(voices, default)
    if default_voice and _norm(voice_locale(default_voice)) == _norm(language):
        return default
    matches = voices_for_language(voices, language)
    if matches:
        preferred = [v for v in matches if "Multilingual" not in str(v.get("ShortName", ""))]
        return str((preferred or matches)[0]["ShortName"])
    return default


def resolve_call_options(
    options: dict[str, Any] | None, defaults: dict[str, Any]
) -> dict[str, str]:
    """Merge per-call options over the saved defaults and format them for edge-tts.

    Raises ValueError for an out-of-range or malformed value.
    """
    options = options or {}
    merged = {
        key: options.get(key, defaults.get(key, 0)) for key in ("rate", "pitch", "volume")
    }
    return {
        "rate": format_percent(parse_rate(merged["rate"])),
        "pitch": format_hertz(parse_pitch(merged["pitch"])),
        "volume": format_percent(parse_volume(merged["volume"])),
    }
