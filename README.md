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

* E2E Encryption has been added.
* Image and Files are also encrypted.

* Database has 2 roles:
    1. postgres: default role, used as server.
    2. client: role created granted power as: 'Grant client to postgres;'.

* Database has 2 tables:
    1. clientinfo: username (text), password (text), status (boolean), ip (text), port (integer), public_{n,e} (text), private_{d,p,q}, salt (text)
        - password is salted and hashed.
        - status is a boolean telling if given client is online
        - ip and port are the socket address for the client (not used yet)
        - The public_n and public_e define the public key of this client, this are stored as it is, so anyone can access these. Anyone wanting to send a message to this client using these values to encrypt the data
        - salt is randomly generated bitstring for encrypt of private keys of this user as mentioned nin next point.
        - The private_{d,p,q} are private keys of this client which are neccessary for decrypt the messages send to it. These keys should not be readable to anyone but this client. So these keys are symmetrically encrypted by using the salt to hash this users password, then using that as a key(k) to encrypt the private_{d,p,q} keys. The key k is also used to decrypt the private keys when loging in, but since no-one else has password of this user, they cannot know the key k, and hence can not read the private keys.

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

## RSA Encryption:
* https://www.section.io/engineering-education/rsa-encryption-and-decryption-in-python/
* https://stackoverflow.com/questions/63423868/using-supplied-key-to-encrypt-text-python
* https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet

## General Reference:
* https://www.youtube.com/c/sentdex/search?query=socket%20chat%20room
