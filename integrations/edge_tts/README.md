# Edge TTS

Text to speech through Microsoft Edge's online read-aloud voices, with no account or key.

Edge TTS adds one text-to-speech entity, `tts.edge_tts`, backed by the [`edge-tts`](https://pypi.org/project/edge-tts/) library. It needs an internet connection each time it speaks, because the audio is generated online. The voice list is fetched when Home Assistant starts and refreshed once a day.

## Setup

1. Open Settings, Devices and services, Add integration, and choose **Edge TTS**.
2. Pick a default voice. Voices are listed by language, for example "English (Canada), Clara, Female". If the voice list cannot be loaded, an error is shown and you can continue with the default `en-US-AriaNeural`.

## Entities

- `tts.edge_tts`: the text-to-speech entity. Its supported languages are every locale in the voice list, and its default language is the locale of the chosen default voice. It accepts the options `voice`, `rate`, `pitch` and `volume`.

## Options

Open the integration and choose **Configure**.

- Default voice.
- Rate, from -50 to +100 percent.
- Pitch, from -50 to +50 Hz.
- Volume, from -50 to +50 percent.

Each text-to-speech call can override these. Values may be written as numbers or in the forms `+10%` and `10`, and a value outside its range is rejected with a clear error.

## Usage

Speak with the default voice:

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.kitchen
  message: "Dinner is ready."
```

Choose a voice and adjust the delivery for one call:

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.kitchen
  message: "Bonjour, le dîner est prêt."
  language: fr-FR
  options:
    voice: fr-FR-DeniseNeural
    rate: "+10%"
    pitch: "-5Hz"
    volume: "+20%"
```

If you give a `language` without a `voice`, the default voice is used when it speaks that language, otherwise the first voice for that language.

With Assist, open Settings, Voice assistants, choose your assistant, and select **Edge TTS** as the text-to-speech engine, then pick a language and voice.

## Notes

- The service is Microsoft's online read-aloud feature. It is not an official, supported API, so it can change or become unavailable. When it cannot be reached, calls fail with a clear error and the voice list keeps its last known values.
- Only the text you speak is sent to Microsoft.

## Install

Download `edge_tts-1.0.0.hapkg` from the latest release (or the button on the website), then
drag it onto the Marketplace page of home-assistant-material, or use **Install from a package
file**. Restart Home Assistant if asked, then add **Edge TTS** under Settings, Devices and services.
Installed copies update themselves from the release index unless you switch automatic updates off.
