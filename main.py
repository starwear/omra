# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import asyncio, mrim.general, mrim.redirect, mrim.avatars

async def main():
    await asyncio.gather(
        mrim.redirect.main(),
        mrim.general.main(),
        mrim.avatars.main()
    )

if __name__ == "__main__":
    asyncio.run(
        main()
    )