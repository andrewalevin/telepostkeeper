import asyncio
import signal

shutdown_event = asyncio.Event()

async def handle_interrupt_or_suspend(signum):
    """
    Handles signals for graceful termination or suspension.
    """
    messages = {
        signal.SIGTSTP: "\nReceived SIGTSTP (Ctrl+Z). Suspending is disabled.",
        signal.SIGINT: "\nReceived SIGINT (Ctrl+C). Exiting gracefully.",
    }
    print(messages.get(signum, "Unknown signal received."))
    shutdown_event.set()  # Notify the main loop to terminate

def setup_signal_handlers():
    """
    Registers signal handlers for SIGTSTP and SIGINT.
    """
    loop = asyncio.get_event_loop()
    for signum in (signal.SIGTSTP, signal.SIGINT):
        signal.signal(signum, lambda s, f: asyncio.run_coroutine_threadsafe(handle_interrupt_or_suspend(s), loop))

async def run_bot():
    """
    Main loop that runs until a shutdown signal is received.
    """
    setup_signal_handlers()

    print("Press Ctrl+C to exit or Ctrl+Z to test SIGTSTP handling.")
    try:
        while not shutdown_event.is_set():
            print("Running... Press Ctrl+C to stop.")
            await asyncio.sleep(2)
    finally:
        print("Cleaning up...")


def main():
    """
    Entry point for the application.
    """
    asyncio.run(run_bot())

main()