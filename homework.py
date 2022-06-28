import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (
    APIResponseError, PracticumError, TelegramError, ConnectionError
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: Bot, message: str) -> None:
    """Отправка сообщений в телеграм."""
    try:
        logging.info(
            'Отправляем сообщение в телеграм: %s', message
        )
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as exc:
        raise TelegramError(
            f'Ошибка отправки сообщения в телеграмм: {exc}'
        ) from exc
    else:
        logging.info('Сообщение в телеграм успешно отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    except Exception as exc:
        raise PracticumError(f'Ошибка подключения к API: {exc}') from exc

    if response.status_code == HTTPStatus.OK:
        try:
            return response.json()
        except Exception as exc:
            raise APIResponseError(
                f'Ошибка преобразования response в json: {exc}'
            ) from exc
    else:
        raise ConnectionError('Неверный статус-код сервера')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        message = 'Ответ API не содержит словаря с данными'
        raise TypeError(message)

    elif any([response.get('homeworks') is None,
              response.get('current_date') is None]):
        message = ('Словарь ответа API не содержит ключей homeworks и/или '
                   'current_date')
        raise KeyError(message)

    elif not isinstance(response.get('homeworks'), list):
        message = 'Ключ homeworks в ответе API не содержит списка'
        raise TypeError(message)

    elif not response.get('homeworks'):
        logging.debug('Статус проверки не изменился')
        return {}

    else:
        return response['homeworks']


def parse_status(homework):
    """Функция возвращает ответ API yandex practicum со статусом проверки."""
    if homework.get('homework_name') is None:
        message = 'Словарь ответа API не содержит ключа homework_name'
        raise KeyError(message)
    elif homework.get('status') is None:
        message = 'Словарь ответа API не содержит ключа status'
        raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
    else:
        message = 'Статус ответа не известен'
        raise APIResponseError(message)

    message = (f'Изменился статус проверки работы "{homework_name}".'
               f' {verdict}')
    logging.debug(message)
    return message


def check_tokens() -> bool:
    """Проверяет наличие всех переменных окружения."""
    return all((
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = (
            'Отсутствуют обязательные переменные окружения: '
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID.'
            'Программа принудительно остановлена'
        )
        logging.critical(error_message)
        sys.exit(error_message)

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    current_report = None
    prev_report = current_report

    while True:
        try:
            response = get_api_answer(current_timestamp)

            result_check = check_response(response)

            current_report = parse_status(result_check)

            if current_report == prev_report:
                logging.debug(
                    'Статус домашней работы не обновился.'
                    'Придется ещё немного подождать.'
                )
        except Exception as exc:
            error_message = f'Сбой в работе программы: {exc}'
            current_report = error_message
            logging.exception(error_message)

        try:
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report

        except TelegramError as exc:
            error_message = f'Сбой в работе программы: {exc}'
            logging.exception(error_message)

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    log_format = (
        '%(asctime)s [%(levelname)s] - '
        '(%(filename)s).%(funcName)s:%(lineno)d - %(message)s'
    )
    log_file = os.path.join(BASE_DIR, 'output.log')
    log_stream = sys.stdout
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(log_stream)
        ]
    )
    main()
