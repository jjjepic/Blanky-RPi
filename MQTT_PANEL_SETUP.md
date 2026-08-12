# MQTT setup (Mosquitto + IoT MQTT Panel)

## 1) Broker

- Host: `localhost`
- Port: `1883`
- Prefixo base: `blanky`

## 2) Topicos de comando

### Comandos por pulso (1 -> 0 em 3s)

- `blanky/mqtt_start`
- `blanky/mqtt_stop`
- `blanky/mqtt_mode_fast`
- `blanky/mqtt_mode_ideal`
- `blanky/mqtt_mode_manual`
- `blanky/mqtt_mode_change`
- `blanky/mqtt_robot_to_metal`
- `blanky/mqtt_robot_to_nonmetal`

### Comandos por nivel (sem pulso, 1/0)

- `blanky/mqtt_motor_1`
- `blanky/mqtt_motor_2`
- `blanky/mqtt_motor_3`
- `blanky/mqtt_cyl_a`
- `blanky/mqtt_cyl_b`
- `blanky/mqtt_cyl_c`
- `blanky/mqtt_cyl_d`
- `blanky/mqtt_green`
- `blanky/mqtt_red`

Regras dos topicos por nivel:

- Payload `1` -> ativa (ON/EXTEND)
- Payload `0` -> desativa (OFF/RETRACT)

Payloads aceites:

- ON: `1`, `on`, `true`, `high`, `pulse`
- OFF: `0`, `off`, `false`, `low`

## 3) Estados e eventos

Estados (`retain=true`):

- `blanky/state/start`
- `blanky/state/mode_fast`
- `blanky/state/mode_ideal`
- `blanky/state/mode_manual`
- `blanky/state/mode_change`
- `blanky/state/motor_1`
- `blanky/state/motor_2`
- `blanky/state/motor_3`
- `blanky/state/cyl_a`
- `blanky/state/cyl_b`
- `blanky/state/cyl_c`
- `blanky/state/cyl_d`
- `blanky/state/light_green`
- `blanky/state/light_red`
- `blanky/state/robot_metal`
- `blanky/state/robot_nonmetal`

Eventos:

- `blanky/events/last_command` -> `{"command":"...","source":"voice|mqtt_panel"}`
- `blanky/events/rejected` -> `{"command":"...","reason":"start_is_0"}`

## 4) IoT MQTT Panel

Para switches (nivel):

- Topic: `blanky/mqtt_motor_1` (exemplo)
- ON payload: `1`
- OFF payload: `0`

Para botoes de pulso:

- Topic: ex. `blanky/mqtt_start`
- Payload: `1`

Monitorizacao:

- `blanky/state/*`
- `blanky/events/last_command`
