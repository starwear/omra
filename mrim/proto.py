# -*- coding: utf-8 -*-

# OMRA by Starwear

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
    # LPS -> password (md5, clear in 5.6)
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
        # LPS -> phone number (ex. 70000000000)
        # LPS -> xstatus meaning
        # LPS -> xstatus title (utf-16-le)
        # LPS -> xstatus description (utf-16-le)
        # LPS -> com_support (ex. 0x3FF)
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

### Поиск
MRIM_CS_WP_REQUEST = 0x1029 # C -> S
    # UL -> field
MRIM_CS_WP_REQUEST_PARAM_USER = 0
MRIM_CS_WP_REQUEST_PARAM_DOMAIN = 1
    # LPS -> value
MRIM_CS_ANKETA_INFO = 0x1028 # S -> C
    # UL -> status
MRIM_ANKETA_INFO_STATUS_OK = 1
MRIM_ANKETA_INFO_STATUS_NOUSER = 0
MRIM_ANKETA_INFO_STATUS_DBERR = 2
MRIM_ANKETA_INFO_STATUS_RATELIMERR = 3
    # UL -> fields num
    # UL -> max rows
    # UL -> server time (unix)
    # Fields
    # Values

### Работа с контактами
MRIM_CS_ADD_CONTACT = 0x1019 # C -> S
    # UL -> flags
CONTACT_FLAG_REMOVED = 0x00000001 # Не применяется к MRIM_CS_ADD_CONTACT
CONTACT_FLAG_GROUP = 0x00000002
CONTACT_FLAG_GROUP_ALT = [0x1000002, 0x2000002, 0x3000002, 0x4000002, 0x5000002, 0x6000002, 0x7000002, 0x8000002, 0x9000002, 0xa000002, 0xb000002, 0xc000002, 0xd000002, 0xe000002, 0xf000002, 0x10000002]
CONTACT_FLAG_INVISIBLE = 0x00000004 # "Я всегда невидим для"
CONTACT_FLAG_VISIBLE = 0x00000008 # "Я всегда видим для"
CONTACT_FLAG_IGNORE = 0x00000010 # Контакт в списоке игнорируемых
CONTACT_FLAG_SHADOW	= 0x00000020
    # UL -> group id (unused if contact is group)
    # LPS -> contact
    # LPS -> name
    # LPS -> unused
MRIM_CS_ADD_CONTACT_ACK = 0x101A # S -> C
    # UL -> status
CONTACT_OPER_SUCCESS = 0x0000
CONTACT_OPER_ERROR = 0x0001
CONTACT_OPER_INTERR = 0x0002
CONTACT_OPER_NO_SUCH_USER = 0x0003
CONTACT_OPER_INVALID_INFO = 0x0004
CONTACT_OPER_USER_EXISTS = 0x0005
CONTACT_OPER_GROUP_LIMIT = 0x6
    # UL -> contact id or -1 if status is not OK

### Сообщения
MRIM_CS_MESSAGE = 0x1008 # C -> S
    # UL -> flags
MESSAGE_FLAG_OFFLINE = 0x00000001
MESSAGE_FLAG_NORECV = 0x00000004
MESSAGE_FLAG_AUTHORIZE = 0x00000008 # X-MRIM-Flags: 00000008
MESSAGE_FLAG_SYSTEM = 0x00000040
MESSAGE_FLAG_RTF = 0x00000080
MESSAGE_FLAG_CONTACT = 0x00000200
MESSAGE_FLAG_NOTIFY = 0x00000400
MESSAGE_FLAG_MULTICAST = 0x00001000
    # LPS -> to
    # LPS -> message
    # LPS -> rtf-formatted message
MRIM_CS_MESSAGE_ACK = 0x1009 # S -> C
    # UL -> msg_id
    # UL -> flags
    # LPS -> from
    # LPS -> message
    # LPS -> rtf-formatted message
MRIM_CS_MESSAGE_RECV = 0x1011 # C -> S
    # LPS -> from
    # UL -> msg_id
MRIM_CS_MESSAGE_STATUS = 0x1012 # S -> C
    # UL -> status
MESSAGE_DELIVERED = 0x0000 # Message delivered directly to user
MESSAGE_REJECTED_NOUSER = 0x8001 # Message rejected - no such user
MESSAGE_REJECTED_INTERR = 0x8003 # Internal server error
MESSAGE_REJECTED_LIMIT_EXCEEDED = 0x8004 # Offline messages limit exceeded
MESSAGE_REJECTED_TOO_LARGE = 0x8005 # Message is too large
MESSAGE_REJECTED_DENY_OFFMSG = 0x8006 # User does not accept offline messages

### Авторизация контактов
MRIM_CS_AUTHORIZE = 0x1020 # C -> S
    # LPS -> user
MRIM_CS_AUTHORIZE_ACK = 0x1021 # S -> C
    # LPS -> user

### Игры
MRIM_CS_GAME = 0x1035 # C <-> S
    # LPS -> to / from email
    # UL -> session id
    # UL -> game msg
    # UL -> msg id 
    # UL -> time send
    # LPS -> data