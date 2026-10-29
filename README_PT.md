# Blanky

[Português](README_PT.md) | [English](README_EN.md)

Blanky é uma interface assistiva para controlo de uma célula industrial simulada. Reúne interação por voz, Text-Bot, botões diretos, MQTT e OPC UA, mantendo as regras de segurança num único ponto de validação.

## O que permite fazer

- Controlar o sistema por voz em linguagem natural.
- Enviar um ou mais comandos pelo Text-Bot.
- Usar os controlos diretos para sistema, modos, motores, cilindros, luzes e robô.
- Receber comandos de um telemóvel através de MQTT.
- Encaminhar comandos validados para o PLC por OPC UA.
- Consultar Eventos, diagnóstico de áudio e exportar dados em CSV ou PDF.
- Adaptar a interface aos modos Escuro, Claro, Alto contraste, Daltonismo, Monocromático e Personalizado.

## Arranque rápido

No Raspberry Pi ou numa máquina com Python 3.10+:

```bash
cd /home/jorge/Blanky20
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Para o atalho de ambiente de trabalho no Raspberry Pi, consulte [raspberrypi/README_PT.md](raspberrypi/README_PT.md).

## Chave OpenAI

Não guarde a chave API no repositório, em capturas de ecrã ou em documentos partilhados. Pode defini-la:

- no Raspberry Pi, no ficheiro local `~/.blanky/openai.env` criado pelo launcher;
- durante a sessão, em `Definições` > `Comunicações e IA` > `OpenAI`.

Também pode definir `OPENAI_API_KEY` como variável de ambiente, mas já não é necessário para abrir a aplicação.

O campo da interface é mascarado e a chave introduzida aí fica apenas na sessão atual. Se uma chave tiver sido exposta, deve ser revogada e substituída no painel da OpenAI.

## Interação por texto e voz

O Text-Bot inicia em modo `Online`. Neste modo, a IA interpreta frases naturais e só devolve comandos permitidos. Se o serviço Online não estiver disponível, o Blanky muda automaticamente para `Offline`, usa o reconhecimento local e informa esse fallback na área Resposta.

O modo `Offline` também pode ser escolhido manualmente. Aceita as variantes previstas na lista local e continua a aplicar as mesmas regras de segurança.

O reconhecimento por voz utiliza o fluxo Online para interpretar frases naturais. Sem acesso ao serviço de IA, a voz não executa comandos; os controlos diretos, MQTT e Text-Bot Offline continuam disponíveis.

## Definições

O botão de engrenagem abre duas áreas independentes:

- `Áudio e Microfone`: perfis, captação, filtros, ajustes manuais e diagnóstico.
- `Comunicações e IA`: estado das ligações automáticas, endereço MQTT, porta, prefixo de tópicos, endpoint OPC UA e chave OpenAI temporária.

Os campos que podem alterar uma ligação começam bloqueados. Use o ícone de lápis para os desbloquear e aplique as alterações quando terminar. MQTT reconecta automaticamente; ao mudar o endereço OPC UA, a ligação persistente é restabelecida no novo servidor.

## OPC UA: envio e receção

O Blanky usa `asyncua` para enviar os comandos existentes do mapa `ns=4` e observar os 25 sinais de retorno do mapa `OPC UA Receber` (atualmente `ns=5`, identificadores `i=2` a `i=26`). O índice do espaço de nomes de receção é resolvido pelo URI `http://OPC UA Receber`; pode ser alterado com `BLANKY_OPCUA_RECEIVE_NAMESPACE_URI` se o PLC usar outro URI. A ligação é mantida mesmo sem comandos, com subscrição dos sinais e leitura periódica como alternativa quando a subscrição não está disponível.

Os sinais de retorno ficam separados do estado local da operação. Alguns são pulsos ou confirmações de processamento, não provas de posição física. Em particular, os nós atuais de C/D indicam o comando de avanço, não os sensores magnéticos `S_C0`/`S_C1`/`S_D0`/`S_D1` (`%I2.0` a `%I2.3`). Não se deve assumir os seus IDs OPC UA: ainda têm de ser publicados/mapeados no PLC. Quando existirem, podem ser indicados por `BLANKY_OPCUA_CYL_C_RETRACTED_NODE`, `BLANKY_OPCUA_CYL_C_ADVANCED_NODE`, `BLANKY_OPCUA_CYL_D_RETRACTED_NODE` e `BLANKY_OPCUA_CYL_D_ADVANCED_NODE` (valores no formato `ns=N;i=ID`). Sem estas variáveis, os sensores não são lidos. O temporizador de atuação de 1 segundo de C/D pertence à lógica do PLC Maquete, não ao cliente OPC UA do Blanky.

O cartão OPC UA mostra a última duração de escrita ou de chegada de um sinal de retorno. A escrita concluída significa resposta do servidor OPC UA; a chegada do sinal significa retorno observado no Blanky. Nenhuma das duas medidas confirma, por si só, o fim de curso físico.

### Comparar `opcua` com `asyncua`

Para comparar as duas bibliotecas no mesmo Raspberry Pi e servidor, instale também a dependência de desenvolvimento antiga e execute a medição **apenas de leitura**:

```bash
pip install -r requirements-dev.txt
python tools/benchmark_opcua.py --url opc.tcp://192.168.30.3:4840 --samples 30 --csv tempos_opcua.csv
```

O resultado contém tempos de ligação e amostras individuais de leitura (`read_ms`), com mediana e percentil 95. As amostras alternam a ordem das bibliotecas. Repita o ensaio com `--connect-first asyncua` para inverter também a ordem de ligação. Para medir escrita e retorno (`write_ms`, `return_ms`), use **exclusivamente nós de diagnóstico sem ligação a atuadores**, criados para o ensaio; o script recusa os nós de comando conhecidos do Blanky:

```bash
python tools/benchmark_opcua.py --url opc.tcp://192.168.30.3:4840 --write-node 'ns=5;i=100' --return-node 'ns=5;i=101' --allow-write --samples 30 --csv tempos_comandos.csv
```

Os IDs `i=100` e `i=101` são apenas exemplos; **não existem no mapa fornecido**. O nó de retorno deve começar em `FALSE`, passar a `TRUE` após a receção do teste e voltar a `FALSE` antes da amostra seguinte. Se o mesmo nó for usado para escrita e retorno, mede-se apenas a leitura de volta do servidor, não o percurso pelos PLCs. Registe também a versão das bibliotecas, a resolução do temporizador/intervalo de polling, a carga do Raspberry Pi e a rede utilizada. Não há resultados do PLC real nesta branch.

## MQTT e telemóvel

O guia completo para Mosquitto e IoT MQTT Panel está em [MQTT_PANEL_SETUP_PT.md](MQTT_PANEL_SETUP_PT.md). Inclui tópicos de comando, tópicos de estado, configuração no telemóvel e testes de ligação.

## Estrutura do projeto

```text
blanky/       Lógica de comandos, áudio, MQTT, OPC UA e controlador QML
ui/           Interface QML e traduções PT/EN
assets/       Logótipos por modo visual
raspberrypi/  Launcher e atalho de ambiente de trabalho
exports/      Exportações geradas localmente, não versionadas
audio/        Áudio temporário gerado localmente, não versionado
```

## Segurança operacional

Todos os pedidos convergem para a mesma validação antes de produzir efeitos. Os Eventos mantêm a origem, o comando canónico e o resultado `OK` ou `REJECT`; a interface principal privilegia mensagens claras para o utilizador.

O modo Manual é necessário para comandar componentes individuais. Ao trocar de modo, os componentes manuais são desligados de forma segura antes de o novo modo ser aceite.

## Validação de acessibilidade cromática

Os perfis Universal, Protan, Deutan e Tritan usam cores semânticas, símbolos e texto; não constituem um diagnóstico nem uma declaração de conformidade legal. Para verificar contrastes, pares de estados e a simulação Machado, instale as dependências de desenvolvimento e execute:

```bash
pip install -r requirements-dev.txt
python tools/validate_color_profiles.py
```

O resultado detalhado é gravado em `docs/color_profile_validation.md`.
