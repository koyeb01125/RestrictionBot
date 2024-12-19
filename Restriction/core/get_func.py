import asyncio
import time, re, os
import aiohttp
from Restriction import app
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, PeerIdInvalid
from pyrogram.enums import MessageMediaType
from Restriction.core.func import progress_bar
from Restriction.core.mongo import settingsdb as db


# ----------------------- Download Thumbnail with aiohttp -----------------------#

async def download_thumbnail(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                filename = url.split("/")[-1]
                with open(filename, 'wb') as f:
                    f.write(await response.read())
                return filename
    return None


# ----------------------- Utility Functions -----------------------#

def replace_text(original_text, replace_txt, to_replace):
    return original_text.replace(replace_txt, to_replace)


def remove_elements(words, cap):
    lol = cap
    for i in words:
        lol = lol.replace(i, '')
    return lol


def clean_string(input_string):
    cleaned_string = re.sub(r'[@,/]', '', input_string)
    return cleaned_string


# ----------------------- Docs Uploader -----------------------#

async def docs_uploader(chat_id, file, caption, thumb, edit):
    try:
        await app.send_document(
            chat_id=chat_id,
            document=file,
            caption=caption,
            thumb=thumb,
            progress=progress_bar,
            progress_args=("UPLOADING", edit, time.time())
        )
    except Exception as e:
        print(f"Error sending document: {e}")


# ----------------------- Video Uploader -----------------------#

async def video_uploader(chat_id, video, caption, height, width, duration, thumb, edit):
    try:
        await app.send_video(
            chat_id=chat_id,
            video=video,
            caption=caption,
            supports_streaming=True,
            height=height,
            width=width,
            duration=duration,
            thumb=thumb,
            progress=progress_bar,
            progress_args=("UPLOADING", edit, time.time())
        )
    except Exception as e:
        print(f"Error Sending Video: {e}")


# ----------------------- Thumb and Caption Generator -----------------------#

async def thumb_caption(userbot, user_id, msg, file):
    data = await db.get_data(user_id)

    caption = data.get("caption") if data and data.get("caption") else msg.caption

    if caption:
        if data and data.get("clean_words"):
            caption = remove_elements(data["clean_words"], caption)

        if data and data.get("replace_txt") and data.get("to_replace"):
            caption = replace_text(caption, data["replace_txt"], data["to_replace"])

    if data and data.get("thumb"):
        thumb_path = await download_thumbnail(data.get("thumb"))
    else:
        thumbnail = None
        if msg.media == MessageMediaType.VIDEO and msg.video.thumbs:
            thumbnail = msg.video.thumbs[0].file_id
        elif msg.media == MessageMediaType.DOCUMENT and msg.document.thumbs:
            thumbnail = msg.document.thumbs[0].file_id

        thumb_path = await userbot.download_media(thumbnail) if thumbnail else None

    return thumb_path or None, caption


# ----------------------- Parallel Media Download -----------------------#

async def parallel_download_media(userbot, media_list, edit):
    tasks = [
        asyncio.create_task(
            userbot.download_media(
                media,
                progress=progress_bar,
                progress_args=("DOWNLOADING", edit, time.time()),
            )
        )
        for media in media_list
    ]
    return await asyncio.gather(*tasks)


# ----------------------- Main Function -----------------------#

async def get_msg(userbot, sender, edit_id, msg_link, edit):
    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]
    msg_id = int(msg_link.split("/")[-1])

    if 't.me/c/' in msg_link or 't.me/b/' in msg_link or 't.me/' in msg_link:
        try:
            if 't.me/b/' in msg_link:
                chat = int(msg_link.split("/")[-2])
            elif 't.me/c/' in msg_link:
                chat = int('-100' + str(msg_link.split("/")[-2]))
            else:
                chat_name = msg_link.split('/')[-2]
                chat = (await userbot.get_chat(f"@{chat_name}")).id
        except Exception as e:
            print(f"ChatID Error: {e}")
            return

        try:
            msg = await userbot.get_messages(chat, msg_id)
            data = await db.get_data(sender)

            # Handle non-media messages
            if not msg.media:
                if msg.text:
                    chat_id = data.get("chat_id") or sender
                    await app.send_message(chat_id, msg.text.markdown)
                    await edit.delete()
                    return

            # Handle media messages
            await edit.edit("Downloading Media...")
            files = await parallel_download_media(userbot, [msg], edit)
            file = files[0] if files else None

            if not file:
                await app.edit_message_text(sender, edit_id, "Failed to download media.")
                return

            thumb_path, caption = await thumb_caption(userbot, sender, msg, file)

            chat_id = data.get("chat_id") or sender
            if msg.media == MessageMediaType.VIDEO:
                await video_uploader(chat_id, file, caption, msg.video.height, msg.video.width, msg.video.duration, thumb_path, edit)
            elif msg.media == MessageMediaType.PHOTO:
                await app.send_photo(chat_id, photo=file, caption=caption)
            else:
                await docs_uploader(chat_id, file, caption, thumb_path, edit)

            # Cleanup
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            if file and os.path.exists(file):
                os.remove(file)

            await edit.delete()

        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await app.edit_message_text(sender, edit_id, "Have you joined the channel?")
            return
        except Exception as e:
            await app.edit_message_text(sender, edit_id, f"**Error**: {str(e)}")




