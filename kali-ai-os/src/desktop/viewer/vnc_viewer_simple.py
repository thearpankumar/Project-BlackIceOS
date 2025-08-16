"""
Simple VNC Client Launcher - Single Method Only
"""

import logging
import subprocess


def launch_remmina_simple(host: str, port: int, logger: logging.Logger) -> bool:
    """Simple Remmina launcher - just run the command"""
    logger.info("Launching Remmina...")
    subprocess.Popen(['/usr/bin/remmina', f'vnc://localhost:{port}'])  # noqa: S603
    return True
