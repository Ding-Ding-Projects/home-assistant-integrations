"""Constants for the Edge TTS integration."""

DOMAIN = "edge_tts"

CONF_VOICE = "voice"
CONF_RATE = "rate"
CONF_PITCH = "pitch"
CONF_VOLUME = "volume"

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = 0
DEFAULT_PITCH = 0
DEFAULT_VOLUME = 0

RATE_RANGE = (-50, 100)
PITCH_RANGE = (-50, 50)
VOLUME_RANGE = (-50, 50)

VOICE_CACHE_SECONDS = 24 * 60 * 60
