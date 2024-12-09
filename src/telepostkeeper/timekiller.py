import subprocess
import time
import argparse


def run_subprocess(seconds):
    print('🚀 Subprocess.call:')

    # Запуск main.py как отдельного процесса
    # Запускаем процесс
    process = subprocess.Popen(
        ['telepostkeeper'],  # команда
        stdout=subprocess.PIPE,  # перенаправляем стандартный вывод
        stderr=subprocess.PIPE,  # перенаправляем стандартный вывод ошибок (опционально)
        text=True  # обеспечивает строковый вывод вместо байтов
    )

    # Читаем вывод из stdout и stderr
    stdout, stderr = process.communicate()

    # Выводим результаты
    if stdout:
        print("Standard Output:")
        print(stdout)

    if stderr:
        print("Standard Error:")
        print(stderr)


    # Пауза на указанное количество секунд
    time.sleep(seconds)

    print('🔫 Subprocess.kill: ')

    # Завершение процесса
    process.kill()


def main():
    # Парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Run and kill a subprocess after a specified time.")
    parser.add_argument("seconds", type=int, help="Time in seconds before killing the subprocess.")
    args = parser.parse_args()

    # Запуск основной функции
    run_subprocess(args.seconds)

if __name__ == "__main__":
    main()