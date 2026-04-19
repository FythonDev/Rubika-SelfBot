#report acc, group, channel

from rubika import Bot
from rubika.configs import reports
from time import sleep as sp
from random import choice


bot = Bot("FythonDev")

guid = input("inter your target guid : ")
ran = int(input("inter your range : "))
a = 0
for i in range(ran):
    bot.reportChat(guid,reports.PORNOGRAPHY)
    print(f"report pornografy {a}")
    a+=1
    sp(.3)
b = 0
for i in range(ran):
    bot.reportChat(guid,reports.FISHING)
    print(f"report fishing {b}")
    b+=1
    sp(.3)
c = 0
for i in range(ran):
    bot.reportChat(guid,reports.SPAM)
    print(f"report spam {c}")
    c+=1
    sp(.3)
d = 0
for i in range(ran):
    bot.reportChat(guid,reports.COPYRIGHT)
    print(f"report copyrite {d}")
    d+=1
    sp(.3)
e = 0
for i in range(ran):
    bot.reportChat(guid,reports.VIOLENCE)
    print(f"report violence {e}")
    e+=1
    sp(.3)
f = 0
list_f = ["ارسال گیف مستهجن ","مالکیت گروه و کانال غیر اخلاقی","ساخت گروه مختلط","استفاده از کلمه های رکیک و زننده","حرف های تحدید آمیز"]
for i in range(ran):
    list_f = choice(list_f)
    bot.reportChat(guid,reports.OTHER,list_f)
    f+=1
    sp(.3)
print("*" * 10)
print("  done !")
input("\n\nexit??\n\n")
