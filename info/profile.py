```Profile bug using the pyrubi library.
Put the addresses of two files in lines 4 and 5, and your account ID (GUID) in line 3```

from pyrubi import Client
app = Client("Fythondev")
guid = "guide"
asli = "original"
kover = "cover"
app.upload_avatar(guid,kover,asli)
