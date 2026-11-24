import asyncio

import pytest

from conftest import load_logic

L = load_logic("edge_tts")
E = load_logic("edge_tts", "engine")


def voice(short, locale, friendly, locale_name=None, gender="Female"):
    data = {
        "ShortName": short,
        "Locale": locale,
        "FriendlyName": friendly,
        "Gender": gender,
    }
    if locale_name:
        data["LocaleName"] = locale_name
    return data


VOICES = [
    voice("en-US-AriaNeural", "en-US", "Microsoft Aria Online (Natural) - English (United States)", "English (United States)"),
    voice("en-CA-ClaraNeural", "en-CA", "Microsoft Clara Online (Natural) - English (Canada)", "English (Canada)"),
    voice("en-CA-LiamNeural", "en-CA", "Microsoft Liam Online (Natural) - English (Canada)", "English (Canada)", "Male"),
    voice("en-AU-WilliamMultilingualNeural", "en-AU", "Microsoft WilliamMultilingual Online (Natural) - English (Australia)", "English (Australia)", "Male"),
    voice("fr-FR-DeniseNeural", "fr-FR", "Microsoft Denise Online (Natural) - French (France)", "French (France)"),
    voice("zh-CN-liaoning-XiaobeiNeural", "zh-CN", "Microsoft Xiaobei Online (Natural) - Chinese (Liaoning, China)", "Chinese (Liaoning, China)"),
]


@pytest.mark.parametrize(
    "value,expected",
    [("+10%", 10), ("10", 10), (10, 10), (10.4, 10), ("-5 %", -5), (" +0% ", 0), ("100%", 100), (-50, -50)],
)
def test_parse_rate_valid(value, expected):
    assert L.parse_rate(value) == expected


@pytest.mark.parametrize("value", ["101%", "-51", "fast", "", None, True, "+-5%", "10Hz", float("nan"), float("inf")])
def test_parse_rate_invalid(value):
    with pytest.raises(ValueError):
        L.parse_rate(value)


def test_parse_pitch_and_volume():
    assert L.parse_pitch("+20Hz") == 20
    assert L.parse_pitch("-50hz") == -50
    assert L.parse_volume("+50%") == 50
    with pytest.raises(ValueError):
        L.parse_pitch("51")
    with pytest.raises(ValueError):
        L.parse_volume("-60%")
    with pytest.raises(ValueError):
        L.parse_pitch("5%")


def test_formatting():
    assert L.format_percent(10) == "+10%"
    assert L.format_percent(0) == "+0%"
    assert L.format_percent(-5) == "-5%"
    assert L.format_hertz(0) == "+0Hz"
    assert L.format_hertz(-20) == "-20Hz"


def test_resolve_call_options_overrides_defaults():
    defaults = {"rate": 10, "pitch": -5, "volume": 0}
    assert L.resolve_call_options(None, defaults) == {"rate": "+10%", "pitch": "-5Hz", "volume": "+0%"}
    result = L.resolve_call_options({"rate": "+30%", "volume": "20"}, defaults)
    assert result == {"rate": "+30%", "pitch": "-5Hz", "volume": "+20%"}
    with pytest.raises(ValueError):
        L.resolve_call_options({"pitch": "99Hz"}, defaults)


def test_labels():
    assert L.voice_label(VOICES[1]) == "English (Canada), Clara, Female"
    assert L.voice_label(VOICES[3]) == "English (Australia), William Multilingual, Male"
    assert L.voice_name({"ShortName": "de-DE-KatjaNeural", "Locale": "de-DE"}) == "Katja"
    assert L.locale_label({"FriendlyName": "Microsoft X Online (Natural) - German (Germany)"}) == "German (Germany)"
    assert L.voice_locale({"ShortName": "ja-JP-NanamiNeural"}) == "ja-JP"


def test_locale_grouping_and_options():
    grouped = L.group_voices_by_locale(VOICES)
    assert list(grouped) == ["zh-CN", "en-AU", "en-CA", "en-US", "fr-FR"]
    assert [v["ShortName"] for v in grouped["en-CA"]] == ["en-CA-ClaraNeural", "en-CA-LiamNeural"]
    options = L.voice_options(VOICES)
    assert len(options) == len(VOICES)
    ca = [i for i, o in enumerate(options) if o["value"].startswith("en-CA")]
    assert ca == list(range(ca[0], ca[0] + 2))
    assert {"value": "en-CA-ClaraNeural", "label": "English (Canada), Clara, Female"} in options
    assert L.locales_from_voices(VOICES) == ["en-AU", "en-CA", "en-US", "fr-FR", "zh-CN"]


def test_voices_for_language():
    assert [v["ShortName"] for v in L.voices_for_language(VOICES, "en-CA")] == ["en-CA-ClaraNeural", "en-CA-LiamNeural"]
    assert len(L.voices_for_language(VOICES, "en")) == 4
    assert len(L.voices_for_language(VOICES, "fr_fr")) == 1
    assert L.voices_for_language(VOICES, "xx-YY") == []


def test_default_language():
    assert L.default_language_for(VOICES, "en-CA-ClaraNeural") == "en-CA"
    assert L.default_language_for([], "fr-FR-DeniseNeural") == "fr-FR"
    assert L.default_language_for([], "iu-Latn-CA-SiqiniqNeural") == "iu-Latn-CA"
    assert L.default_language_for([], "weird") == "en-US"


def test_choose_voice():
    default = "en-US-AriaNeural"
    assert L.choose_voice(VOICES, "fr-FR", "en-CA-LiamNeural", default) == "en-CA-LiamNeural"
    assert L.choose_voice(VOICES, "en-US", None, default) == default
    assert L.choose_voice(VOICES, "fr-FR", None, default) == "fr-FR-DeniseNeural"
    assert L.choose_voice(VOICES, "en-AU", None, default) == "en-AU-WilliamMultilingualNeural"
    assert L.choose_voice(VOICES, "xx-YY", None, default) == default
    assert L.choose_voice(VOICES, None, None, default) == default


class FakeCommunicate:
    calls = []
    chunks = [
        {"type": "audio", "data": b"ab"},
        {"type": "WordBoundary", "offset": 1},
        {"type": "audio", "data": b"cd"},
    ]
    error = None

    def __init__(self, text, voice, **kwargs):
        FakeCommunicate.calls.append((text, voice, kwargs))

    async def stream(self):
        for chunk in FakeCommunicate.chunks:
            if FakeCommunicate.error:
                raise FakeCommunicate.error
            yield chunk


@pytest.fixture(autouse=True)
def reset_fake():
    FakeCommunicate.calls = []
    FakeCommunicate.error = None
    FakeCommunicate.chunks = [
        {"type": "audio", "data": b"ab"},
        {"type": "WordBoundary", "offset": 1},
        {"type": "audio", "data": b"cd"},
    ]


def test_synthesize_collects_audio():
    audio = asyncio.run(
        E.synthesize("hi", "en-US-AriaNeural", "+10%", "+0Hz", "+0%", communicate_cls=FakeCommunicate)
    )
    assert audio == b"abcd"
    assert FakeCommunicate.calls == [
        ("hi", "en-US-AriaNeural", {"rate": "+10%", "pitch": "+0Hz", "volume": "+0%"})
    ]


def test_synthesize_network_failure():
    FakeCommunicate.error = OSError("no route")
    with pytest.raises(E.EdgeTTSError, match="no route"):
        asyncio.run(E.synthesize("hi", "v", "+0%", "+0Hz", "+0%", communicate_cls=FakeCommunicate))


def test_synthesize_no_audio():
    FakeCommunicate.chunks = [{"type": "WordBoundary"}]
    with pytest.raises(E.EdgeTTSError, match="no audio"):
        asyncio.run(E.synthesize("hi", "v", "+0%", "+0Hz", "+0%", communicate_cls=FakeCommunicate))


def test_voice_cache_refreshes_once_a_day():
    now = [0.0]
    fetches = []

    async def fetcher():
        fetches.append(now[0])
        return list(VOICES)

    cache = E.VoiceCache(fetcher, max_age=100, clock=lambda: now[0])

    async def run():
        await cache.async_get()
        now[0] = 50
        await cache.async_get()
        assert len(fetches) == 1
        now[0] = 150
        await cache.async_get()
        assert len(fetches) == 2

    asyncio.run(run())


def test_voice_cache_failure_paths():
    now = [0.0]
    state = {"fail": True}

    async def fetcher():
        if state["fail"]:
            raise OSError("down")
        return list(VOICES)

    cache = E.VoiceCache(fetcher, max_age=10, clock=lambda: now[0])

    async def run():
        with pytest.raises(E.EdgeTTSError):
            await cache.async_get()
        state["fail"] = False
        assert len(await cache.async_get()) == len(VOICES)
        state["fail"] = True
        now[0] = 100
        assert len(await cache.async_get()) == len(VOICES)  # keeps the last good list

    asyncio.run(run())
