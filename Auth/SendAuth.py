#Send session to Rubika
#Line 8, instead of guide, put your ID (str)
from pyrubi import Client
from pyrubi.types import Message

app = Clinet("FythonDev", platform="android")

app.send_message(app.get_me(), "guide")
