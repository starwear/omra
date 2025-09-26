import os, io, time
from quart import Quart, request, make_response, send_file
from dotenv import load_dotenv
from PIL import Image
from email.utils import formatdate
from datetime import datetime, timedelta, timezone

app = Quart(__name__)

# Загружаем конфигурацию сервера
load_dotenv()

AVATARS_PATH = os.environ.get("avatars_path")

async def create_empty_avatar(size: int):
    img = Image.new('RGB', (size, size), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=1)
    buf.seek(0)
    return buf

@app.route('/<domain>/<username>/<type>', methods=['GET', 'HEAD'])
async def get_avatar(domain, username, type):
    if type == "_mrimavatar" or type == "_avatar":
        size = 90
    elif type == "_mrimavatarsmall":
        size = 45
    else:
        return "Bad Request", 400

    file_name = f"{username}_{domain}.jpg"
    path = AVATARS_PATH + file_name

    if not os.path.isfile(path):
        # Создаем пустышку
        empty_avatar = await create_empty_avatar(1)

        # Создаем ответ
        if request.method == 'GET':
            response = await make_response(
                await send_file(
                    filename_or_io=empty_avatar,
                    mimetype='image/jpeg',
                    conditional=True,
                    as_attachment=False
                )
            )
        elif request.method == 'HEAD':
            response = await make_response()
        else:
            return "Bad Request", 400

        # Дата истечения аватарки
        expires = datetime.now() + timedelta(days=7)

        # Заголовки
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=604800',
            'Last-Modified': formatdate(time.time(), localtime=True),
            'Expires': formatdate(expires.timestamp(), localtime=True),
            'X-NoImage': '1'
        }

        response.headers.update(headers)
        return response
    else:
        # Ресайзим картинку
        with Image.open(path) as img:
            img = img.resize((size, size), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, 'JPEG')
            buf.seek(0)

        # Дата истечения аватарки
        expires = datetime.now() + timedelta(days=7)

        # Заголовки
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=604800',
            'Last-Modified': formatdate(os.path.getmtime(path), localtime=True),
            'Expires': formatdate(expires.timestamp(), localtime=True)
        }

        # Создаем ответ
        if request.method == 'GET':
            response = await make_response(
                await send_file(
                    filename_or_io=buf,
                    mimetype='image/jpeg',
                    conditional=True,
                    as_attachment=False
                )
            )
        elif request.method == 'HEAD':
            response = await make_response()
        else:
            return "Bad Request", 400
        
        response.headers.update(headers)
        return response


app.run(
    port=os.environ.get("avatars_port")
)