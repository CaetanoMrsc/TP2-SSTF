#!/usr/bin/env python3

import json
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

# --- Alunos devem implementar as funções abaixo --- #

def get_datetime():
    with open("/proc/stat", "r") as file:
        for line in file:
            if line.startswith("btime "):
                boot_time = int(line.split()[1])
                break

    with open("/proc/uptime", "r") as file:
        uptime_seconds = float(file.readline().split()[0])

    current_timestamp = boot_time + uptime_seconds
    return datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%d %H:%M:%S")

def get_uptime():
    with open("/proc/uptime", "r") as file:
        return float(file.readline().split()[0])

def get_cpu_info():
    model = "Unknown"
    speed_mhz = 0.0

    with open("/proc/cpuinfo", "r") as file:
        for line in file:
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break

    with open("/proc/cpuinfo", "r") as file:
        for line in file:
            if line.startswith("cpu MHz"):
                speed_mhz = float(line.split(":", 1)[1].strip())
                break

    def read_cpu_stats():
        with open("/proc/stat", "r") as file:
            fields = file.readline().split()[1:]
            values = [int(value) for value in fields]
            idle = values[3] + values[4]
            total = sum(values)
            return total, idle

    total_1, idle_1 = read_cpu_stats()
    time.sleep(0.1)
    total_2, idle_2 = read_cpu_stats()

    total_delta = total_2 - total_1
    idle_delta = idle_2 - idle_1

    if total_delta > 0:
        usage_percent = (total_delta - idle_delta) / total_delta * 100
    else:
        usage_percent = 0.0

    return {
        "model": model,
        "speed_mhz": speed_mhz,
        "usage_percent": round(usage_percent, 2)
    }

def get_memory_info():
    total_kb = 0
    available_kb = 0

    with open("/proc/meminfo", "r") as file:
        for line in file:
            if line.startswith("MemTotal:"):
                total_kb = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                available_kb = int(line.split()[1])

    total_mb = total_kb // 1024
    used_mb = (total_kb - available_kb) // 1024

    return {
        "total_mb": total_mb,
        "used_mb": used_mb
    }

def get_os_version():
    with open("/proc/version", "r") as file:
        return file.readline().strip()

def get_process_list():
    processes = []

    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue

        pid = int(entry)

        try:
            with open(f"/proc/{pid}/comm", "r") as file:
                name = file.readline().strip()
        except (FileNotFoundError, PermissionError):
            continue

        processes.append({
            "pid": pid,
            "name": name
        })

    return processes

def get_disks():
    disks = []

    for device in os.listdir("/sys/block"):
        size_path = f"/sys/block/{device}/size"

        try:
            with open(size_path, "r") as file:
                sectors = int(file.readline().strip())
        except (FileNotFoundError, ValueError):
            continue

        size_mb = (sectors * 512) // (1024 * 1024)

        disks.append({
            "device": f"/dev/{device}",
            "size_mb": size_mb
        })

    return disks

def get_usb_devices():
    devices = []
    usb_path = "/sys/bus/usb/devices"

    if not os.path.isdir(usb_path):
        return devices

    for device in os.listdir(usb_path):
        device_path = os.path.join(usb_path, device)

        if not os.path.isdir(device_path):
            continue

        if ":" in device:
            continue

        product_path = os.path.join(device_path, "product")

        try:
            with open(product_path, "r") as file:
                description = file.readline().strip()
        except (FileNotFoundError, PermissionError):
            continue

        devices.append({
            "port": device,
            "description": description
        })

    return devices

def get_network_adapters():
    adapters = []
    interfaces = os.listdir("/sys/class/net")

    local_ips = []

    with open("/proc/net/fib_trie", "r") as file:
        current_ip = None

        for line in file:
            line = line.strip()

            if line.startswith("|-- "):
                current_ip = line[4:].strip()

            elif line == "/32 host LOCAL" and current_ip:
                local_ips.append(current_ip)
                current_ip = None

    routes = {}

    with open("/proc/net/route", "r") as file:
        next(file)

        for line in file:
            fields = line.split()

            if len(fields) < 8:
                continue

            interface = fields[0]
            destination = fields[1]
            mask = fields[7]

            if destination == "00000000":
                continue

            destination_value = int(destination, 16)
            mask_value = int(mask, 16)

            routes.setdefault(interface, []).append(
                (destination_value, mask_value)
            )

    for interface in interfaces:
        if interface == "lo":
            adapters.append({
                "interface": "lo",
                "ip_address": "127.0.0.1"
            })
            continue

        for ip in local_ips:
            parts = ip.split(".")

            if len(parts) != 4:
                continue

            ip_value = sum(
                int(parts[i]) << (8 * i)
                for i in range(4)
            )

            for destination_value, mask_value in routes.get(interface, []):
                if (ip_value & mask_value) == (destination_value & mask_value):
                    adapters.append({
                        "interface": interface,
                        "ip_address": ip
                    })
                    break

            if any(
                adapter["interface"] == interface
                for adapter in adapters
            ):
                break

    return adapters

# --- Servidor HTTP --- #

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/status":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        response = {
            "datetime": get_datetime(),
            "uptime_seconds": get_uptime(),
            "cpu": get_cpu_info(),
            "memory": get_memory_info(),
            "os_version": get_os_version(),
            "processes": get_process_list(),
            "disks": get_disks(),
            "usb_devices": get_usb_devices(),
            "network_adapters": get_network_adapters()
        }

        data = json.dumps(response, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

def run_server(port=8080):
    print(f"Servidor disponível em http://0.0.0.0:{port}/status")
    server = HTTPServer(("0.0.0.0", port), StatusHandler)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
