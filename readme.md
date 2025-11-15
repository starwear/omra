# OMRA

Ещё 1 сервер под Агент Mail.ru

# Требования

OMRA тестировалась на Python 3.12 / 3.13. Работа на версиях выше или ниже не гарантирована.

В качестве базы данных вы можете использовать MySQL или MariaDB. 

# Установка

Перед использованием вам необходимо импортировать схему таблиц из `tables.sql` и настроить сервер. Также если вы хотите использовать SSL на MRA 6.2-6.5 вам потребуется любой сертификат для SSL (например, от Let's Encrypt или самоподписный)

Пример `.env` файла

```
mysql_host = localhost
mysql_port = 3306
mysql_user = starwear
mysql_pass = qwe123
mysql_base = omrabase

main_host = 127.0.0.1
main_port = 2043

redirect_host = 127.0.0.1
redirect_port = 2042

certfile_path = C:\certs\certificate.crt
keyfile_path = C:\certs\private.key

telegram_bot_token = example

avatars_path = C:\avatars\
avatars_port = 2041
avatars_host = 127.0.0.1
```

Пример создания пользователя:

```sql
INSERT INTO `users` (`email`, `password`) VALUES ("admin@mail.ru", MD5("qwerty"));
INSERT INTO `user_data` (`email`, `nickname`, `groups`, `contacts`, `status`) VALUES ("admin@mail.ru", "Admin", '[{"flags":0,"name":"General"}]', "[]", 1);
INSERT INTO `anketa` (`email`, `username`, `domain`) VALUES ("admin@mail.ru", "admin", "mail.ru");
```

Установите зависимости:

```bash
pip install -r requirements.txt
```