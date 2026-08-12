# Blanky Raspberry Pi Launcher

This folder creates a desktop shortcut for Blanky without storing secrets in the project.

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

Defaults:

```bash
BLANKY_DIR=/home/jorge/Blanky15
BLANKY_MAIN=main15.py
```

To use another folder/version, edit `raspberrypi/run_blanky.sh` or launch with those environment variables changed.
