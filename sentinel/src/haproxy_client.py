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
        response = await reader.read(4096)
        writer.close()
        await writer.wait_closed()
        return response.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Error communicating with HAProxy socket ({socket_path}): {e}")
        return ""


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
