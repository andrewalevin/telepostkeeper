import asyncio
import hashlib
import pathlib
import time
from typing import Optional

import yaml


async def write_yaml(path: pathlib.Path, data: any) -> Optional[pathlib.Path]:
    path = pathlib.Path(path)
    try:
        with path.open('w') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print('Error Writing YAML: ', e)
        return

    return path


async def read_yaml(path: pathlib.Path) -> any:
    path = pathlib.Path(path)
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print("Failed to load YAML from %s: %s", path, e)
    except Exception as e:
        print("Unexpected error reading %s: %s", path, e)

    return data

async def get_md5(data: str, salt: str) -> str:
    # Combine the data with the salt
    salted_data = data.encode() + salt.encode()

    # Create MD5 hash object
    md5_hash = hashlib.md5()

    # Update the hash object with the salted data
    md5_hash.update(salted_data)

    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest()


async def run_command(cmd: str, timeout: int = None, throttle_delay: int = 0):
    """
    Run a command asynchronously with a timeout option and log output in real-time.

    Args:
        cmd (str): The shell command to execute.
        timeout (int or None): Timeout in seconds. If None, no timeout is applied.

    Returns:
        tuple: (stdout, stderr, return_code)
        :param cmd:
        :param timeout:
        :param throttle_delay:
    """
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Read stdout and stderr line by line and log immediately
    stdout_lines = []
    stderr_lines = []

    async def read_stream(stream, lines, _throttle_delay):
        """Helper to read a stream line by line and log each line with a throttle delay."""
        last_log_time = time.time()

        while True:
            line = await stream.readline()
            if line:
                decoded_line = line.decode().strip()

                # Apply throttle logic: only log if enough time has passed
                current_time = time.time()
                if current_time - last_log_time >= _throttle_delay:
                    print(decoded_line)
                    last_log_time = current_time

                lines.append(decoded_line)  # Store the line for final return
            else:
                break

    try:
        # Use asyncio.gather with a timeout if specified
        if timeout is not None:
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout, stdout_lines, throttle_delay),
                    read_stream(process.stderr, stderr_lines, throttle_delay)
                ),
                timeout=timeout
            )
            # Wait for the process to exit within the timeout
            return_code = await asyncio.wait_for(process.wait(), timeout=timeout)
        else:
            # No timeout applied
            await asyncio.gather(
                read_stream(process.stdout, stdout_lines, throttle_delay),
                read_stream(process.stderr, stderr_lines, throttle_delay)
            )
            return_code = await process.wait()

    except asyncio.TimeoutError:
        print("Command timed out. Killing process.")
        process.kill()
        await process.wait()  # Ensure process cleanup
        return "\n".join(stdout_lines), "\n".join(stderr_lines), None

    return "\n".join(stdout_lines), "\n".join(stderr_lines), return_code