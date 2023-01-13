import socket
import sqlite3
import threading

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from werkzeug.security import check_password_hash, generate_password_hash

USERS_DB = "users.db"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8081


def _ensure_users_table() -> None:
    """Create the users table on first launch if it doesn't exist."""
    conn = sqlite3.connect(USERS_DB)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   username TEXT PRIMARY KEY,
                   password TEXT NOT NULL
               )"""
        )
        conn.commit()
    finally:
        conn.close()


class LoginScreen(Screen):
    pass


class ChatScreen(Screen):
    def on_enter(self, *args):
        self.connect_to_server()
        threading.Thread(target=self.retrieve_past_messages, daemon=True).start()

    def retrieve_past_messages(self):
        while True:
            try:
                message = self.client.recv(4096).decode("utf-8")
                if message:
                    Clock.schedule_once(lambda dt, m=message: self.update_chat_output(m))
            except Exception as e:
                print(f"Error retrieving messages: {e}")
                break

    def update_chat_output(self, message: str):
        self.ids.chat_output.text += message

    def connect_to_server(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((SERVER_HOST, SERVER_PORT))
        self.client.send(self.username.encode("utf-8"))

    def disconnect_from_server(self):
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing socket connection: {e}")


class LoginSuccessScreen(Screen):
    pass


class MainApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        _ensure_users_table()
        Builder.load_file("login.kv")
        Builder.load_file("login_success.kv")
        Builder.load_file("chat.kv")
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(LoginSuccessScreen(name="login_success"))
        return sm

    def signup(self, username: str, password: str) -> None:
        if not username or not password:
            print("Username and password are required.")
            return
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect(USERS_DB)
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password_hash),
            )
            conn.commit()
            print(f"Signed up: {username}")
        except sqlite3.IntegrityError:
            print(f"Username '{username}' is already taken.")
        finally:
            conn.close()

    def login(self, username: str, password: str) -> None:
        conn = sqlite3.connect(USERS_DB)
        try:
            row = conn.execute(
                "SELECT password FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        finally:
            conn.close()

        if row is not None and check_password_hash(row[0], password):
            print("Login successful")
            self.root.get_screen("login_success").username = username
            self.root.current = "login_success"
        else:
            print("Login failed")

    def clear_credentials(self) -> None:
        conn = sqlite3.connect(USERS_DB)
        try:
            conn.execute("DELETE FROM users")
            conn.commit()
        finally:
            conn.close()

    def send_message(self, message: str) -> None:
        try:
            chat_screen = self.root.get_screen("chat")
            chat_screen.client.send(message.encode("utf-8"))
            chat_screen.ids.chat_input.text = ""
        except Exception as e:
            print(f"Error sending message: {e}")

    def switch_to_chat(self, username: str) -> None:
        self.root.transition.direction = "left"
        self.root.get_screen("chat").username = username
        self.root.current = "chat"

    def on_stop(self) -> None:
        try:
            self.root.get_screen("chat").disconnect_from_server()
        except Exception as e:
            print(f"Error during shutdown: {e}")


if __name__ == "__main__":
    MainApp().run()
