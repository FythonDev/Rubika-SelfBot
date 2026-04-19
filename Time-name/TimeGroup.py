#edit line 7,8

from pyrubi import Client
import time
import datetime
import pytz

GUID = "guide group" 
BASE_TITLE = "name group" 
client = Client("FythonDev")

def update_group_title():
    try:
        tehran_time = datetime.datetime.now(pytz.timezone("Asia/Tehran"))
        current_time = tehran_time.strftime("%H:%M")
        
    
        fancy_numbers = str.maketrans("0123456789")
        fancy_time = current_time.translate(fancy_numbers)
        
        client.edit_group_info(object_guid=GUID, title=f"{BASE_TITLE} {fancy_time}")
        print(f"update: {BASE_TITLE} {current_time} ({tehran_time.strftime('%Y-%m-%d %H:%M')})")
    except Exception as e:
        print(f" error: {e}")

print("Bot is Starting...")

while True:
    update_group_title()
    time.sleep(1)
bot.run()
