import os
import io
import time
from datetime import datetime, timedelta
from email.utils import formatdate

from aiohttp import web
from dotenv import load_dotenv
from PIL import Image

# Загружаем конфигурацию сервера
load_dotenv()

AVATARS_PATH = os.environ.get("avatars_path")

async def get_avatar(request):
    domain = request.match_info['domain']
    username = request.match_info['username']
    type_avatar = request.match_info['type']
    
    if type_avatar == "_mrimavatar" or type_avatar == "_avatar":
        size = 90
    elif type_avatar == "_mrimavatarsmall":
        size = 45
    elif type_avatar == "_mrimavatar128":
        size = 128
    elif type_avatar == "_mrimavatar32":
        size = 32
    elif type_avatar == "_mrimavatar22":
        size = 22
    elif type_avatar == "_mrimavatar60":
        size = 60
    elif type_avatar == "_mrimavatar180":
        size = 180
    else:
        return web.Response(text="Bad Request", status=400)

    # Костыль для MRA 6.x
    if domain == "mail.ru":
        domain = "mail"
    elif domain == "bk.ru":
        domain = "bk"
    elif domain == "inbox.ru":
        domain = "inbox"
    elif domain == "list.ru":
        domain = "list"
    elif domain == "corp.mail.ru":
        domain = "corp"

    file_name = f"{username}_{domain}.jpg"
    path = os.path.join(AVATARS_PATH, file_name)

    if not os.path.isfile(path):
        # Дата истечения аватарки
        expires = datetime.now() + timedelta(days=7)

        # Заголовки
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=604800',
            'Last-Modified': formatdate(time.time(), localtime=False),
            'Expires': formatdate(expires.timestamp(), localtime=False),
            'X-NoImage': '1',
        }

        return web.Response(status=200, headers=headers, content_type='image/jpeg')

    else:
        # Ресайзим картинку
        with Image.open(path) as img:
            img = img.resize((size, size), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, 'JPEG')
            buf.seek(0)

        # Дата истечения аватарки
        expires = datetime.now() + timedelta(days=7)

        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=604800',
            'Last-Modified': formatdate(os.path.getmtime(path), localtime=False),
            'Expires': formatdate(expires.timestamp(), localtime=False),
        }

        return web.Response(body=buf.getvalue(), status=200, headers=headers, content_type='image/jpeg')

app = web.Application()
app.router.add_get('/{domain}/{username}/{type}', get_avatar)

if __name__ == '__main__':
    web.run_app(app, host=os.environ.get("avatars_host"), port=int(os.environ.get("avatars_port")))
