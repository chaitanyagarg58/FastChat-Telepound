# Telepound

## Contributions
    - We did not completely distribute work. This was because we tried to do that, but then the codes were not compatible with each other and required double the time to combine the features, so we resorted to doing 1 thing together instead of 3 things seperately.

    - We discussed the approach to add the features and whoever was free contributed in impliment the approach.

    - Chaitanya Garg (210050039) was like the head of group, he contributed in all features.
    - Jennisha Agrawal (210050039) contributed in Encryption and Undelivered messages.
    - Atharv Kshirsagar (210050025) contributed in Encryption, Groups and SignUp/login.

## Running Instructions
    - Database dump has been added in db.sql
    - The postgres server is setup and running as required.
    - Run loadbalancer.py will a argument of port. For example port 5000: 'python3 loadbalancer.py 5000'. User this same port for other files.
    - Run as many servers as you want by: 'python3 server.py 5000'
    - Run as many clients as you want by: 'python3 client.py 5000'

## Features added
    - SignUp/Login Authentication.
    - Database to store information securely.
    - E2E encryption of files and messages.
    - Storing and managing messages for offline clients
    - Load Balancing on multiple servers.
    - Group Chat.

## Technologies Used:
    - socket library is used for communication and basically everything.
    - select library is used for managing multiple processes at same time.
    - bcrypt library is used to one way encrypt (not decryptable) the password while storing in database and checking if password is correct on login.
    - Postgresql is used to create and manage database.
    - rsa library is used for E2E encryption.
    - to store private keys in secure/encrypted way, and to retreive them when needed, cryptography library is used.
    - General libraries such as base64, json, time, datetime, sys, os are used wherever needed.

## Details
    - Some Keywords ('CREATE GROUP', 'ADD MEMBER', 'REMOVE MEMBER', 'LEAVE GROUP', 'EXIT') are preserved and can not be used as user or group name.
    - username and groupname are unique ids and can not be repeated.
    
    - UI is pretty informative and should be easy to use.
    - First enter the username/groupname you want to send message to other specify command to create/modify group as in preserved keywords.
    - If no file is to be attached, directly press enter.
    - All Communication is via json object, not string.
    - date and time are also send and printed.

    - User passwords are stored in salted and hashed form in the database.

    - Messages/file data/file name are all E2E Encrypted for individual as well as group chats.

    - In groups, there is only 1 admin, who can modify group, who is the creator of the group as well.
    - A client can leave group as well.
    - If the admin leaves the group or removes himself, the group is deleted.

    - Database has 2 roles:
        1. postgres: default role, used as server, its password used is 'telepoundServer'.
        2. client: role created to allow only SELECT command to users, its password used is 'telepoundClient'.

    - Database has 3 tables:
        1. clientinfo: username (text), password (text), public_{n,e} (text), private_{d,p,q}, salt (text)
            - password is salted and hashed.
            - The public_n and public_e define the public key of this client, this are stored as it is, so anyone can access these. Anyone wanting to send a message to this client using these values to encrypt the data
            - salt is randomly generated bitstring for encrypt of private keys of this user as mentioned nin next point.
            - The private_{d,p,q} are private keys of this client which are neccessary for decrypt the messages send to it. These keys should not be readable to anyone but this client. So these keys are symmetrically encrypted by using the salt to hash this users password, then using that as a key(k) to encrypt the private_{d,p,q} keys. The key k is also used to decrypt the private keys when loging in, but since no-one else has password of this user, they cannot know the key k, and hence can not read the private keys.

        2. groupinfo: groupname (text), admin (text), members (TEXT[])
            - admin is the username of the creator of group, only he can modify group.
            - members is an array containing username of all members of the group.

        3. undelivered: time (double precision), touser (text), message (jsonb)
            - Stores undelivered massages.

## References

- multi-threading of mulitple clients on a server:
    * https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/

- Client input handling:
    * https://stackoverflow.com/questions/68474167/how-to-replace-the-keyboardinterrupt-command-for-another-key

- date-time handling:
    * https://stackoverflow.com/questions/26276906/python-convert-seconds-from-epoch-time-into-human-readable-time

- sending images:
    * https://stackoverflow.com/questions/50266553/send-json-with-image-as-bytes-using-websocket

- RSA Encryption:
    * https://www.section.io/engineering-education/rsa-encryption-and-decryption-in-python/
    * https://stackoverflow.com/questions/63423868/using-supplied-key-to-encrypt-text-python
    * https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet

- General Reference/ Starter Reference:
    * https://www.youtube.com/c/sentdex/search?query=socket%20chat%20room
