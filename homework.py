import logging
import sys
import time
from http import HTTPStatus

import requests
import telegram

from settings import (PRACTICUM_TOKEN, RETRY_TIME, TELEGRAM_CHAT_ID,
                      TELEGRAM_TOKEN)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot, message):
    """Отправляет сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение {message} отправлено в Telegram')
    except telegram.error.TelegramError as te:
        logger.error(f'Неудачная отправка сообщения: {te.message}')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
    else:
        if response.status_code != HTTPStatus.OK:
            logger.error(
                f'Эндопоинт недоступен. Код ответа API: {response.status_code}'
            )
            raise ConnectionError
    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if type(response) != dict:
        raise TypeError(f'Неверный тип ответа API: {type(response)}')
    homework = response.get('homeworks')
    if homework is None:
        logger.error('Отсутсвует ожидаемый ключ')
        raise KeyError
    if type(homework) != list:
        raise TypeError(
            f'Неверный тип ответа функции: {type(homework)}'
        )
    if not homework:
        logger.info('Пустой список')
    return homework


def parse_status(homework):
    """Статус домашней работы."""
    try:
        homework_name = homework['homework_name']
    except Exception as error:
        logger.error(f'Отсутсвует ключ homework_name: {error}')
    try:
        homework_status = homework['status']
    except Exception as error:
        logger.error(f'Отсутсвует ключ status: {error}')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error(
            f'Недокументированный статус {homework_status}'
        )
        raise KeyError
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logger.critical(
            'Обязательные переменные окружения отсутствуют.'
        )
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != status:
                send_message(bot, message)
                status = message
            logger.error(error, exc_info=True)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
