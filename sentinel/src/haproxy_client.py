import asyncio
import logging
import os

logger = logging.getLogger("driftguard.haproxy")


async def send_haproxy_command(socket_path: str, command: str) -> str:
    """
    Sends a CLI command to the HAProxy UNIX domain socket and reads the response.
    Returns empty string if socket is unavailable or error occurs.
    """
    if not os.path.exists(socket_path):
        logger.debug(f"HAProxy socket at '{socket_path}' not found.")
        return ""

    try:
        reader, writer = await asyncio.open_unix_connection(socket_path)
        cmd_bytes = f"{command.strip()}\n".encode("utf-8")
        writer.write(cmd_bytes)
        await writer.drain()

        # HAProxy sends output and closes connection for one-shot commands
        chunks = []
        while True:
            chunk = await reader.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        writer.close()
        await writer.wait_closed()
        return b"".join(chunks).decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Error communicating with HAProxy socket ({socket_path}): {e}")
        return ""


async def get_backend_stats(
    backend_name: str,
    socket_path: str = "/run/haproxy/admin.sock"
) -> dict[str, int]:
    """
    Connects to the HAProxy UNIX domain socket, sends 'show stat', and extracts:
    - total_requests ('stot')
    - current_in_flight ('scur')
    - http_2xx ('hrsp_2xx')
    - http_5xx ('hrsp_5xx')
    """
    default_stats = {
        "total_requests": 0,
        "current_in_flight": 0,
        "http_2xx": 0,
        "http_5xx": 0,
    }

    # Handle flexible argument order if socket_path and backend_name are reversed
    if backend_name.startswith("/") or "sock" in backend_name:
        socket_path, backend_name = backend_name, socket_path

    if not socket_path:
        socket_path = os.environ.get("HAPROXY_SOCKET_PATH", "/run/haproxy/admin.sock")

    if not os.path.exists(socket_path):
        logger.debug(f"HAProxy socket at '{socket_path}' not found for backend stats.")
        return default_stats

    try:
        raw_output = await send_haproxy_command(socket_path, "show stat")
        if not raw_output:
            return default_stats

        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        if not lines:
            return default_stats

        header_line = lines[0].lstrip("#").strip()
        headers = [h.strip() for h in header_line.split(",")]

        matching_rows: list[dict[str, str]] = []
        for line in lines[1:]:
            parts = [p.strip() for p in line.split(",")]
            row = dict(zip(headers, parts))
            if row.get("pxname") == backend_name:
                matching_rows.append(row)

        if not matching_rows:
            logger.debug(f"No HAProxy stat rows found matching backend '{backend_name}'.")
            return default_stats

        # Prefer aggregate BACKEND row, otherwise fallback to primary server row
        target_row = next((r for r in matching_rows if r.get("svname") == "BACKEND"), matching_rows[0])

        def _parse_int(val: str | None) -> int:
            try:
                return int(val) if val not in (None, "", "-") else 0
            except (ValueError, TypeError):
                return 0

        return {
            "total_requests": _parse_int(target_row.get("stot")),
            "current_in_flight": _parse_int(target_row.get("scur")),
            "http_2xx": _parse_int(target_row.get("hrsp_2xx")),
            "http_5xx": _parse_int(target_row.get("hrsp_5xx")),
        }
    except Exception as exc:
        logger.warning(f"Failed to query backend stats for '{backend_name}' from {socket_path}: {exc}")
        return default_stats


async def set_server_state(socket_path: str, backend: str, server: str, state: str) -> bool:
    """
    Dynamically update HAProxy server state via UNIX socket:
    'set server <backend>/<server> state maint'
    'set server <backend>/<server> state ready'
    """
    if (state not in {"ready", "maint"}
            or not backend
            or not backend[0].isalpha()
            or not all(char.isalnum() or char == "_" for char in backend)):
        logger.error("Rejected invalid HAProxy state command")
        return False
    if server not in {"primary", "fallback"}:
        logger.error("Rejected invalid HAProxy server name")
        return False
    if not os.path.exists(socket_path):
        logger.error("HAProxy admin socket is unavailable; failed to update %s/%s", backend, server)
        return False

    cmd = f"set server {backend}/{server} state {state}"
    resp = await send_haproxy_command(socket_path, cmd)
    if any(error in resp for error in ("No such server", "No such backend", "Unknown command", "Permission denied")):
        logger.error(f"HAProxy rejected command '{cmd}': {resp.strip()}")
        return False
    logger.debug("HAProxy socket state updated: %s", cmd)
    return True
