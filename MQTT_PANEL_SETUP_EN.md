# MQTT and IoT MQTT Panel

[Português](MQTT_PANEL_SETUP.md) | [English](MQTT_PANEL_SETUP_EN.md)

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

Also add text widgets for:

| Topic | Content |
| --- | --- |
| `blanky/events/last_command` | Latest command and origin, as JSON |
| `blanky/events/rejected` | Rejected command and reason, as JSON |

The `MQTT Phone` card in Blanky's interface shows activity for 30 seconds after receiving a valid message.

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

## 6. Common issues

- `MQTT Base` offline: confirm the Mosquitto service is active and the host/port in Settings match the broker.
- `MQTT Phone` inactive: confirm the Raspberry Pi IP address, the `blanky` prefix and that the phone is on the same network.
- Command rejected: confirm the safety sequence and active mode before controlling individual components.
- No state updates: subscribe to `blanky/state/#` and confirm the panel prefix matches Blanky's configured prefix.

For installations outside a controlled local network, enable Mosquitto authentication and protect network access before exposing the MQTT port.
