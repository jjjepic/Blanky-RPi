# Atalho do Blanky no Raspberry Pi

[Português](README_PT.md) | [English](README.md)

Esta pasta cria um atalho de ambiente de trabalho para o Blanky sem guardar segredos no projeto.

## Iniciar pelo terminal

Na pasta do projeto, ative o ambiente virtual e inicie normalmente. A aplicação lê automaticamente `~/.blanky/openai.env`, se esse ficheiro existir.

```bash
cd /home/jorge/Blanky20
source venv/bin/activate
python main.py
```

Não é necessário usar `export OPENAI_API_KEY=...`. Sem chave, o Blanky continua a abrir e mantém os controlos diretos, MQTT e Text-Bot Offline disponíveis.

## Configurar a chave sem atalho

Se o atalho ainda não estiver instalado, crie uma vez o ficheiro privado local:

```bash
mkdir -p ~/.blanky
nano ~/.blanky/openai.env
chmod 600 ~/.blanky/openai.env
```

O ficheiro deve conter apenas:

```bash
OPENAI_API_KEY="a_sua_chave_aqui"
```

## Instalar o atalho de ambiente de trabalho

No Raspberry Pi, a partir da pasta do Blanky:

```bash
chmod +x raspberrypi/install_desktop_shortcut.sh
./raspberrypi/install_desktop_shortcut.sh
```

Depois, adicione a chave OpenAI uma vez em:

```bash
nano ~/.blanky/openai.env
```

Use este formato:

```bash
OPENAI_API_KEY="a_sua_chave_aqui"
```

Proteja o ficheiro depois de o criar:

```bash
chmod 600 ~/.blanky/openai.env
```

O launcher identifica automaticamente a pasta onde está instalado e inicia `main.py`. Mesmo sem chave, abre o Blanky com as funcionalidades Online indisponíveis; os botões diretos, MQTT e Text-Bot Offline continuam disponíveis.

Para usar outra pasta ou ficheiro de entrada, inicie o launcher com as variáveis `BLANKY_DIR` e `BLANKY_MAIN` alteradas.
