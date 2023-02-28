from __future__ import print_function
from configobj import ConfigObj
import os.path
import asyncio
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=f'log.txt')
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
config_file = 'settings.ini'
config = ConfigObj(config_file, encoding="utf-8")
sections = ['Google API', 'Google Sheet', 'Telegram']
SAMPLE_SPREADSHEET_ID = config[sections[1]]['spreadsheet_id']
SAMPLE_RANGE_NAME = config[sections[1]]['sample_range_name']
API_TOKEN = config[sections[2]]['api_token']
CHAT_ID = int(config[sections[2]]['chat_id'])
log = logging.getLogger('logger')
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> int:
    try:
        message = await bot.send_message(user_id, text, disable_notification=disable_notification,
                                         disable_web_page_preview=True)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.error(f"Target [ID:{user_id}]: failed")
    else:
        return message.message_id
    return False


def read_google_sheet():
    creds = None
    token_file = 'token.json'
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config[sections[0]]['credentials_file'], SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])
        if not values:
            print('No data found.')
            return None
        return values
    except HttpError as err:
        log.error(f"{err}")


def get_last_response_id_from_settings():
    if not os.path.exists(config_file):
        config[sections[1]] = {'last_response_id': '0'}
        config.write()
    return config[sections[1]]['last_response_id']


def update_last_response_id(last_response_id: str):
    config[sections[1]]['last_response_id'] = last_response_id
    config.write()


async def main():
    last_response_id = get_last_response_id_from_settings()
    values = read_google_sheet()
    last_row_number = len(values)
    if last_response_id == '0':
        for row in reversed(values):
            last_response_id = row[0]
            break
        update_last_response_id(last_response_id)
        log.info(f'Первый запуск и настройка прошли успешно. Последняя найденная жалоба - {last_response_id}.')
        return
    message_list = []
    for row in reversed(values):
        if last_response_id == row[0]:
            break
        message = f'<b>Новая жалоба {last_row_number} поступила в таблицу!</b>\n\
ID жалобы: {row[0]}\n\
Время подачи: {row[1]}\n\
Время получения: {row[2]}\n\
IP отправителя: {row[3]}\n\
User ID отправителя: {row[4]}\n\
Почта отправителя: {row[5]}\n\
Тип жалобы: {row[6]}\n\
Комментарий: {row[7]}\n\
Доказательства: {row[8]}\n\
ID Канала: {row[9]}\n\
URL Стрима: {row[10]}\n\
URL Канала: {row[11]}\n\
        \n'
        last_row_number -= 1
        message = (message[:4090] + '...') if len(message) > 4096 else message
        message_list.append(message)
    message_list = message_list if config[sections[2]]['sort'] == 'desc' else reversed(message_list)
    for message in message_list:
        await send_message(CHAT_ID, message)
        log.info(f'Message "{message[3:30]}..." was sent to the chat')
    for row in reversed(values):
        last_response_id = row[0]
        break
    update_last_response_id(last_response_id)


if __name__ == '__main__':
    try:
        executor.start(dp, main())
    except exceptions.TelegramAPIError:
        log.error(f"Telegram API Error. Check your api_token and chat_id in settings.ini")
