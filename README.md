# Telepound

* Connection of multiple clients on a server possible.
<!-- * Abruptly closing any client does not affect remaining network. -->
<!-- * Abruptly closing any client closes all clients connected. -->
* First enter the message, then the user you want to send to.
* If no file is to be attached, directly press enter.
* All Communication is via json object, not string.
* date and time are also send and printed.

* Modularised client.py keeping all the same functionalities.

* Authentication of users has been added. 
* User login and sign-up possible.
* User passwords are stored in salted and hashed form in the database.

* Database has 2 tables:
    1. clientinfo: username (text), password (text), public_key (text), status (boolean), ip (text), port (integer)
        - password is salted and hashed.
        - public_key is the rsa public key (not used yet)
        - status is a boolean telling if given client is online
        - ip and port are the socket address for the client (also not used yet)

    2. undelivered: time (double precision), touser (text), message (jsonb)
        - Supposed to store undelivered massages.
        - not used yet.

* **Abrupt closing of server or client needs to be handled.**

## Reference for multi-threading of mulitple clients on a server:
* https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/

## Reference for Client input handling:
* https://stackoverflow.com/questions/68474167/how-to-replace-the-keyboardinterrupt-command-for-another-key

## Reference for date-time handling:
* https://stackoverflow.com/questions/26276906/python-convert-seconds-from-epoch-time-into-human-readable-time

## Reference for sending images:
* https://stackoverflow.com/questions/50266553/send-json-with-image-as-bytes-using-websocket

## General Reference
* https://www.youtube.com/c/sentdex/search?query=socket%20chat%20room