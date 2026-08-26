# Blanky Raspberry Pi Launcher

[Português](README_PT.md) | [English](README.md)

This folder creates a desktop shortcut for Blanky without storing secrets in the project.

## Start from the terminal

From the project folder, activate the virtual environment and launch normally. The application automatically reads `~/.blanky/openai.env` when that file exists.

```bash
cd /home/jorge/Blanky20
source venv/bin/activate
python main.py
```

No `export OPENAI_API_KEY=...` command is needed. Without a key, Blanky still opens and keeps direct controls, MQTT and Text-Bot Offline available.

## Configure the key without a shortcut

If the shortcut is not installed yet, create the private local file once:

```bash
mkdir -p ~/.blanky
nano ~/.blanky/openai.env
chmod 600 ~/.blanky/openai.env
```

The file must contain only:

```bash
OPENAI_API_KEY="your_key_here"
```

On the Raspberry Pi, from the Blanky folder:

```bash
chmod +x raspberrypi/install_desktop_shortcut.sh
./raspberrypi/install_desktop_shortcut.sh
```

Then add the OpenAI key once to:

```bash
nano ~/.blanky/openai.env
```

Use this format:

```bash
OPENAI_API_KEY="your_key_here"
```

Protect the file after creating it:

```bash
chmod 600 ~/.blanky/openai.env
```

O launcher identifica automaticamente a pasta onde está instalado e inicia `main.py`. Mesmo sem chave, abre o Blanky com as funcionalidades Online indisponíveis; os botões diretos, MQTT e Text-Bot Offline continuam disponíveis.

Para usar outra pasta ou ficheiro de entrada, inicie o launcher com as variáveis `BLANKY_DIR` e `BLANKY_MAIN` alteradas.
