# shhh — a tiny encrypted-feel chat app

A full-stack toy chat application built with **KivyMD** (Material-Design Python UI) on the client and a **raw TCP socket server** on the backend, with **SQLite** for user accounts and message history.

> Built end-to-end as a learning project covering: cross-platform GUI layout, real-time bidirectional sockets, threaded message handling, and persistent storage.

## Architecture

```
┌────────────────────────┐                  ┌──────────────────────┐
│  KivyMD client (GUI)   │                  │  chat_server.py      │
│  - LoginScreen         │  TCP 127.0.0.1   │  - threaded per-user │
│  - ChatScreen          │ ◄──────────────► │  - SQLite history    │
│  - ScreenManager nav   │     :8081        │  - broadcast fan-out │
└────────────────────────┘                  └──────────────────────┘
         │                                            │
         ▼                                            ▼
   users.db (accounts)                       chat_messages.db (log)
```

The client opens a long-lived socket on entering the chat screen, spawns a background thread to poll for inbound messages, and pushes UI updates back onto the Kivy event loop via `Clock.schedule_once` (the only thread-safe way to mutate Kivy widgets).

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1 — start the server
python chat_server.py

# Terminal 2 — start the client (and a third for a second user)
python main.py
```

Sign up with any username/password, log in, head to the Chat tab, and start sending messages. Open a second client to chat with yourself.

## Files

| File | Purpose |
|---|---|
| `main.py` | KivyMD app: screens, login/signup, socket client |
| `chat_server.py` | Threaded socket server with SQLite persistence |
| `login.kv` / `chat.kv` / `login_success.kv` | KV-language UI layouts |
| `Cougar Paw CBSS.png` | Logo asset shown on the login screen |

## Security notes

- Passwords are stored as **PBKDF2 hashes** (via `werkzeug.security.generate_password_hash`), not plaintext.
- All SQL queries use **parameter binding** — no string interpolation, so no SQL injection.
- The socket connection is plaintext TCP — for a real deployment you'd wrap it in TLS (`ssl.wrap_socket`) and add a proper handshake/auth message instead of relying on the client to send its own username post-login.

## Future ideas

- End-to-end encryption (X25519 key exchange + AES-GCM per message)
- Multi-room support (currently every connected client sees every message)
- Mobile build via `buildozer`
