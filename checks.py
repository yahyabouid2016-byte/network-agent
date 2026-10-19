import subprocess


def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def check_link_layer(interface):
    output = run_command(f"ip link show {interface}")
    if not output or ("state UP" not in output and "UP" not in output.split(":")[1]):
        return {"status": "error", "reason": "interface_down"}
    if "NO-CARRIER" in output:
        return {"status": "error", "reason": "no_carrier"}
    return {"status": "ok"}


def check_wifi_layer(interface, expected_mode="AP"):
    output = run_command(f"iw dev {interface} info")
    if f"type {expected_mode}" not in output:
        return {"status": "error", "reason": f"not_{expected_mode}"}
    return {"status": "ok"}


def check_network_layer(interface, expected_ip, expected_prefix, gateway):
    output = run_command(f"ip addr show {interface}")
    if "inet " not in output:
        return {"status": "error", "reason": "no_ip"}
    if "169.254." in output:
        return {"status": "error", "reason": "apipa"}
    if f"{expected_ip}/{expected_prefix}" not in output:
        return {"status": "error", "reason": "wrong_ip"}
    if "default via" not in run_command("ip route show"):
        return {"status": "error", "reason": "no_gateway"}
    return {"status": "ok"}


def check_services_layer(systemd_services, processes):
    results = {}
    for service in systemd_services:
        if run_command(f"systemctl is-active {service}") == "active":
            results[service] = {"status": "ok"}
        else:
            results[service] = {"status": "error", "reason": "service_down"}
    for process in processes:
        if run_command(f"pgrep -x {process}"):
            results[process] = {"status": "ok"}
        else:
            results[process] = {"status": "error", "reason": "process_down"}
    return results


def check_connectivity_layer(targets, dns_test):
    results = {"ping": {}, "dns": {"status": "ok"}}
    for target in targets:
        res = subprocess.run(["ping", "-c", "1", "-W", "2", target], capture_output=True)
        results["ping"][target] = {"status": "ok"} if res.returncode == 0 else {"status": "error"}
    out = subprocess.run(["nslookup", dns_test], capture_output=True, text=True).stdout
    if "Address" not in out:
        results["dns"] = {"status": "error", "reason": "dns_failed"}
    return results
