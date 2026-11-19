# Blanky

[Português](README_PT.md) | [English](README_EN.md)

Blanky is an assistive interface for controlling a simulated industrial cell. It combines voice interaction, Text-Bot, direct buttons, MQTT and OPC UA, with safety rules enforced by a single validation point.

## Features

- Natural-language voice control.
- One or more Text-Bot commands.
- Direct controls for the system, modes, motors, cylinders, lights and pickup requests.
- Mobile-phone commands through MQTT.
- Validated commands forwarded to the PLC through OPC UA.
- Events, audio diagnostics and CSV/PDF exports.
- Dark, Light, High Contrast, Colour Blind, Monochrome and Custom visual modes.

## Quick start

On a Raspberry Pi or a computer running Python 3.10+:

```bash
cd /home/jorge/Blanky20
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

For the Raspberry Pi desktop shortcut, see [raspberrypi/README_EN.md](raspberrypi/README_EN.md).

## OpenAI key

Never store an API key in the repository, screenshots or shared documents. Configure it either in the local Raspberry Pi file `~/.blanky/openai.env`, or for the current session in `Settings` > `Communications and AI` > `OpenAI`.

`OPENAI_API_KEY` can also be set as an environment variable, but it is not required to open the application. A key entered in the interface is masked and is kept only for the current session. Revoke and replace any key that has been exposed.

## Text and voice interaction

Text-Bot starts in `Online` mode. AI interprets natural language and returns only permitted commands or validated status questions. If Online is unavailable, Blanky automatically changes to `Offline`, uses local recognition and reports this in the Response area.

`Offline` can also be selected manually. It accepts variants in the local command list and applies the same safety rules.

In Offline recognition, "advance cylinder A" selects the cylinder rather than starting the system; the Portuguese word "para" means stop only when used alone or at the start of a phrase. Rejections and no-change requests use natural PT/EN sentences shared by the Response area, Events and spoken reply, without internal command identifiers in the message text. Use the `Change mode` button before selecting another mode.

Voice recognition needs OpenAI to transcribe audio. If Online interpretation fails after transcription, it tries the Offline interpreter. Without the AI service for transcription, voice cannot handle requests; direct controls, MQTT and Text-Bot Offline stay available.

Speech now uses one coordinator: synthesis does not block the interface, a new recording interrupts stale speech before capture, and nearby button/phone confirmations can be grouped. Spoken acceptance confirms only that a **request was accepted**, never a physical position. Requested replies, critical warnings and operational confirmations have separate priorities. **Repeat answer** uses the last speech that actually started, with the current voice, speed and language. TTS/playback failures appear in Audio Diagnostics. See the [Raspberry Pi validation checklist (Portuguese)](AUDIO_VALIDATION_PT.md).

## Status questions

By voice or Text-Bot, Online or Offline, you can ask about the system, mode, motors, cylinders, lights, robot, MQTT, OPC UA, OpenAI, errors, last event and available actions. Examples: `How is the system?`, `Is cylinder A extended?`, `Tell me the status of OPC UA and OpenAI`, `What can I do now?` and `Repeat`. You can mix an action and a question, for example `Turn on motor 1 and tell me if MQTT is connected`.

You can also ask about groups: `Which motors are on?`, `Which cylinders are extended?`, `What is active?`. Ask `Which voice are you using?`, `What is the volume?` or `Which voices are available?` for preferences. Spoken answers are brief; the screen and Events retain the detail, including the source of component states and the limits of PLC feedback.

## Change settings by voice or Text-Bot

Try `Set the volume to 60`, `Increase the volume`, `Speak more slowly`, `Change the voice to Coral`, `Switch to light theme` or `Larger text`. You can also change language, color profile, audio profile, animations, display scale and Text-Bot Online/Offline mode. These preferences work even when the system is stopped, use the same limits as the interface controls, and are logged as `Setting`. They never send anything to the PLC. MQTT/OPC UA parameters and the OpenAI key can only be changed in the Settings menu.

Questions work while the system is stopped, are logged as `Query`, and never send commands to the PLC. In synchronized mode, displayed status comes from PLC-reported returns, never just the last accepted request. In test mode, answers explicitly identify local, unconfirmed state. Motors and lights reflect logical outputs; A/B use end-position sensors; C/D only confirm extension, not retraction. An OpenAI key alone does not guarantee service availability.

## Settings

The gear button opens two areas:

- `Audio and Microphone`: profiles, capture, filters, manual adjustments and diagnostics.
- `Communications and AI`: automatic connection status, MQTT address, port, topic prefix, OPC UA endpoint and a temporary OpenAI key.

In **Communications and AI**, the **Control mode** switch selects **Synchronized PLC** (the startup default, based on return signals) or **Local test** (immediate local state and response, even without a PLC). The header and Operation Panel identify the mode. **Warning:** test-mode commands are still sent to the PLC whenever OPC UA is connected, and existing MQTT command topics remain active; both may actuate the machine. Local state does not prove that this happened. Events and `state_quality/*` mark the state `local`, except a real PLC error signal, which remains visible and blocks commands. `monitor/control_mode` publishes `test` or `plc`. Turn off the switch to return to PLC state; pending requests must finish first. The mode is not persisted across restarts.

In test mode, C/D extension and robot pickup requests use a two-second local/MQTT pulse, after which the button becomes inactive so another request can be made. This **does not confirm physical retraction**. OPC UA keeps its normal 0.3-second pulse, and C/D still have no dedicated retract node. In synchronized mode, C/D without confirmed extension show `? Unknown`.

Connection fields start locked. Use the pencil icon to unlock them, then apply your changes. MQTT reconnects automatically; changing the OPC UA endpoint reconnects the persistent client to the new server.

In the Communications cards, `OpenAI` replaces only the `MQTT Base` display; the MQTT service remains active. The OpenAI card makes no probe requests: it reports an unconfigured key, standby, a request in progress or the last request result. Its time is the duration of the last STT, AI interpretation or TTS generation/download request, not total speech time or a permanent connection latency. After a voice request, the Microphone card displays the last recording duration, using the same capture value as the audio logs. `Connected` retains its previous meaning of initialized audio; it does not confirm that an analog microphone plug is inserted.

## OPC UA: sending and receiving

Blanky uses `asyncua` to send the existing `ns=4` commands and observe all 25 return signals in the `OPC UA Receber` map (currently `ns=5`, identifiers `i=2` through `i=26`). The receive namespace index is resolved from the URI `http://OPC UA Receber`; set `BLANKY_OPCUA_RECEIVE_NAMESPACE_URI` if the PLC uses another URI. The connection stays active without commands, using subscriptions or periodic reads if subscriptions are unavailable.

Commands travel Blanky → OPC UA write on PLC Send&Receive → DB100 → TSEND_C/TRCV_C → PLC Maquete. Returns travel back from the machine's DB4 through the 25 `OPC UA Receber` nodes. A complete initial read synchronizes the interface without fabricating events. Later PLC-reported changes update the interface even when triggered by the HMI or automatic cycle. Loss of OPC UA communication invalidates current values; reconnection establishes a fresh baseline before reporting changes.

The event history distinguishes accepted request, queueing, OPC UA write, observed state and timeout/error. An observed state is **not an individual ACK** and cannot prove that a specific request caused the change. A connected OPC UA server and active subscription cannot, without a separate heartbeat, prove that the TCP link between PLCs is fresh. Inconsistent complementary signals are unconfirmed, not invented `OFF` values. Motors and lights are logical outputs; A/B use extend/retract sensors; C/D DBX2.0/DBX2.1 now reflect advanced-position sensors `S_C1`/`S_D1`. `FALSE` for C/D does not prove retraction. No new sensor NodeIds are assumed.

Blanky can request C/D extension only in this version. Retraction through speech, Text-Bot, buttons or MQTT is rejected and never written to the PLC. Technical names `ROBOT_TO_METAL` and `ROBOT_TO_NONMETAL` remain for compatibility but mean manual pickup requests on Conveyors 2 and 3; no physical robot is operating. The PLC remains responsible for resetting C/D on leaving manual mode or entering STOP/error.

The OPC UA card displays the latest write or return-signal observation time. A completed write means the OPC UA server responded; an observed signal does not establish individual command causation. The 300 ms pulse remains a starting point, with a `FALSE` reset attempted after failures and queued stale requests discarded on reconnection. This does not guarantee that every pulse crosses TSEND_C while it is busy; such a guarantee needs an additional PLC-side acknowledgement protocol. See [the laboratory validation procedure](PLC_VALIDATION_PT.md).

Run hardware-free tests with `python -m unittest discover -s tests -q`. OPC UA integration tests require `asyncua`; simulated feedback, command and failure tests do not require a physical PLC.

### Comparing `opcua` and `asyncua`

To compare the two libraries on the same Raspberry Pi and server, install the legacy development dependency and run the **read-only** benchmark:

```bash
pip install -r requirements-dev.txt
python tools/benchmark_opcua.py --url opc.tcp://192.168.30.3:4840 --samples 30 --csv opcua_times.csv
```

This reports connection times and individual read samples (`read_ms`), median and 95th percentile. The clients alternate order. Repeat with `--connect-first asyncua` to reverse connection order as well. To include writes and returns (`write_ms`, `return_ms`), use **dedicated non-actuating diagnostic nodes only**; the script rejects Blanky's known actuator command nodes:

```bash
python tools/benchmark_opcua.py --url opc.tcp://192.168.30.3:4840 --write-node 'ns=5;i=100' --return-node 'ns=5;i=101' --allow-write --samples 30 --csv command_times.csv
```

The `i=100` and `i=101` IDs are examples only; **they are not present in the supplied map**. The return node must start `FALSE`, become `TRUE` after the test request, then reset to `FALSE` before the next sample. Reusing one node for both write and return measures only a server readback, not the complete PLC path. Record library versions, polling interval, Raspberry Pi load and network conditions with the dissertation results. This branch contains no measurements from the real PLC.

## MQTT and mobile phone

Read the complete Mosquitto and IoT MQTT Panel guide in [MQTT_PANEL_SETUP_EN.md](MQTT_PANEL_SETUP_EN.md). It covers command topics, state topics, read-only MQTT monitoring, phone Text-Bot with Online/Offline modes, mobile setup and connection tests.

## Project structure

```text
blanky/       Command logic, audio, MQTT, OPC UA and the QML controller
ui/           QML interface and PT/EN translations
assets/       Logos for each visual mode
raspberrypi/  Launcher and desktop shortcut
exports/      Locally generated exports, not versioned
audio/        Locally generated temporary audio, not versioned
```

## Operational safety

Every request reaches the same validation before producing effects. Events retain the origin, canonical command and `OK` or `REJECT` result, while the main interface prioritises clear messages for the user.

Manual mode is required to control individual components. When changing mode, manual components are switched off safely before the new mode is accepted.

## Colour vision accessibility validation

Universal, Protan, Deutan and Tritan profiles use semantic colours, symbols and text; they are not a diagnosis or a legal conformance claim. To verify contrast, state pairs and the Machado simulation, install the development dependencies and run:

```bash
pip install -r requirements-dev.txt
python tools/validate_color_profiles.py
```

The detailed result is written to `docs/color_profile_validation.md`.
