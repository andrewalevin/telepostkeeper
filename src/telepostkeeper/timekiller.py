import subprocess
import sys
import time
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_subprocess(command: str, seconds: int):
    """
    Runs a subprocess using a command passed as a string, splits it into parts,
    and terminates it after a specified number of seconds.

    Args:
        command (str): The command to run as a subprocess (single string, e.g., "echo Hello World").
        seconds (int): Number of seconds to run the subprocess.

    Raises:
        ValueError: If input arguments are invalid.
        RuntimeError: If the subprocess fails to start or terminate properly.
    """
    if not isinstance(command, str) or not command.strip():
        raise ValueError("The 'command' parameter must be a non-empty string.")

    if not isinstance(seconds, int) or seconds <= 0:
        raise ValueError("The 'seconds' parameter must be a positive integer.")

    # Split the command into parts for subprocess
    command_parts = command.split()
    logger.info(f"🚀 Starting subprocess ...")


    try:
        # Start the subprocess
        process = subprocess.Popen(command_parts)

        # Sleep for the specified duration
        time.sleep(seconds)

        logger.info("🔫 Attempting to terminate subprocess...")

        # Terminate the subprocess
        process.terminate()

        # Ensure the process terminates gracefully
        process.wait(timeout=5)
        logger.info("✅ Subprocess terminated successfully.")
    except subprocess.TimeoutExpired:
        logger.warning("⚠️ Subprocess did not terminate gracefully, forcing termination...")
        process.kill()
        logger.info("✅ Subprocess forcefully terminated.")
    except Exception as e:
        logger.error(f"❌ Error while managing subprocess: {e}")
        raise RuntimeError(f"Subprocess execution failed: {e}") from e
    finally:
        # Ensure subprocess resources are cleaned up
        if process and process.poll() is None:
            process.kill()
            logger.warning("⚠️ Subprocess had to be forcefully killed in cleanup.")

def main():
    """
    Основная функция для парсинга аргументов и вызова run_subprocess.
    """
    try:
        # Парсер аргументов командной строки
        parser = argparse.ArgumentParser(description="Run and kill a subprocess after a specified time.")
        parser.add_argument(
            "command",
            nargs="?",
            default="telepostkeeper",
            help="Command to run in the subprocess (default: 'telepostkeeper')."
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Time in seconds before killing the subprocess (default: 10 seconds)."
        )
        args = parser.parse_args()

        # Логирование информации о запуске
        logger.info(f"🚀 Running command '{args.command}' for {args.timeout} seconds.")

        # Запуск основной функции

        #run_subprocess0(args.seconds)

        run_subprocess(args.command, args.timeout)


    except KeyboardInterrupt:
        logger.warning("❗ Program interrupted by the user.")
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred in main(): {e}")

if __name__ == "__main__":
    main()