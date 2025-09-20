# -*- coding: utf-8 -*-

# OMRA by PostDevelopers

### Команды протокола

### Приветствие
MRIM_CS_HELLO = 0x1001 # C -> S
    # empty
MRIM_CS_HELLO_ACK = 0x1002 # S -> C
    # empty

### SSL
MRIM_CS_SSL = 0x1086 # C -> S
    # empty
MRIM_CS_SSL_ACK = 0x1087 # S -> C
    # empty

### Авторизация
MRIM_CS_LOGIN = 0x1003 # C -> S
    # LPS -> login
    # LPS -> password
MRIM_CS_LOGIN2 = 0x1038 # C -> S
    # LPS -> login
    # LPS -> password
    # UL -> status
    # LPS -> client info
MRIM_CS_LOGIN3 = 0x1078 # C -> S
    # LPS -> login
    # LPS -> password (md5)
    # DWORD -> ???
    # LPS -> version
    # LPS -> locale
    # DWORD -> ???
    # DWORD -> ???
    # LPS -> ??? geo-list
    # LPS -> version2
    # for ;;
        # DWORD[2] -> id_argument
        # DWORD -> ???
        # DWORD -> data
MRIM_CS_LOGIN_ACK = 0x1004 # S -> C
    # empty
MRIM_CS_LOGIN_REJ = 0x1005 # S -> C
    # empty
MRIM_CS_USER_INFO = 0x1015 # S -> C
    # KEY + VALUE
    # LPS -> MESSAGES.TOTAL (windows-1251) + LPS -> total messages in mailbox (utf-16-le)
    # LPS -> MESSAGES.UNREAD (windows-1251) + LPS -> unread messages in mailbox (utf-16-le)
    # LPS -> MRIM.NICKNAME (windows-1251) + LPS -> nickname (utf-16-le)
    # LPS -> client.endpoint (windows-1251) + LPS -> user's ip:port (utf-16-le) 
MRIM_CS_CONTACT_LIST2 = 0x1037 # S -> C
    # UL -> status
GET_CONTACTS_OK = 0x0000
GET_CONTACTS_ERROR = 0x0001
GET_CONTACTS_INTERR = 0x0002
    # UL -> groups number
    # LPS -> groups mask (us)
    # LPS -> contacts mask (uussuussssusuuusssssu)
    # Groups
        # UL -> flags (0)
        # LPS -> group name (utf-16-le)
    # Contacts
        # UL -> flags
        # UL -> group id
        # LPS -> email
        # LPS -> nickname (utf-16-le)
        # UL -> authorization (0 - authorized, 1 - deauthorized)
        # UL -> status (num)
        # LPS -> phone number (ex. +70000000000)
        # LPS -> xstatus meaning
        # LPS -> xstatus title (utf-16-le)
        # LPS -> xstatus description (utf-16-le)
        # LPS -> hide client (ex. 0x3FF or -1)
        # LPS -> user agent (formated string) 
        # UL -> ???
        # UL -> ???
        # UL -> ???
        # LPS -> microblog
        # LPS -> ???
        # LPS -> ???
        # LPS -> ???
        # LPS -> ???
        # UL -> ???

### Keep-Alive
MRIM_CS_PING = 0x1006 # C -> S
    # empty

### Статус
MRIM_CS_CHANGE_STATUS = 0x1022 # C -> S
    # UL -> new status (num)
    # LPS -> xstatus_meaning
    # LPS -> xstatus_title | unicode
    # LPS -> xstatus_description | unicode
    # UL -> com_support (0x03FF)
MRIM_CS_USER_STATUS = 0x100F # S -> C
    # UL -> status
    # LPS -> xstatus meaning
    # LPS -> xstatus title | unicode
    # LPS -> xstatus description | unicode
    # LPS -> user email
    # UL -> com support
    # LPS -> user_agent