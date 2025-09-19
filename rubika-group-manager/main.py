import re
import asyncio
import datetime
import json
import os
from typing import Dict, Any, Union, Optional, List
from rubpy import Client
from rubpy.types.update import Update

class BotDatabase:
    def __init__(self, db_file="bot_data.json"):
        self.db_file = db_file
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._default_data()
        return self._default_data()

    def _default_data(self):
        return {
            "users": {},
            "settings": {
                "strict_mode": False,
                "filters": {
                    "gif": False,
                    "story": False,
                    "photo": False,
                    "voice": False,
                    "video": False,
                    "other_files": False
                },
                "voice_call_active": False
            }
        }

    def _save_data(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def get_user_data(self, user_guid: str) -> Dict[str, Any]:
        return self.data["users"].get(user_guid, {})

    def update_user_data(self, user_guid: str, key: str, value: Any):
        if user_guid not in self.data["users"]:
            self.data["users"][user_guid] = {}
        self.data["users"][user_guid][key] = value
        self._save_data()

    def increment_message_count(self, user_guid: str):
        if user_guid not in self.data["users"]:
            self.data["users"][user_guid] = {"messages_count": 0}
        self.data["users"][user_guid]["messages_count"] = self.data["users"][user_guid].get("messages_count", 0) + 1
        self._save_data()

    def set_strict_mode(self, status: bool):
        self.data["settings"]["strict_mode"] = status
        self._save_data()

    def get_strict_mode(self) -> bool:
        return self.data["settings"]["strict_mode"]

    def set_filter(self, filter_type: str, status: bool):
        if filter_type in self.data["settings"]["filters"]:
            self.data["settings"]["filters"][filter_type] = status
            self._save_data()

    def get_filter_status(self, filter_type: str) -> bool:
        return self.data["settings"]["filters"].get(filter_type, False)

    def set_voice_call_status(self, status: bool):
        self.data["settings"]["voice_call_active"] = status
        self._save_data()

    def get_voice_call_status(self) -> bool:
        return self.data["settings"]["voice_call_active"]

client = Client('cortexAi')
db = BotDatabase()

SILENT_USERS = {}

HANG_PATTERNS = [
    r"(22\.){15,}",
    r"(\d{1,3}\.){8,}",
    r"([^\w\s]{4,}){8,}",
    r"(\w{1,3}\s*){30,}",
]

def is_hang_message(text: str) -> bool:
    if isinstance(text, str):
        for pattern in HANG_PATTERNS:
            if re.search(pattern, text):
                return True
    return False

@client.on_chat_updates()
async def welcome_new_member(update: Update):
    if update.json_data and update.json_data.get("update_type") == "NewMessage" and \
       update.json_data.get("message") and update.json_data.get("message").get("type") == "Event":
        event_data = update.json_data["message"]["event_data"]
        event_type = event_data.get("type")
        object_guid = update.object_guid
        
        if event_type == "AddGroupMembers":
            for member_guid in event_data.get("peer_guids", []):
                try:
                    user_info_raw = await client.get_user_info(member_guid)
                    user_name = "کاربر ناشناس"
                    if user_info_raw and user_info_raw.get("data") and user_info_raw["data"].get("user"):
                        user_info = user_info_raw["data"]["user"]
                        user_name = user_info.get("first_name", "")
                        if user_info.get("last_name"):
                            user_name += " " + user_info["last_name"]
                    
                    join_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    db.update_user_data(member_guid, "name", user_name)
                    db.update_user_data(member_guid, "join_date", join_date)
                    db.update_user_data(member_guid, "messages_count", 0)
                    db.update_user_data(member_guid, "warnings", 0)
                    db.update_user_data(member_guid, "title", "")
                    db.update_user_data(member_guid, "is_original", False)

                    welcome_message = f"سلام {user_name} عزیز! به گروه **{client.me.get('first_name', 'cortexAo')}** خوش آمدید.\nتاریخ و زمان ورود: {join_date}"
                    await client.send_message(object_guid, welcome_message)
                except Exception:
                    pass
        
        elif event_type == "RemoveGroupMembers":
            for member_guid in event_data.get("peer_guids", []):
                try:
                    user_data = db.get_user_data(member_guid)
                    user_name = user_data.get("name", "کاربر")
                    await client.send_message(object_guid, f"کاربر {user_name} گروه را ترک کرد.")
                except Exception:
                    pass

@client.on_message_updates()
async def handle_message_updates(update: Update):
    if not (update.json_data and update.json_data.get("update_type") == "NewMessage" and update.json_data.get("message")):
        return

    message = update.json_data["message"]
    user_guid = update.user_guid
    object_guid = update.object_guid
    message_id = message.get("message_id")
    message_type = message.get("type")
    message_text = message.get("text", "")
    
    if user_guid == client.guid:
        return

    if message_type == "Text" and is_hang_message(message_text):
        try:
            await asyncio.wait_for(client.delete_messages(object_guid, [message_id]), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        return

    if user_guid in SILENT_USERS:
        mute_until = SILENT_USERS[user_guid]
        if datetime.datetime.now() < mute_until:
            await client.delete_messages(object_guid, [message_id])
            return
        else:
            del SILENT_USERS[user_guid]

    if message_type == "Text":
        db.increment_message_count(user_guid)

    if message_text == "آمارم":
        user_data = db.get_user_data(user_guid)
        user_name = user_data.get("name", "شما")
        join_date = user_data.get("join_date", "نامشخص")
        messages_count = user_data.get("messages_count", 0)
        warnings = user_data.get("warnings", 0)
        title = user_data.get("title", "ندارد")
        is_original = "ثبت شده" if user_data.get("is_original", False) else "ثبت نشده"

        user_role = "کاربر"
        try:
            is_admin_check = await client.user_is_admin(object_guid=object_guid, user_guid=user_guid)
            if is_admin_check:
                user_role = "ادمین"
        except Exception:
            pass
        
        stats_message = (
            f"📊 آمار {user_name}:\n"
            f"📋 مقام: {user_role}\n"
            f"👑 لقب: {title}\n"
            f"💬 تعداد پیام‌ها: {messages_count}\n"
            f"⚠️ اخطارها: {warnings}\n"
            f"📝 اصل: {is_original}\n"
            f"🕰️ تاریخ ورود: {join_date}"
        )
        await client.send_message(object_guid, stats_message, reply_to_message_id=message_id)

    elif message_text.startswith("اصل "):
        original_content = message_text[4:].strip()
        if original_content:
            db.update_user_data(user_guid, "is_original", original_content)
            await client.send_message(object_guid, f"✅ اصل شما با موفقیت ثبت شد: '{original_content}'", reply_to_message_id=message_id)
        else:
            await client.send_message(object_guid, "لطفاً بعد از 'اصل' متن اصلی خود را وارد کنید.", reply_to_message_id=message_id)

    elif message_text == "اصل":
        user_data = db.get_user_data(user_guid)
        original_content = user_data.get("is_original", "ثبت نشده")
        await client.send_message(object_guid, f"اصل ثبت شده شما: '{original_content}'", reply_to_message_id=message_id)

    if message.get("reply_to_message_id"):
        reply_to_message_id = message["reply_to_message_id"]
        replied_message_obj = await client.get_messages_by_id(object_guid, [reply_to_message_id])
        replied_message_sender_guid = replied_message_obj.messages[0].get("author_object_guid") if replied_message_obj and replied_message_obj.messages else None

        if message_text == "اصل" and replied_message_sender_guid:
            replied_user_data = db.get_user_data(replied_message_sender_guid)
            replied_user_name = replied_user_data.get("name", "کاربر ناشناس")
            original_content = replied_user_data.get("is_original", "ثبت نشده")
            await client.send_message(object_guid, f"اصل ثبت شده توسط {replied_user_name}: '{original_content}'", reply_to_message_id=message_id)
        
        is_sender_admin = False
        try:
            is_sender_admin = await client.user_is_admin(object_guid=object_guid, user_guid=user_guid)
        except Exception:
            pass

        if is_sender_admin and replied_message_sender_guid:
            target_user_data = db.get_user_data(replied_message_sender_guid)
            target_user_name = target_user_data.get("name", "کاربر ناشناس")
            
            if message_text == "بن":
                try:
                    await client.ban_group_member(object_guid, replied_message_sender_guid)
                    await client.send_message(object_guid, f"کاربر {target_user_name} با موفقیت از گروه بن شد.")
                    if replied_message_sender_guid in db.data["users"]:
                        del db.data["users"][replied_message_sender_guid]
                        db._save_data()
                except Exception as e:
                    await client.send_message(object_guid, f"خطا در بن کردن کاربر {target_user_name}: {e}", reply_to_message_id=message_id)

            elif message_text == "ادمین معمولی":
                try:
                    await client.set_group_admin(object_guid, replied_message_sender_guid, action="UnsetAdmin")
                    await client.send_message(object_guid, f"کاربر {target_user_name} با موفقیت به ادمین معمولی تبدیل شد.")
                except Exception as e:
                    await client.send_message(object_guid, f"خطا در تبدیل کاربر {target_user_name} به ادمین معمولی: {e}", reply_to_message_id=message_id)

            elif message_text == "ویژه":
                db.update_user_data(replied_message_sender_guid, "role", "ویژه")
                await client.send_message(object_guid, f"کاربر {target_user_name} با موفقیت به ادمین ویژه تبدیل شد.")
                
            elif message_text.startswith("لقب "):
                new_title = message_text[4:].strip()
                if new_title:
                    db.update_user_data(replied_message_sender_guid, "title", new_title)
                    await client.send_message(object_guid, f"✅ لقب کاربر {target_user_name} با موفقیت به '{new_title}' تغییر یافت.", reply_to_message_id=message_id)
                else:
                    await client.send_message(object_guid, "لطفاً بعد از 'لقب' لقب مورد نظر را وارد کنید.", reply_to_message_id=message_id)
            
            elif message_text.startswith("سکوت "):
                try:
                    duration_minutes = int(message_text[len("سکوت "):].strip())
                    if duration_minutes > 0:
                        mute_until = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)
                        SILENT_USERS[replied_message_sender_guid] = mute_until
                        await client.send_message(object_guid, f"کاربر {target_user_name} به مدت {duration_minutes} دقیقه سکوت شد.")
                    else:
                        await client.send_message(object_guid, "لطفاً مدت زمان سکوت را به دقیقه و به صورت عدد صحیح وارد کنید (مثال: سکوت 1).", reply_to_message_id=message_id)
                except ValueError:
                    await client.send_message(object_guid, "لطفاً مدت زمان سکوت را به دقیقه و به صورت عدد صحیح وارد کنید (مثال: سکوت 1).", reply_to_message_id=message_id)
    
    if user_guid and is_sender_admin:
        if message_text == "سختگیرانه فعال":
            db.set_strict_mode(True)
            await client.send_message(object_guid, "⚙️ حالت سختگیرانه فعال شد. ارسال لینک منجر به بن کاربر می‌شود.")
        elif message_text == "سختگیرانه خاموش":
            db.set_strict_mode(False)
            await client.send_message(object_guid, "⚙️ حالت سختگیرانه غیرفعال شد. ارسال لینک منجر به حذف لینک می‌شود.")
        
        filter_commands = {
            "فیلتر گیف فعال": ("gif", True), "فیلتر گیف خاموش": ("gif", False),
            "فیلتر استوری فعال": ("story", True), "فیلتر استوری خاموش": ("story", False),
            "فیلتر عکس فعال": ("photo", True), "فیلتر عکس خاموش": ("photo", False),
            "فیلتر ویس فعال": ("voice", True), "فیلتر ویس خاموش": ("voice", False),
            "فیلتر ویدیو فعال": ("video", True), "فیلتر ویدیو خاموش": ("video", False),
            "فیلتر سایر فعال": ("other_files", True), "فیلتر سایر خاموش": ("other_files", False),
        }
        if message_text in filter_commands:
            filter_type, status = filter_commands[message_text]
            db.set_filter(filter_type, status)
            status_text = "فعال" if status else "غیرفعال"
            await client.send_message(object_guid, f"✅ فیلتر {filter_type} {status_text} شد.")

        if message_text == "ویسکال فعال":
            db.set_voice_call_status(True)
            await client.send_message(object_guid, "📞 ویسکال فعال شد.")
        elif message_text == "ویسکال غیرفعال":
            db.set_voice_call_status(False)
            await client.send_message(object_guid, "🚫 ویسکال غیرفعال شد.")

        if message_text == "پین":
            if message.get("reply_to_message_id"):
                reply_to_message_id = message["reply_to_message_id"]
                try:
                    await client.set_pin_message(object_guid, reply_to_message_id, action="Pin")
                    await client.send_message(object_guid, "✅ پیام با موفقیت پین شد.", reply_to_message_id=message_id)
                except Exception as e:
                    await client.send_message(object_guid, f"خطا در پین کردن پیام: {e}", reply_to_message_id=message_id)
            else:
                await client.send_message(object_guid, "برای پین کردن، روی پیام مورد نظر ریپلای کنید و 'پین' را ارسال کنید.", reply_to_message_id=message_id)
        
        elif message_text == "آنپین":
            if message.get("reply_to_message_id"):
                reply_to_message_id = message["reply_to_message_id"]
                try:
                    await client.set_pin_message(object_guid, reply_to_message_id, action="Unpin")
                    await client.send_message(object_guid, "✅ پیام با موفقیت آنپین شد.", reply_to_message_id=message_id)
                except Exception as e:
                    await client.send_message(object_guid, f"خطا در آنپین کردن پیام: {e}", reply_to_message_id=message_id)
            else:
                await client.send_message(object_guid, "برای آنپین کردن، روی پیام مورد نظر ریپلای کنید و 'آنپین' را ارسال کنید.", reply_to_message_id=message_id)

    if object_guid == user_guid and message_type == "Text" and message_text.startswith("https://rubika.ir/g/"):
        group_link = message_text.strip()
        try:
            await client.join_group(group_link)
            await client.send_message(user_guid, "✅ با موفقیت به گروه مورد نظر جوین شدم!")
        except Exception as e:
            await client.send_message(user_guid, f"❌ خطایی در جوین شدن به گروه رخ داد: {e}")
    elif object_guid == user_guid and message_type == "Text":
        await client.send_message(user_guid, "لطفاً لینک دعوت گروه را به درستی ارسال کنید (مثال: https://rubika.ir/g/xxxxx).")


    strict_mode = db.get_strict_mode()
    
    if message_type == "Text":
        text_content = message.get("text", "")
        if "rubika.ir/" in text_content or "https://" in text_content or "http://" in text_content:
            if strict_mode:
                is_sender_admin = await client.user_is_admin(object_guid=object_guid, user_guid=user_guid)
                if not is_sender_admin:
                    await client.ban_group_member(object_guid, user_guid)
                    await client.send_message(object_guid, f"کاربر به دلیل ارسال لینک در حالت سختگیرانه بن شد.")
                    if user_guid in db.data["users"]:
                        del db.data["users"][user_guid]
                        db._save_data()
            else:
                await client.delete_messages(object_guid, [message_id])
                await client.send_message(object_guid, "لینک ارسالی شما حذف شد.")
            return

        if len(text_content) > 1000 or any(char in text_content for char in ['\u200b', '\ufeff']):
            await client.delete_messages(object_guid, [message_id])
            await client.send_message(object_guid, "پیام حاوی کد نامعتبر یا طولانی حذف شد.")
            return

    filter_map = {
        "Gif": "gif",
        "Image": "photo",
        "Voice": "voice",
        "Video": "video"
    }

    if message_type in filter_map and db.get_filter_status(filter_map[message_type]):
        await client.delete_messages(object_guid, [message_id])
        await client.send_message(object_guid, f"ارسال {filter_map[message_type]} مجاز نیست.")
        return

    if message_type == "File" and db.get_filter_status("story") and \
       message.get("file_inline", {}).get("mime") and "video" in message["file_inline"]["mime"] and \
       message.get("metadata", {}).get("is_story"):
        await client.delete_messages(object_guid, [message_id])
        await client.send_message(object_guid, "ارسال استوری مجاز نیست.")
        return

    if message_type == "File" and db.get_filter_status("other_files") and \
       not message.get("metadata", {}).get("is_story"):
        await client.delete_messages(object_guid, [message_id])
        await client.send_message(object_guid, "ارسال سایر فایل‌ها مجاز نیست.")
        return


async def main():
    print("ربات در حال اجرا است. منتظر به‌روزرسانی‌ها...")
    await client.start()
    
if __name__ == "__main__":
    try:
        client.run(main())
    except KeyboardInterrupt:
        print("ربات متوقف شد.")
    except Exception as e:
        print(f"خطای غیرمنتظره در اجرای ربات: {e}")