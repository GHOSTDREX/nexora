"""
AgriNova Backend — SSRF guard for farmer-configured hardware addresses.

Farm.sensor_node_host / robot_host / camera_host are LAN addresses (mDNS
hostnames or IPs) a farmer types into Settings for their own ESP32 devices,
then the backend makes outbound HTTP requests to them (hardware_poller.py,
routers/robot.py, routers/camera.py). Because the target host is
user-controlled and the requests happen server-side, an authenticated user
could point one of these fields at something other than their own hardware —
most dangerously a cloud metadata endpoint (169.254.169.254) or back at the
backend's own loopback interface — to probe or exfiltrate from internal
infrastructure (classic SSRF).

Real ESP32 devices live at ordinary private LAN addresses (192.168.x.x,
10.x.x.x, mDNS .local names that resolve to those), so blocking all private
ranges would break the feature. Instead this blocks the specific ranges that
have no legitimate reason to ever be a farm's hardware host: loopback
(would point the request back at the backend itself) and link-local
(169.254.0.0/16 — which is exactly where cloud metadata services live).
Resolution happens fresh at call time (not just when the host was saved),
so this also defends against DNS rebinding.
"""

from __future__ import annotations

import ipaddress
import socket


def is_safe_hardware_host(host: str) -> bool:
    """True if `host` (a bare hostname/IP, no scheme, port stripped by caller
    or absent) is safe to make a server-side request to."""
    if not host:
        return False
    hostname = host.split(":")[0].strip()
    if not hostname:
        return False

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, UnicodeError):
        return False

    if not addr_infos:
        return False

    for info in addr_infos:
        raw_ip = info[4][0]
        try:
            ip = ipaddress.ip_address(raw_ip)
        except ValueError:
            return False
        if ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast:
            return False

    return True
