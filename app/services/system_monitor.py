import asyncio
import glob
import os
import shutil
import time
from typing import Any

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes, format_seconds
from app.services.docker_service import docker_service
from app.services.qbittorrent import qbittorrent_service
from app.services.rclone import rclone_service


class SystemMonitorService(BaseServiceClient):
    """Collects host hardware metrics, thermal sensors, GPU status, RAM, disk I/O, network, and live transfers."""

    def __init__(self) -> None:
        super().__init__(
            service_name="HomepageSysInfo",
            base_url=settings.HOMEPAGE_URL,
            timeout=8.0,
        )
        self._last_io_time: float = 0.0
        self._last_disk_read: int = 0
        self._last_disk_write: int = 0
        self._last_net_rx: int = 0
        self._last_net_tx: int = 0
        self._rclone_history: dict[str, list[tuple[float, int]]] = {}

    def _read_file_safe(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""

    def _read_raw_disk_bytes(self) -> tuple[int, int]:
        read_bytes = 0
        write_bytes = 0
        try:
            for dev in os.listdir("/sys/block"):
                if dev.startswith(("loop", "ram", "dm-")):
                    continue
                stat_raw = self._read_file_safe(f"/sys/block/{dev}/stat")
                if not stat_raw:
                    continue
                stat = stat_raw.split()
                if len(stat) > 6:
                    read_bytes += int(stat[2]) * 512
                    write_bytes += int(stat[6]) * 512
        except Exception:
            pass
        return read_bytes, write_bytes

    def _read_raw_net_bytes(self) -> tuple[int, int]:
        rx = 0
        tx = 0
        try:
            net_dev = self._read_file_safe("/proc/net/dev")
            lines = net_dev.splitlines()[2:]
            for line in lines:
                if ":" not in line:
                    continue
                iface, stats = line.split(":", 1)
                iface = iface.strip()
                if iface == "lo" or iface.startswith(("veth", "br-", "docker")):
                    continue
                parts = stats.split()
                if len(parts) > 8:
                    rx += int(parts[0])
                    tx += int(parts[8])
        except Exception:
            pass
        return rx, tx

    async def sample_io_rates(self) -> dict[str, Any]:
        """Computes live Disk Read/Write and Network RX/TX speeds in bytes/sec."""
        now = time.time()
        curr_d_read, curr_d_write = self._read_raw_disk_bytes()
        curr_rx, curr_tx = self._read_raw_net_bytes()

        dt = now - self._last_io_time
        if self._last_io_time == 0.0 or dt <= 0.05 or dt > 30.0:
            await asyncio.sleep(0.25)
            now2 = time.time()
            next_d_read, next_d_write = self._read_raw_disk_bytes()
            next_rx, next_tx = self._read_raw_net_bytes()
            dt = max(0.05, now2 - now)
            disk_r_speed = max(0.0, (next_d_read - curr_d_read) / dt)
            disk_w_speed = max(0.0, (next_d_write - curr_d_write) / dt)
            net_rx_speed = max(0.0, (next_rx - curr_rx) / dt)
            net_tx_speed = max(0.0, (next_tx - curr_tx) / dt)
            self._last_io_time = now2
            self._last_disk_read, self._last_disk_write = next_d_read, next_d_write
            self._last_net_rx, self._last_net_tx = next_rx, next_tx
        else:
            disk_r_speed = max(0.0, (curr_d_read - self._last_disk_read) / dt)
            disk_w_speed = max(0.0, (curr_d_write - self._last_disk_write) / dt)
            net_rx_speed = max(0.0, (curr_rx - self._last_net_rx) / dt)
            net_tx_speed = max(0.0, (curr_tx - self._last_net_tx) / dt)
            self._last_io_time = now
            self._last_disk_read, self._last_disk_write = curr_d_read, curr_d_write
            self._last_net_rx, self._last_net_tx = curr_rx, curr_tx

        return {
            "disk_read_bytes_sec": round(disk_r_speed, 1),
            "disk_write_bytes_sec": round(disk_w_speed, 1),
            "disk_read_speed": f"{format_bytes(disk_r_speed)}/s",
            "disk_write_speed": f"{format_bytes(disk_w_speed)}/s",
            "net_rx_bytes_sec": round(net_rx_speed, 1),
            "net_tx_bytes_sec": round(net_tx_speed, 1),
            "net_rx_speed": f"{format_bytes(net_rx_speed)}/s",
            "net_tx_speed": f"{format_bytes(net_tx_speed)}/s",
        }

    async def _sample_cpu_usage_percent(self, interval: float = 0.25) -> float:
        """Calculates real-time CPU usage percentage from /proc/stat over a short window."""
        def read_stat() -> tuple[int, int]:
            line = self._read_file_safe("/proc/stat").splitlines()[0]
            parts = [int(x) for x in line.split()[1:]]
            idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
            total = sum(parts)
            return idle, total

        try:
            idle_start, total_start = read_stat()
            await asyncio.sleep(interval)
            idle_end, total_end = read_stat()
            total_diff = total_end - total_start
            idle_diff = idle_end - idle_start
            if total_diff <= 0:
                return 0.0
            return round(100.0 * (1.0 - (idle_diff / total_diff)), 1)
        except Exception:
            return 0.0

    def get_cpu_details(self) -> dict[str, Any]:
        """Reads CPU model, core count, load average, and per-core MHz frequencies."""
        cpuinfo = self._read_file_safe("/proc/cpuinfo")
        model_name = "Unknown CPU"
        mhz_list: list[float] = []
        for line in cpuinfo.splitlines():
            if line.startswith("model name") and model_name == "Unknown CPU":
                model_name = line.split(":", 1)[1].strip()
            elif line.startswith("cpu MHz"):
                try:
                    mhz_list.append(round(float(line.split(":", 1)[1].strip()), 0))
                except ValueError:
                    pass

        loadavg_raw = self._read_file_safe("/proc/loadavg").split()
        load_avg = {
            "1m": float(loadavg_raw[0]) if len(loadavg_raw) > 0 else 0.0,
            "5m": float(loadavg_raw[1]) if len(loadavg_raw) > 1 else 0.0,
            "15m": float(loadavg_raw[2]) if len(loadavg_raw) > 2 else 0.0,
        }

        avg_freq_mhz = round(sum(mhz_list) / len(mhz_list), 0) if mhz_list else None
        max_core_mhz = max(mhz_list) if mhz_list else None
        min_core_mhz = min(mhz_list) if mhz_list else None

        return {
            "model": model_name,
            "logical_cores": len(mhz_list) or (os.cpu_count() or 1),
            "avg_frequency_mhz": avg_freq_mhz,
            "min_core_frequency_mhz": min_core_mhz,
            "max_core_frequency_mhz": max_core_mhz,
            "load_average": load_avg,
        }

    def get_memory_details(self) -> dict[str, Any]:
        """Reads detailed RAM and Swap metrics from /proc/meminfo."""
        meminfo_raw = self._read_file_safe("/proc/meminfo")
        info: dict[str, int] = {}
        for line in meminfo_raw.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                parts = val.strip().split()
                if parts and parts[0].isdigit():
                    info[key.strip()] = int(parts[0]) * 1024

        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", info.get("MemFree", 0))
        used = max(0, total - available)
        buffers = info.get("Buffers", 0)
        cached = info.get("Cached", 0)
        swap_total = info.get("SwapTotal", 0)
        swap_free = info.get("SwapFree", 0)
        swap_used = max(0, swap_total - swap_free)

        return {
            "ram_total": format_bytes(total),
            "ram_used": format_bytes(used),
            "ram_available": format_bytes(available),
            "ram_cached_buffers": format_bytes(buffers + cached),
            "ram_usage_percent": round((used / total) * 100.0, 1) if total > 0 else 0.0,
            "swap_total": format_bytes(swap_total),
            "swap_used": format_bytes(swap_used),
            "swap_free": format_bytes(swap_free),
            "swap_usage_percent": round((swap_used / swap_total) * 100.0, 1) if swap_total > 0 else 0.0,
        }

    def get_thermal_details(self) -> dict[str, Any]:
        """Reads hardware temperature sensors from /sys/class/thermal."""
        zones: list[dict[str, Any]] = []
        cpu_temp_c = None
        label_map = {
            "x86_pkg_temp": "CPU Package",
            "B0D4": "CPU Thermal Sensor (B0D4)",
            "acpitz": "Motherboard / ACPI",
            "pch_cannonlake": "Intel PCH Chipset",
            "iwlwifi_1": "Wi-Fi Adapter",
            "INT3400 Thermal": "System Ambient (INT3400)",
        }

        for z_path in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
            t_type = self._read_file_safe(f"{z_path}/type")
            t_raw = self._read_file_safe(f"{z_path}/temp")
            if not t_raw or not t_raw.lstrip("-").isdigit():
                continue
            temp_c = round(int(t_raw) / 1000.0, 1)
            if temp_c <= 1.0:
                continue
            friendly_name = label_map.get(t_type, t_type)
            zones.append(
                {
                    "sensor": friendly_name,
                    "raw_type": t_type,
                    "temperature_c": temp_c,
                }
            )
            if t_type == "x86_pkg_temp":
                cpu_temp_c = temp_c

        if cpu_temp_c is None and zones:
            cpu_temp_c = max(z["temperature_c"] for z in zones)

        return {
            "cpu_package_temp_c": cpu_temp_c,
            "sensors": zones,
        }

    def get_gpu_details(self) -> dict[str, Any]:
        """Reads Intel iGPU and NVIDIA dGPU status from /sys/class/drm and PCI sysfs."""
        gpus: list[dict[str, Any]] = []

        igpu_cur = self._read_file_safe("/sys/class/drm/card0/gt_cur_freq_mhz")
        igpu_max = self._read_file_safe("/sys/class/drm/card0/gt_max_freq_mhz")
        igpu_min = self._read_file_safe("/sys/class/drm/card0/gt_min_freq_mhz")
        if igpu_cur or igpu_max:
            cur_val = int(igpu_cur) if igpu_cur.isdigit() else 0
            max_val = int(igpu_max) if igpu_max.isdigit() else 0
            min_val = int(igpu_min) if igpu_min.isdigit() else 0
            freq_ratio = (
                round(((cur_val - min_val) / max(1, max_val - min_val)) * 100.0, 1)
                if max_val > min_val
                else 0.0
            )
            gpus.append(
                {
                    "name": "Intel UHD Graphics 620 (Integrated GPU)",
                    "device": "/dev/dri/card0 (VA-API / QuickSync Hardware Transcoding)",
                    "current_frequency_mhz": cur_val,
                    "min_frequency_mhz": min_val,
                    "max_frequency_mhz": max_val,
                    "frequency_scaling_percent": max(0.0, freq_ratio),
                }
            )

        nvidia_power_path = "/sys/bus/pci/devices/0000:02:00.0/power/runtime_status"
        nvidia_status = self._read_file_safe(nvidia_power_path)
        if nvidia_status or os.path.exists("/sys/class/drm/card1"):
            gpus.append(
                {
                    "name": "NVIDIA GeForce MX250 (Dedicated GPU - 2048 MiB VRAM)",
                    "device": "/dev/dri/card1 (PCI 0000:02:00.0)",
                    "power_state": nvidia_status or "present",
                }
            )

        return {"gpus": gpus}

    def get_power_and_uptime(self) -> dict[str, Any]:
        """Reads system uptime and power supply / battery state."""
        uptime_raw = self._read_file_safe("/proc/uptime").split()
        uptime_seconds = float(uptime_raw[0]) if uptime_raw else 0.0
        days, rem = divmod(int(uptime_seconds), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)

        ac_online = self._read_file_safe("/sys/class/power_supply/AC0/online")
        bat_status = self._read_file_safe("/sys/class/power_supply/BAT0/status")
        bat_cap = self._read_file_safe("/sys/class/power_supply/BAT0/capacity")

        power_info: dict[str, Any] = {}
        if ac_online:
            power_info["ac_mains_connected"] = ac_online == "1"
        if bat_status:
            power_info["battery_status"] = bat_status
        if bat_cap and bat_cap.isdigit():
            power_info["battery_capacity_percent"] = int(bat_cap)

        return {
            "uptime_formatted": f"{days}d {hours}h {minutes}m",
            "uptime_hours": round(uptime_seconds / 3600.0, 1),
            "power_supply": power_info,
        }

    def get_local_disk_usage(self) -> dict[str, Any]:
        """Reads root filesystem disk space."""
        try:
            usage = shutil.disk_usage("/")
            free_pct = round((usage.free / usage.total) * 100.0, 1) if usage.total > 0 else 0.0
            return {
                "mount": "/",
                "total": format_bytes(usage.total),
                "used": format_bytes(usage.used),
                "free": format_bytes(usage.free),
                "usage_percent": round((usage.used / usage.total) * 100.0, 1),
                "free_percent": free_pct,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _compute_sliding_speed(self, key: str, current_time: float, current_bytes: int) -> float:
        """Computes a 5-second sliding window transfer speed in bytes/sec (ported from server-monitor.py)."""
        hist = self._rclone_history.setdefault(key, [])
        hist.append((current_time, current_bytes))
        hist = [(t, b) for t, b in hist if current_time - t <= 5.0]
        self._rclone_history[key] = hist
        if len(hist) >= 2:
            oldest_t, oldest_b = hist[0]
            dt = current_time - oldest_t
            if dt > 0 and current_bytes >= oldest_b:
                return (current_bytes - oldest_b) / dt
        return 0.0

    async def get_live_transfers(self) -> dict[str, Any]:
        """Replaces server-monitor.py: live Disk I/O, Network I/O, qBittorrent active downloads & Rclone transfers."""
        now = time.time()

        async def _fetch_qb() -> dict[str, Any]:
            try:
                raw_torrents, raw_transfer = await asyncio.gather(
                    qbittorrent_service.request("GET", "/api/v2/torrents/info"),
                    qbittorrent_service.request("GET", "/api/v2/transfer/info"),
                )
                t_list = raw_torrents if isinstance(raw_torrents, list) else []
                t_info = raw_transfer if isinstance(raw_transfer, dict) else {}

                active_States = {
                    "downloading",
                    "metadl",
                    "forceddl",
                    "stalleddl",
                    "queueddl",
                    "checkingdl",
                    "uploading",
                    "forcedup",
                }
                formatted_active: list[dict[str, Any]] = []
                formatted_all: list[dict[str, Any]] = []

                for item in t_list:
                    progress_pct = round(float(item.get("progress", 0.0)) * 100.0, 1)
                    dl_spd = int(item.get("dlspeed", 0) or 0)
                    up_spd = int(item.get("upspeed", 0) or 0)
                    state_str = str(item.get("state", ""))
                    entry = {
                        "hash": item.get("hash"),
                        "name": item.get("name", "Unknown"),
                        "state": state_str,
                        "progress_percent": progress_pct,
                        "completed": format_bytes(item.get("completed", 0)),
                        "total_size": format_bytes(item.get("total_size") or item.get("size", 0)),
                        "dlspeed_bytes": dl_spd,
                        "upspeed_bytes": up_spd,
                        "dlspeed": f"{format_bytes(dl_spd)}/s",
                        "upspeed": f"{format_bytes(up_spd)}/s",
                        "eta": format_seconds(item.get("eta")),
                        "num_seeds": item.get("num_seeds", 0),
                        "num_leechs": item.get("num_leechs", 0),
                        "category": item.get("category", ""),
                    }
                    formatted_all.append(entry)
                    if state_str.lower() in active_States or dl_spd > 0 or up_spd > 0 or progress_pct < 100.0:
                        formatted_active.append(entry)

                dl_info_speed = int(t_info.get("dl_info_speed", 0) or 0)
                up_info_speed = int(t_info.get("up_info_speed", 0) or 0)
                return {
                    "online": True,
                    "dl_speed_bytes": dl_info_speed,
                    "ul_speed_bytes": up_info_speed,
                    "dl_speed": f"{format_bytes(dl_info_speed)}/s",
                    "ul_speed": f"{format_bytes(up_info_speed)}/s",
                    "free_space_on_disk": format_bytes(t_info.get("free_space_on_disk", 0)),
                    "active_count": len(formatted_active),
                    "total_count": len(formatted_all),
                    "active_torrents": formatted_active,
                    "all_torrents": formatted_all[:30],
                }
            except Exception as exc:
                return {
                    "online": False,
                    "error": str(exc),
                    "dl_speed": "0 B/s",
                    "ul_speed": "0 B/s",
                    "active_count": 0,
                    "total_count": 0,
                    "active_torrents": [],
                    "all_torrents": [],
                }

        async def _fetch_rclone() -> dict[str, Any]:
            try:
                core_stats, vfs_stats = await asyncio.gather(
                    rclone_service.request("POST", "/core/stats", json_data={}),
                    rclone_service.request("POST", "/vfs/stats", json_data={}),
                )
                c_data = core_stats if isinstance(core_stats, dict) else {}
                v_data = vfs_stats if isinstance(vfs_stats, dict) else {}

                global_bytes = int(c_data.get("bytes", 0) or 0)
                sliding_global = self._compute_sliding_speed("global", now, global_bytes)
                reported_speed = float(c_data.get("speed", 0.0) or 0.0)
                effective_global_speed = sliding_global if sliding_global > 0 else reported_speed

                raw_transferring = c_data.get("transferring") or []
                active_files: list[dict[str, Any]] = []
                for item in raw_transferring:
                    full_name = item.get("name", "Unknown")
                    short_name = full_name.split("/")[-1]
                    size_b = int(item.get("size", 0) or 0)
                    done_b = int(item.get("bytes", 0) or 0)
                    file_sliding = self._compute_sliding_speed(f"file:{short_name}", now, done_b)
                    file_reported = float(item.get("speed", 0.0) or 0.0)
                    eff_file_speed = file_sliding if file_sliding > 0 else file_reported
                    pct = item.get("percentage")
                    if pct is None and size_b > 0:
                        pct = round((done_b / size_b) * 100.0, 1)
                    active_files.append(
                        {
                            "name": short_name,
                            "full_path": full_name,
                            "size": format_bytes(size_b),
                            "bytes_done": format_bytes(done_b),
                            "percentage": pct or 0,
                            "speed_bytes": round(eff_file_speed, 1),
                            "speed": f"{format_bytes(eff_file_speed)}/s",
                            "eta": format_seconds(item.get("eta")),
                        }
                    )

                disk_cache = v_data.get("diskCache") or {}
                return {
                    "online": True,
                    "speed_bytes": round(effective_global_speed, 1),
                    "speed": f"{format_bytes(effective_global_speed)}/s",
                    "total_bytes_transferred": format_bytes(global_bytes),
                    "active_count": len(active_files),
                    "errors": c_data.get("errors", 0),
                    "transfers": active_files,
                    "vfs_cache": {
                        "bytes_used": format_bytes(disk_cache.get("bytesUsed", 0)),
                        "files_in_cache": disk_cache.get("files", 0),
                        "uploads_in_progress": disk_cache.get("uploadsInProgress", 0),
                        "uploads_queued": disk_cache.get("uploadsQueued", 0),
                    },
                }
            except Exception as exc:
                return {
                    "online": False,
                    "error": str(exc),
                    "speed": "0 B/s",
                    "active_count": 0,
                    "transfers": [],
                    "vfs_cache": {},
                }

        io_rates, qb_data, rc_data = await asyncio.gather(
            self.sample_io_rates(),
            _fetch_qb(),
            _fetch_rclone(),
        )
        disk_space = self.get_local_disk_usage()

        return {
            "timestamp": now,
            "system": {
                "disk": disk_space,
                "io": io_rates,
            },
            "qbittorrent": qb_data,
            "rclone": rc_data,
        }

    async def get_full_system_metrics(self) -> dict[str, Any]:
        """Aggregates local hardware sensors, disk/network I/O, and Docker status."""
        cpu_usage_task = asyncio.create_task(self._sample_cpu_usage_percent())
        io_task = asyncio.create_task(self.sample_io_rates())
        docker_task = asyncio.create_task(docker_service.list_containers(all_containers=True))

        homepage_sysinfo = None
        homepage_status = None
        try:
            homepage_sysinfo = await self.request("GET", "/api/sysinfo")
        except Exception:
            pass

        try:
            homepage_status = await self.request("GET", "/api/status")
        except Exception:
            pass

        sampled_cpu_percent, io_rates, docker_res = await asyncio.gather(
            cpu_usage_task, io_task, docker_task
        )
        cpu_details = self.get_cpu_details()
        if isinstance(homepage_sysinfo, dict) and "cpu" in homepage_sysinfo:
            hp_load = homepage_sysinfo["cpu"].get("load")
            cpu_details["usage_percent"] = float(hp_load) if hp_load is not None else sampled_cpu_percent
        else:
            cpu_details["usage_percent"] = sampled_cpu_percent

        memory_details = self.get_memory_details()
        thermal_details = self.get_thermal_details()
        gpu_details = self.get_gpu_details()
        power_uptime = self.get_power_and_uptime()
        root_disk = self.get_local_disk_usage()
        root_disk["read_speed"] = io_rates.get("disk_read_speed", "0 B/s")
        root_disk["write_speed"] = io_rates.get("disk_write_speed", "0 B/s")

        os_info: dict[str, Any] = {}
        os_release_raw = self._read_file_safe("/etc/os-release")
        if os_release_raw:
            for line in os_release_raw.splitlines():
                if line.startswith("PRETTY_NAME="):
                    os_info["distro"] = line.split("=", 1)[1].strip().strip('"')
        if isinstance(homepage_sysinfo, dict) and homepage_sysinfo.get("os"):
            os_info = homepage_sysinfo.get("os", os_info)

        network_info = {
            "rx_speed": io_rates.get("net_rx_speed", "0 B/s"),
            "tx_speed": io_rates.get("net_tx_speed", "0 B/s"),
        }
        if isinstance(homepage_sysinfo, dict):
            net_raw = homepage_sysinfo.get("network", {})
            if isinstance(net_raw, dict) and (net_raw.get("rx_sec") or net_raw.get("tx_sec")):
                network_info = {
                    "rx_speed": f"{format_bytes(net_raw.get('rx_sec', 0))}/s",
                    "tx_speed": f"{format_bytes(net_raw.get('tx_sec', 0))}/s",
                }

        docker_summary = docker_res.get("summary", {}) if isinstance(docker_res, dict) else {}
        if not docker_summary.get("total") and isinstance(homepage_sysinfo, dict):
            docker_summary = homepage_sysinfo.get("docker", {})

        return {
            "os": os_info,
            "uptime_and_power": power_uptime,
            "cpu": cpu_details,
            "temperatures": thermal_details,
            "memory": memory_details,
            "gpu": gpu_details,
            "system_disk": root_disk,
            "network": network_info,
            "docker_containers": docker_summary,
            "public_endpoints_ping": homepage_status if isinstance(homepage_status, list) else [],
        }


system_monitor_service = SystemMonitorService()
