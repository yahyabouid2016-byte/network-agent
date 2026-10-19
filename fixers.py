import subprocess
import time


def run_action(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True).returncode == 0


def fix_link(interface):
    run_action(f"ip link set {interface} up")
    time.sleep(1)
    return True


def fix_wifi(interface):
    run_action("pkill -9 hostapd")
    time.sleep(1)
    run_action(f"ip link set {interface} down")
    time.sleep(1)
    run_action(f"ip link set {interface} up")
    time.sleep(1)
    run_action("hostapd /etc/hostapd/hostapd.conf &")
    time.sleep(2)
    return True


def fix_network(interface, expected_ip, expected_prefix):
    run_action(f"ip addr flush dev {interface}")
    run_action(f"ip addr add {expected_ip}/{expected_prefix} dev {interface}")
    run_action(f"ip link set {interface} up")
    time.sleep(1)
    return True


def fix_systemd_service(service_name):
    run_action(f"systemctl restart {service_name}")
    time.sleep(2)
    return run_action(f"systemctl is-active {service_name}")


def fix_process(process_name, start_command):
    run_action(f"pkill -9 {process_name}")
    time.sleep(1)
    run_action(f"{start_command} &")
    time.sleep(2)
    return run_action(f"pgrep -x {process_name}")


def fix_dns():
    run_action("echo 'nameserver 8.8.8.8' > /etc/resolv.conf")
    run_action("echo 'nameserver 1.1.1.1' >> /etc/resolv.conf")
    run_action("systemctl restart dnsmasq")
    time.sleep(2)
    return True
