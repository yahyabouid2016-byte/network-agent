import json
import logging
import time
from datetime import datetime
from pathlib import Path

from checks import *
from fixers import *
from ai_analyzer import AIAnalyzer, get_service_context

STATUS_FILE = Path("status.json")
EVENTS_FILE = Path("events.json")
AI_FILE = Path("ai_decision.json")


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_event(layer, msg, level="info"):
    events = []
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
    events.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "layer": layer,
        "level": level,
        "message": msg,
    })
    write_json(EVENTS_FILE, events[:50])


def ask_ai(ai, layer, issue, context):
    res = ai.analyze_issue(layer, issue, context)
    write_json(AI_FILE, res)
    add_event("AI", res.get("root_cause", ""), "info")
    return res


def main():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("agent.log"), logging.StreamHandler()],
    )
    logger = logging.getLogger("Agent")
    ai = AIAnalyzer(config["ai"]["api_key"], config["ai"]["model"]) if config["ai"]["enabled"] else None

    while True:
        status = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "agent": "running"}

        # 1. Services layer (Rule-based & AI)
        svc_cfg = config["layers"]["services"]
        svc_results = check_services_layer(svc_cfg["systemd"], svc_cfg["processes"])
        status["services"] = {}
        for name, res in svc_results.items():
            status["services"][name] = res["status"]
            if res["status"] != "ok":
                logger.warning(f"{name} down. Fixing...")
                if name in svc_cfg["systemd"]:
                    fixed = fix_systemd_service(name)
                else:
                    fixed = fix_process(name, f"/usr/sbin/{name} /etc/hostapd/hostapd.conf")
                if not fixed and ai:
                    logger.info("Rule-based failed. Asking AI...")
                    ai_res = ask_ai(ai, "services", f"{name} down", get_service_context(name))
                    if ai_res.get("safe_to_auto") and ai_res.get("confidence", 0) > 0.8:
                        logger.info("AI auto-fixing...")
                        fix_systemd_service(name)
                    else:
                        logger.warning(f"AI says: {ai_res.get('message')}")

        # 2. Link Layer
        link_cfg = config["layers"]["link"]
        status["link"] = {}
        for iface in link_cfg["interfaces"]:
            res = check_link_layer(iface)
            status["link"][iface] = res["status"]
            if res["status"] != "ok":
                logger.warning(f"Link {iface} down. Fixing...")
                fix_link(iface)

        # 3. Wi-Fi Layer
        wifi_cfg = config["layers"]["wifi"]
        status["wifi"] = {}
        for iface in wifi_cfg["interfaces"]:
            res = check_wifi_layer(iface, wifi_cfg["expected_mode"])
            status["wifi"][iface] = res["status"]
            if res["status"] != "ok":
                logger.warning(f"Wi-Fi {iface} issue. Fixing...")
                fix_wifi(iface)

        # 4. Network Layer
        net_cfg = config["layers"]["network"]
        status["network"] = {}
        for iface_cfg in net_cfg["interfaces"]:
            name = iface_cfg["name"]
            res = check_network_layer(name, iface_cfg["expected_ip"], iface_cfg["expected_prefix"], net_cfg["gateway"])
            status["network"][name] = {"status": res["status"], "ip": iface_cfg["expected_ip"]}
            if res["status"] != "ok":
                logger.warning(f"Network {name} issue. Fixing...")
                fix_network(name, iface_cfg["expected_ip"], iface_cfg["expected_prefix"])

        # 5. Connectivity Layer
        conn_cfg = config["layers"]["connectivity"]
        conn_res = check_connectivity_layer(conn_cfg["targets"], conn_cfg["dns_test"])
        status["connectivity"] = {"dns": conn_res["dns"]["status"]}
        for target, res in conn_res["ping"].items():
            status["connectivity"][target] = res["status"]
            if res["status"] != "ok":
                logger.warning(f"Connectivity to {target} failed. Fixing DNS...")
                fix_dns()

        write_json(STATUS_FILE, status)
        time.sleep(config["agent"]["interval"])


if __name__ == "__main__":
    main()