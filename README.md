# Telepound

* Connection of multiple clients on a server possible.
* Abruptly closing any client does not affect remaining network.
* Abruptly closing any client closes all clients connected.
* First enter the message, then the user you want to send to.
* If no file is to be attached, directly press enter.
* Sending Files is not working right now due to some reason. Program struck at client.py:89 sendString = json.dumps(toSend)
* All Communication is via json object, not string.
* date and time are also send and printed.


## Reference for multi-threading of mulitple clients on a server:
* https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/

## Reference for Client input handling:
* https://stackoverflow.com/questions/68474167/how-to-replace-the-keyboardinterrupt-command-for-another-key

## Reference for date-time handling:
* https://stackoverflow.com/questions/26276906/python-convert-seconds-from-epoch-time-into-human-readable-time

## General Reference
* https://www.youtube.com/c/sentdex/search?query=socket%20chat%20room