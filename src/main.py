import asyncio
import signal

from bot import run_bot


def main():
    # Setup signal handling for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTSTP, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    asyncio.run(run_bot())


async def shutdown(loop):
    print("Shutting down gracefully...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    loop.stop()
    print("Bot stopped.")