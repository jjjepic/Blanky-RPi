# MQTT e IoT MQTT Panel

[Português](MQTT_PANEL_SETUP.md) | [English](MQTT_PANEL_SETUP_EN.md)

Este guia liga o Blanky ao broker Mosquitto e configura o telemóvel no IoT MQTT Panel. Todos os comandos recebidos por MQTT passam pelas mesmas regras de segurança dos controlos locais.

## 1. Preparar o broker Mosquitto

No Raspberry Pi:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
```

Por defeito, o Blanky usa:

| Campo | Valor |
| --- | --- |
| Broker no Raspberry Pi | `localhost` |
| Porta | `1883` |
| Prefixo de tópicos | `blanky` |

No telemóvel, `localhost` não aponta para o Raspberry Pi. Use o endereço IP do Raspberry Pi na rede local, por exemplo `192.168.1.50`, e a porta `1883`.

Pode alterar o endereço do broker, porta e prefixo em `Definições` > `Comunicações e IA`. As alterações MQTT reconectam o serviço automaticamente.

## 2. Tópicos de comando

### Botões de ação

Configure cada um como botão no IoT MQTT Panel. Envie o payload `1`.

| Ação | Tópico |
| --- | --- |
| Iniciar | `blanky/mqtt_start` |
| Parar | `blanky/mqtt_stop` |
| Modo rápido | `blanky/mqtt_mode_fast` |
| Modo ideal | `blanky/mqtt_mode_ideal` |
| Modo manual | `blanky/mqtt_mode_manual` |
| Trocar modo | `blanky/mqtt_mode_change` |
| Robô para metal | `blanky/mqtt_robot_to_metal` |
| Robô para não metal | `blanky/mqtt_robot_to_nonmetal` |

### Interruptores de nível

Configure cada um como switch. O payload `1` liga/avança e `0` desliga/recua.

| Componente | Tópico | `1` | `0` |
| --- | --- | --- | --- |
| Motor 1 | `blanky/mqtt_motor_1` | Ligar | Desligar |
| Motor 2 | `blanky/mqtt_motor_2` | Ligar | Desligar |
| Motor 3 | `blanky/mqtt_motor_3` | Ligar | Desligar |
| Cilindro A | `blanky/mqtt_cyl_a` | Avançar | Recuar |
| Cilindro B | `blanky/mqtt_cyl_b` | Avançar | Recuar |
| Cilindro C | `blanky/mqtt_cyl_c` | Avançar | Recuar |
| Cilindro D | `blanky/mqtt_cyl_d` | Avançar | Recuar |
| Luz verde | `blanky/mqtt_green` | Ligar | Desligar |
| Luz vermelha | `blanky/mqtt_red` | Ligar | Desligar |

Também são aceites `on`, `true`, `high` e `pulse` para ligar; `off`, `false` e `low` para desligar.

## 3. Sequência segura de utilização

1. Envie `mqtt_start`.
2. Escolha um modo: rápido, ideal ou manual.
3. Para componentes individuais, escolha primeiro o modo manual.
4. Para trocar de modo, envie `mqtt_mode_change` e escolha o novo modo.
5. Use `mqtt_stop` para parar e repor o sistema.

Se um pedido não cumprir esta sequência, o Blanky publica um evento de rejeição e não envia a ação ao PLC.

## 4. Monitorização no telemóvel

Os seguintes tópicos de estado usam `retain=true`, pelo que mostram o último estado logo que o painel se liga:

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

Adicione também widgets de texto para:

| Tópico | Conteúdo |
| --- | --- |
| `blanky/events/last_command` | Último comando e origem, em JSON |
| `blanky/events/rejected` | Comando rejeitado e motivo, em JSON |

O cartão `MQTT Telemóvel` na interface Blanky mostra atividade durante 30 segundos depois de receber uma mensagem válida.

## 5. Testar a ligação

No Raspberry Pi, abra dois terminais:

```bash
mosquitto_sub -h localhost -v -t 'blanky/#'
```

Noutro terminal, envie um comando:

```bash
mosquitto_pub -h localhost -t blanky/mqtt_start -m 1
```

Deve ver o comando nos Eventos do Blanky e nos tópicos `blanky/events/last_command` e `blanky/state/*`.

## 6. Problemas frequentes

- `MQTT Base` offline: confirme se o serviço Mosquitto está ativo e se o host/porta em Definições correspondem ao broker.
- `MQTT Telemóvel` sem atividade: confirme o IP do Raspberry Pi, o prefixo `blanky` e se o telemóvel está na mesma rede.
- Comando rejeitado: confirme a sequência de segurança e o modo ativo antes de controlar componentes individuais.
- Nenhuma atualização de estado: subscreva `blanky/state/#` e confirme que o prefixo no painel é o mesmo configurado no Blanky.

Para instalações fora de uma rede local controlada, ative autenticação no Mosquitto e proteja o acesso à rede antes de expor a porta MQTT.
