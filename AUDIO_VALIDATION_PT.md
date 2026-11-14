# Validação do áudio coordenado no Raspberry Pi

Esta lista complementa os testes automáticos sem hardware. Faz os testes com a maquete em estado seguro e confirma os comandos no registo de Eventos e no PLC; a fala **não** é prova de posição física.

1. Inicia o Blanky com microfone e saída de áudio. Envia três comandos de botão em menos de um segundo. Confirma que os três Eventos aparecem logo, que o PLC recebe os comandos e que a confirmação falada é agrupada sem repetir estados antigos.
2. Envia `Motor 1 ligado`, seguido imediatamente de `Motor 1 desligado`. Na fala agrupada deve prevalecer o último pedido; ambos os Eventos devem permanecer no registo.
3. Durante uma resposta longa, inicia uma gravação. A fala anterior deve parar antes do beep e da captura; não pode surgir uma resposta antiga depois da gravação. Faz também um pedido por voz durante uma confirmação MQTT.
4. Enquanto uma confirmação está a tocar, envia outra ação pelo IoT MQTT Panel e uma pergunta pelo Text-Bot. A pergunta solicitada tem prioridade; as confirmações operacionais posteriores não devem cortar repetidamente a resposta em curso.
5. Com uma gravação ativa, provoca uma recusa de segurança por botão ou telemóvel. O aviso deve permanecer visível em Eventos e ser falado depois da captura, sem se misturar com confirmações normais.
6. Seleciona outra voz, velocidade e idioma; usa **Repetir resposta** após uma resposta efetivamente iniciada. Confirma que a nova reprodução usa essas definições e o texto no idioma atual. Uma resposta cancelada antes da reprodução não deve tornar-se a última resposta.
7. Simula lentidão na OpenAI/TTS. Verifica que Text-Bot, botões, MQTT e OPC UA continuam a responder e que um WAV tardio não toca depois de uma nova gravação. Consulta o Diagnóstico de áudio para falhas de síntese.
8. Desliga voluntariamente a saída de áudio e volta a ligá-la. A interface e o PLC devem continuar a funcionar; o silêncio voluntário não deve surgir como avaria, e uma nova resposta deve conseguir tocar após a reativação. Se o dispositivo falhar com a saída ativa, o erro deve ficar visível e registado.
9. Desliga e religa o microfone USB. A captura seguinte deve redetetar o dispositivo uma vez. Se falhar, o erro deve ficar no diagnóstico sem bloquear as restantes formas de controlo.
10. Com retorno OPC UA ativo, compara uma confirmação de pedido aceite com a consulta posterior ao estado. A fala não deve anunciar uma posição física apenas por o comando ter sido aceite ou o sinal de receção ter sido visto.

Configuração opcional (segundos): `BLANKY_AUDIO_GROUP_WINDOW_SECONDS` (predefinição `0.30`, limite `0.05–1.0`) e `BLANKY_AUDIO_GROUP_MAX_WAIT_SECONDS` (predefinição `0.85`, limite `0.10–2.0`). `BLANKY_AUDIO_TTS_CACHE_ENTRIES` limita o número de áudios em memória (predefinição `8`, máximo `16`).
