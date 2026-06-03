from __future__ import annotations

import asyncio
import getpass

from telethon.errors import SessionPasswordNeededError

from app.telegram_service import telegram_service


async def run() -> None:
    if not telegram_service.is_configured():
        raise RuntimeError("Telegram credentials are not configured.")
    client = telegram_service.create_client()
    async with client:
        if await client.is_user_authorized():
            print("Telegram session already authorized.")
            return
        phone = input("Telegram phone number: ").strip()
        sent = await client.send_code_request(phone)
        code = input("Telegram login code: ").strip()
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
        except SessionPasswordNeededError:
            password = getpass.getpass("Telegram 2FA password: ")
            await client.sign_in(password=password)
        if await client.is_user_authorized():
            print("Telegram session saved.")
        else:
            raise RuntimeError("Telegram authorization failed.")


if __name__ == "__main__":
    asyncio.run(run())

