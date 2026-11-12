# MQTT and IoT MQTT Panel

[Português](MQTT_PANEL_SETUP_PT.md) | [English](MQTT_PANEL_SETUP_EN.md)

This guide connects Blanky to the Mosquitto broker and configures a mobile phone in IoT MQTT Panel. Every MQTT command is subject to the same safety rules as local controls.

## 1. Prepare the Mosquitto broker

On the Raspberry Pi:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
```

By default, Blanky uses:

| Field | Value |
| --- | --- |
| Broker on the Raspberry Pi | `localhost` |
| Port | `1883` |
| Topic prefix | `blanky` |

On the phone, `localhost` does not refer to the Raspberry Pi. Use the Raspberry Pi's local network IP address, for example `192.168.1.50`, and port `1883`.

You can change the broker address, port and prefix in `Settings` > `Communications and AI`. MQTT reconnects automatically after changes.

## 2. Command topics

### Action buttons

Configure each as a button in IoT MQTT Panel. Send payload `1`.

| Action | Topic |
| --- | --- |
| Start | `blanky/mqtt_start` |
| Stop | `blanky/mqtt_stop` |
| Fast mode | `blanky/mqtt_mode_fast` |
| Ideal mode | `blanky/mqtt_mode_ideal` |
| Manual mode | `blanky/mqtt_mode_manual` |
| Change mode | `blanky/mqtt_mode_change` |
| Robot to metal | `blanky/mqtt_robot_to_metal` |
| Robot to non-metal | `blanky/mqtt_robot_to_nonmetal` |

### Level switches

Configure each item as a switch. Payload `1` turns on/extends, and `0` turns off/retracts.

| Component | Topic | `1` | `0` |
| --- | --- | --- | --- |
| Motor 1 | `blanky/mqtt_motor_1` | Turn on | Turn off |
| Motor 2 | `blanky/mqtt_motor_2` | Turn on | Turn off |
| Motor 3 | `blanky/mqtt_motor_3` | Turn on | Turn off |
| Cylinder A | `blanky/mqtt_cyl_a` | Extend | Retract |
| Cylinder B | `blanky/mqtt_cyl_b` | Extend | Retract |
| Cylinder C | `blanky/mqtt_cyl_c` | Extend | Retract |
| Cylinder D | `blanky/mqtt_cyl_d` | Extend | Retract |
| Green light | `blanky/mqtt_green` | Turn on | Turn off |
| Red light | `blanky/mqtt_red` | Turn on | Turn off |

`on`, `true`, `high` and `pulse` are also accepted to turn on; `off`, `false` and `low` turn off.

## 3. Safe operating sequence

1. Send `mqtt_start`.
2. Select a mode: fast, ideal or manual.
3. Before controlling individual components, select manual mode.
4. To change mode, send `mqtt_mode_change`, then select the new mode.
5. Use `mqtt_stop` to stop and reset the system.

If a request does not follow this sequence, Blanky publishes a rejected event and does not send the action to the PLC.

## 4. Phone monitoring

The following state topics use `retain=true`, so they show the latest state immediately when the panel connects:

```text
blanky/state/start
blanky/state/mode_fast
blanky/state/mode_ideal
blanky/state/mode_manual
blanky/state/mode_change
blanky/state/motor_1 ... blanky/state/motor_3
blanky/state/cyl_a ... blanky/state/cyl_d
blanky/state/light_green
blanky/state/light_red
blanky/state/robot_metal
blanky/state/robot_nonmetal
```

These legacy topics remain available for existing switches and indicators. For a **read-only** dashboard, Blanky now also publishes `blanky/monitor/*`. Never configure a monitoring widget to publish to `monitor/*` or to send commands through `mqtt_*`.

### Recommended IoT MQTT Panel layout

Set the dashboard prefix to `blanky` and enter only the suffix below in Topic, for example `state/start`. Alternatively, enter `blanky/state/start` and check **Disable dashboard prefix topic**. Do not combine a dashboard prefix with a full topic path, which could subscribe to `blanky/blanky/state/start`.

| Group | Widget | Topic (with dashboard prefix `blanky`) | Setup |
| --- | --- | --- | --- |
| Availability | Multi-State Indicator | `monitor/availability` | `online` = Blanky available; `offline` = Blanky unavailable. Subscribe-only widget, without a sync request. |
| System | LED Indicator | `state/start` | Payload on `1`, off `0`; fixed panel name `System`. The LED does not change its name dynamically. |
| System | Text Output | `monitor/en/system` | Displays `Started` or `Stopped`; place next to the LED. |
| Current mode | Multi-State Indicator | `monitor/mode` | `stopped` = Stopped; `choose_mode` = Choose mode; `fast` = Fast; `ideal` = Ideal; `manual` = Manual; `changing` = Choose new mode. |
| Current mode | Text Output (alternative) | `monitor/en/mode` | Readable text if Multi-State cannot show labels. |
| Motors | LED Indicator + Text Output | `state/motor_1` + `monitor/en/motor_1` (also `_2`, `_3`) | `0` = Off; `1` = On. |
| Cylinders | LED Indicator + Text Output | `state/cyl_a` + `monitor/en/cyl_a` (also `_b`, `_c`, `_d`) | `0` = Retract requested; `1` = Extend requested. Not a measured position. |
| Lights | LED Indicator + Text Output | `state/light_green` + `monitor/en/light_green` (also `light_red`) | `0` = Off; `1` = On. |
| Robot | Text Output | `monitor/en/robot` | No active target, Target: metal pieces or Target: non-metal pieces. The selection is temporary. |
| Communications | Multi-State Indicator | `monitor/opcua` | `connected` / `disconnected`: OPC UA connection, not actuator confirmation. |
| Communications | Text Output | `monitor/en/opcua_feedback` | `Active` or `Unavailable`: OPC UA feedback reception. |
| OPC UA timings | Text Output | `monitor/en/opcua_write_time`, `monitor/en/opcua_ack_time` | Latest write and PLC signal acknowledgement in ms; unavailable values use text. These are not MQTT timings. |
| Latest activity | Text Output | `monitor/en/last_message` | Latest readable response or refusal; not a full event history. |

Portuguese equivalents are available under `monitor/pt/...`. All `monitor/*` topics are retained once first published. Use text, symbols and position in addition to color; do not rely only on red/green for critical states. **Do not use Node Status** with `monitor/availability`: the app version that requires a `Payload sync request` publishes a request, but Blanky does not implement that request/response protocol. Never publish to this topic, as doing so may overwrite its retained value. A subscribe-only Multi-State Indicator shows **Blanky's presence on the broker**, not that the system has started or that the PLC is connected. A clean exit publishes `offline`, and the Last Will publishes it after an unexpected disconnect; the broker may take some time to detect a lost connection. Disregard retained state values while availability is `offline`.

`state/*` and `monitor/*` represent Blanky's internal state. The OPC UA connection and feedback indicate communication; they **do not individually confirm the physical position of each actuator**. PLC sensor/receive data is not yet published as per-component physical state over MQTT.

For advanced diagnostics, the existing topics remain available:

| Topic | Content |
| --- | --- |
| `blanky/events/last_command` | Latest command and origin, as JSON |
| `blanky/events/rejected` | Rejected command and reason, as JSON |

The `MQTT Phone` card in Blanky's interface shows activity for 30 seconds after receiving a valid message. `events/last_command` contains the latest attempt even if rejected; `events/rejected` is not a substitute for the accessible `monitor/en/last_message`.

### Text-Bot on the phone

IoT MQTT Panel can send complete phrases rather than only button codes. Add a **Text Input** for each mode you want to use:

| Widget | Publish topic (with dashboard prefix `blanky`) | Behavior |
| --- | --- | --- |
| Text Input: Text-Bot Online | `textbot/online` | AI interprets natural language; if unavailable, it falls back to the Offline parser. |
| Text Input: Text-Bot Offline | `textbot/offline` | Uses local phrase variants directly, without AI. |
| Text Output: Response | `monitor/en/phone_textbot_response` | Shows only the latest response to a phone text request. |
| Text Output: Route used | `monitor/en/phone_textbot_path` | Online, Offline or Online-to-Offline fallback. |

In Text Input, publish **plain text**, with JSON off, `retain` **off** and QoS `0`. The topic selects the mode; interpretation uses Blanky's active UI language. Separate multiple requests with semicolons, for example `start; manual mode; turn on motor 1`. Retained input messages are never executed, even if saved by mistake. Messages are limited to 1000 characters.

The phone Text-Bot follows the same safety rules, Events and TTS flow as the local Text-Bot; audio plays on the Raspberry Pi, **not on the phone speaker**. Events identify the source as `PHONE`, just like the app buttons. The phone response has its own topic so voice and button activity does not overwrite it. Protect the broker: an accepted phrase can operate real actuators.

## 5. Test the connection

On the Raspberry Pi, open two terminals:

```bash
mosquitto_sub -h localhost -v -t 'blanky/#'
```

In the other terminal, send a command:

```bash
mosquitto_pub -h localhost -t blanky/mqtt_start -m 1
```

You should see the command in Blanky Events and in `blanky/events/last_command` and `blanky/state/*` topics.
To inspect only the new presentation topics, run `mosquitto_sub -h localhost -v -t 'blanky/monitor/#'`.
To test phone Text-Bot without operating the machine, run `mosquitto_pub -h localhost -t blanky/textbot/offline -m 'hello'`. An unrecognized-request response should appear in `blanky/monitor/en/phone_textbot_response` and Events, without sending a command to the PLC. Only then test operational commands under safe conditions.

## 6. Common issues

- `MQTT Base` offline: confirm the Mosquitto service is active and the host/port in Settings match the broker.
- `MQTT Phone` inactive: confirm the Raspberry Pi IP address, the `blanky` prefix and that the phone is on the same network.
- Command rejected: confirm the safety sequence and active mode before controlling individual components.
- No state updates: subscribe to `blanky/state/#` and confirm the panel prefix matches Blanky's configured prefix.

For installations outside a controlled local network, enable Mosquitto authentication and protect network access before exposing the MQTT port.
