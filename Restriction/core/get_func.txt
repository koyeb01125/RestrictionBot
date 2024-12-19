import asyncio
import time, re
import os
import requests
from Restriction import app
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, PeerIdInvalid
from pyrogram.enums import MessageMediaType
from Restriction.core.func import progress_bar
from Restriction.core.mongo import settingsdb as db
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup




# ----------------------- Download-Thumbnail -----------------------#

async def download_thumbnail(url):
    response = requests.get(url)
    if response.status_code == 200:
        filename = url.split("/")[-1]
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename

# ----------------------- short-functions -----------------------#

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


# ----------------------- Docs-Uploader -----------------------#

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
        await app.send_document(
            chat_id=chat_id,
            document=file,
            caption=caption,
            thumb=None,
            progress=progress_bar,
            progress_args=("UPLOADING", edit, time.time())
        )
 
# ----------------------- Video-Uploader -----------------------#

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
        await app.send_video(
            chat_id=chat_id,  
            video=video,      
            caption=caption,
            supports_streaming=True,
            height=height,
            width=width,
            duration=duration,
            thumb=None,      
            progress=progress_bar,
            progress_args=("UPLOADING", edit, time.time())
        )
        
# ----------------------- Thumb-Caption -----------------------#

async def thumb_caption(userbot, user_id, msg, file):
    data = await db.get_data(user_id)
    
    if data and data.get("caption"):
        caption = data.get("caption")
    else:
        caption = msg.caption

    if caption:
        if data.get("clean_words"):
            words = data.get("clean_words")
            caption = remove_elements(words, caption)

        if data.get("replace_txt") and data.get("to_replace"):
            replace_txt = data.get("replace_txt")
            to_replace = data.get("to_replace")
            caption = replace_text(caption, replace_txt, to_replace)

    if data and data.get("thumb"):
        thumb_url = data.get("thumb")
        thumb_path = await download_thumbnail(thumb_url)
    else:
        thumbnail = None
        
        if msg.media == MessageMediaType.VIDEO and msg.video.thumbs:
            thumbnail = msg.video.thumbs[0].file_id

        elif msg.media == MessageMediaType.DOCUMENT and msg.document.thumbs:
            thumbnail = msg.document.thumbs[0].file_id

        if thumbnail:
            thumb_path = await userbot.download_media(thumbnail)
        else: 
            thumb_path = None
            print("Failed to generate thumbnails")

    return thumb_path or None, caption




# -----------------------Main-Function -----------------------#

async def get_msg(userbot, sender, edit_id, msg_link, edit):
        
    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]
    msg_id = int(msg_link.split("/")[-1])

    if 't.me/c/' in msg_link or 't.me/b/' in msg_link or 't.me/' in msg_link:
        try:
            if 't.me/b/' in msg_link:
                chat = int(msg_link.split("/")[-2])
                print(chat)
            elif 't.me/c/' in msg_link:
                chat = int('-100' + str(msg_link.split("/")[-2]))
                print(chat)
            else:
                chat_name = msg_link.split('/')[-2]
                gp = await userbot.get_chat(f"@{chat_name}")
                chat = gp.id
                print(chat)
        except Exception as e:
            print(f"ChatID Error: {e}")
            return

        
        file = ""
        try:
            msg = await userbot.get_messages(chat, msg_id)
            data = await db.get_data(sender)
                 
            if msg.media:
                if msg.media == MessageMediaType.WEB_PAGE_PREVIEW:
                    await edit.edit("Cloning.")
                    chat_id = data.get("chat_id") if data.get("chat_id") else sender
                    try:
                        await app.send_message(chat_id, msg.text.markdown)
                        await edit.delete()
                        return 
                    except:
                        await app.edit_message_text(sender, edit_id, "The bot is not an admin in the specified chat.")
                        await edit.delete()
                        return 
                        
            
            if not msg.media:
                if msg.text:
                    await edit.edit("Cloning.")
                    chat_id = data.get("chat_id") if data.get("chat_id") else sender
                    try:
                        await app.send_message(chat_id, msg.text.markdown)
                        await edit.delete()
                        return 
                    except:
                        await app.edit_message_text(sender, edit_id, "The bot is not an admin in the specified chat.")
                        await edit.delete()
                        return 
                        
                        
                               
            edit = await app.edit_message_text(sender, edit_id, "**Trying to Download.**")
            try:
                file = await asyncio.create_task(userbot.download_media(
                 msg,
                 progress=progress_bar,
                 progress_args=("DOWNLOADING", edit, time.time())
                ))
            except Exception as e: 
                print(f"Downloading Error: {e}")
                await app.edit_message_text(sender, edit_id, "Skip, bruh this message doest not exist.")
                await asyncio.sleep(2.5)
                await edit.delete()
                return
            
            await edit.edit('Preparing to Upload!')
            thumb_path, caption = await thumb_caption(userbot, sender, msg, file) 
           
            
            if msg.media == MessageMediaType.VIDEO:
                width = msg.video.width
                height = msg.video.height      
                duration = msg.video.duration
                               
                chat_id = data.get("chat_id") if data.get("chat_id") else sender
                try:
                    await video_uploader(chat_id=chat_id, video=file, caption=caption, height=height, width=width, duration=duration, thumb=thumb_path, edit=edit)                    
                except:
                    await app.edit_message_text(sender, edit_id, "The bot is not an admin in the specified chat.")                    
                    
                                            
            elif msg.media == MessageMediaType.PHOTO:
                await edit.edit("Uploading photo.")
                chat_id = data.get("chat_id") if data.get("chat_id") else sender
                try:
                    await app.send_photo(chat_id=chat_id, photo=file, caption=caption)
                except:
                    await app.edit_message_text(sender, edit_id, "The bot is not an admin in the specified chat.")                    
                    
            else:               
                chat_id = data.get("chat_id") if data.get("chat_id") else sender
                try:
                    await docs_uploader(chat_id=chat_id, file=file, caption=caption, thumb=thumb_path, edit=edit)
                except:
                    await app.edit_message_text(sender, edit_id, "The bot is not an admin in the specified chat.") 
                
                    
                

            if not data.get("thumb") and thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            else:
                print("Thumbnail file not found or failed to generate.")
            os.remove(file)                        
            await edit.delete()
        
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await app.edit_message_text(sender, edit_id, "Have you joined the channel?")
            return
        except Exception as e:
            await app.edit_message_text(sender, edit_id, f"**Failed to save**: `{msg_link}`\n\n**Error**: {str(e)}")       
    """  
    else:
        try:            
            await userbot.copy_message(sender, chat, msg_id)
        except Exception as e:
            await app.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
    """






