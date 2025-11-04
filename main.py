# -*- coding: utf-8 -*-

# OMRA, by Starwear

# Импортируем библиотеки
import asyncio, main_server, redirect_server

async def main():
    await asyncio.gather(
        redirect_server.main(),
        main_server.main()
    )

if __name__ == "__main__":
    asyncio.run(
        main()
    )