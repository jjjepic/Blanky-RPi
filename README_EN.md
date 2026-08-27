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

Connection fields start locked. Use the pencil icon to unlock them, then apply your changes. MQTT reconnects automatically; a new OPC UA endpoint is used by the next command sent to the PLC.

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
