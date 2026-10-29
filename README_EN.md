# Blanky

[Português](README_PT.md) | [English](README_EN.md)

Blanky is an assistive interface for controlling a simulated industrial cell. It combines voice interaction, Text-Bot, direct buttons, MQTT and OPC UA, with safety rules enforced by a single validation point.

## Features

- Natural-language voice control.
- One or more Text-Bot commands.
- Direct controls for the system, modes, motors, cylinders, lights and robot.
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

Text-Bot starts in `Online` mode. AI interprets natural language and returns only permitted commands. If Online is unavailable, Blanky automatically changes to `Offline`, uses local recognition and reports this in the Response area.

`Offline` can also be selected manually. It accepts variants in the local command list and applies the same safety rules.

Voice recognition uses the Online flow to interpret natural phrases. Without the AI service, voice does not execute commands; direct controls, MQTT and Text-Bot Offline stay available.

## Settings

The gear button opens two areas:

- `Audio and Microphone`: profiles, capture, filters, manual adjustments and diagnostics.
- `Communications and AI`: automatic connection status, MQTT address, port, topic prefix, OPC UA endpoint and a temporary OpenAI key.

Connection fields start locked. Use the pencil icon to unlock them, then apply your changes. MQTT reconnects automatically; changing the OPC UA endpoint reconnects the persistent client to the new server.

## OPC UA: sending and receiving

Blanky uses `asyncua` to send the existing `ns=4` commands and observe all 25 return signals in the `OPC UA Receber` map (currently `ns=5`, identifiers `i=2` through `i=26`). The receive namespace index is resolved from the URI `http://OPC UA Receber`; set `BLANKY_OPCUA_RECEIVE_NAMESPACE_URI` if the PLC uses another URI. The connection stays active without commands, using subscriptions or periodic reads if subscriptions are unavailable.

Return signals are kept separate from the local operating state. Some are pulses or processing acknowledgements, not physical position feedback. In particular, the current C/D nodes indicate an advance command, not the magnetic sensors `S_C0`/`S_C1`/`S_D0`/`S_D1` (`%I2.0` through `%I2.3`). Their OPC UA node IDs must not be guessed; they still need to be exposed/mapped by the PLC. Once available, set `BLANKY_OPCUA_CYL_C_RETRACTED_NODE`, `BLANKY_OPCUA_CYL_C_ADVANCED_NODE`, `BLANKY_OPCUA_CYL_D_RETRACTED_NODE` and `BLANKY_OPCUA_CYL_D_ADVANCED_NODE` (values such as `ns=N;i=ID`). Without these variables, the sensors are not read. The C/D one-second actuation timer belongs in the PLC Maquete logic, not the Blanky OPC UA client.

The OPC UA card displays the most recent write or PLC-return-signal duration. A completed write means the OPC UA server responded; a return signal means Blanky observed that signal. Neither proves that the actuator reached its physical endpoint.

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

Read the complete Mosquitto and IoT MQTT Panel guide in [MQTT_PANEL_SETUP_EN.md](MQTT_PANEL_SETUP_EN.md). It covers command topics, state topics, mobile configuration and connection tests.

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
