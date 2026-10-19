# Autonomous Network and Wi-Fi Troubleshooting Agent

An AI-assisted agent that monitors a (virtual) Wi-Fi access point lab, detects failures across several network layers, repairs them automatically with rule-based fixers, and falls back to an LLM (Groq) for root-cause analysis when the rules fail.

Note: this is a learning project. It was built and tested in a lab environment only (Debian VM with `mac80211_hwsim`). It is not a commercial product and has not had a security review.

## Features

- 5-layer monitoring model: link, Wi-Fi (AP mode), network (IP / gateway), services (dnsmasq, hostapd), connectivity (ping + DNS)
- Auto-repair: restarts services and processes, resets interfaces, re-applies IP configuration, fixes DNS
- LLM root-cause analysis (Groq): returns JSON with root cause, confidence score and `safe_to_auto`
- Safety gate: auto-fix only if `safe_to_auto` is true and confidence is above 0.8, otherwise it escalates to the administrator
- Flask dashboard: live service status and last AI decision (auto-refresh every 5 seconds)

## Project structure

```
network-agent/
  agent.py              Main monitoring loop
  checks.py             Per-layer health checks
  fixers.py             Rule-based repair actions
  ai_analyzer.py        Groq LLM root-cause analysis
  dashboard.py          Flask web dashboard
  config.json           Agent configuration (placeholders)
  templates/
    index.html          Dashboard page
  configs/
    hostapd.conf.example
    dnsmasq.conf.example
  docs/
    SETUP.md            VM / infrastructure setup
  requirements.txt
  CONTRIBUTING.md
  LICENSE
  README.md
```

## Quick start

1. Prepare the lab VM: follow [docs/SETUP.md](docs/SETUP.md)
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt --break-system-packages
   ```
3. Edit `config.json` and replace the placeholders:
   - `your ip addr`: your lab AP / gateway address
   - `your API key`: your Groq API key
   - `your model name`: a model available on your Groq account
4. Run (two terminals, root privileges are needed for the fixers):
   ```bash
   sudo python3 agent.py
   python3 dashboard.py
   ```
5. Open `http://your ip addr:5000` in your browser.

## Configuration

| Key | Description |
|---|---|
| `agent.interval` | Seconds between checks |
| `layers.*.enabled` | Enable or disable each layer |
| `layers.network.interfaces[].expected_ip` | Expected IP of the AP interface |
| `layers.services` | systemd services and processes to watch |
| `auto_fix.enabled` | Allow automatic repairs |
| `ai.enabled` | Use the LLM when rule-based fixes fail |
| `ai.api_key` / `ai.model` | Groq credentials and model |

Never commit your real API key. Keep it in a local file (`config.local.json` is git-ignored) or in an environment variable.

## How it works

```
check layers -> issue found -> rule-based fixer -> fixed?
                                                    |
                                      yes: done     |     no
                                                    v
                                           LLM analysis (Groq)
                                                    |
                                 safe_to_auto and confidence > 0.8 ?
                                      |                       |
                                     yes                      no
                                      |                       |
                                  auto-fix            escalate to admin
```

## Roadmap

- Wire the link, Wi-Fi, network and connectivity checks into `agent.py` (currently the main loop runs the services layer only)
- Event log view in the dashboard
- Retry limits (`auto_fix.max_retries`)
- Remote deployment (SSH / OpenWrt) after proper security testing

## License

MIT. See [LICENSE](LICENSE).
