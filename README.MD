1. Скачать и установить последнюю версию https://www.python.org/downloads/
2. Скачать и распаковать текущий репозиторий  к себе на компьютер (Вверху кнопка Code -> Download ZIP)
3. Открыть и заполнить файл settings.ini 
   1. credentials_file - файл с данными для аутентификации Google, создается через https://console.cloud.google.com/apis/credentials
   2. spreadsheet_id - наименование Google таблицы, копируется из адресной строки
   3. sample_range_name - Наименование листа!диапазона столбцов
   4. last_response_id - можно оставить 0 или указать свой последний response id в таблице
   5. api_token - API токен бота. Получить через бота https://t.me/BotFather
   6. chat_id - ID личного диалога или группы. Получить через https://t.me/username_to_id_bot
   7. sort - порядок отправки сообщений: asc - по порядку строк в таблице (сверху вниз), desc - в обратном порядке
4. Открыть командную строку в папке с проектом и установить все зависимости командой:  
**pip install -r requirements.txt**
5. Произвести первый запуск бота командой:  
**python bot.py**  
и предоставить необходимые доступы.
6. Добавить запуск по необходимому вам расписанию в "Планировщик задач" для windows или cron для linux