# chat_server.py
import socket
import threading
import sqlite3

HOST = '127.0.0.1'
PORT = 8081

clients = {}

# Use a separate SQLite database for chat messages
CHAT_DB_NAME = 'chat_messages.db'

def create_table():
    conn = sqlite3.connect(CHAT_DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT)''')
    conn.commit()
    conn.close()

def store_message(username, message):
    conn = sqlite3.connect(CHAT_DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

def retrieve_messages():
    conn = sqlite3.connect(CHAT_DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM messages")
    messages = c.fetchall()
    conn.close()
    return messages

def handle_client(client_socket, username):
    past_messages = retrieve_messages()
    for msg in past_messages:
        formatted_message = f"{msg[1]}: {msg[2]}\n"  # Add a newline character at the end of each message
        client_socket.send(formatted_message.encode('utf-8'))

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            broadcast(username, message)
            store_message(username, message)
        except Exception as e:
            print(f"Error: {e}")
            break

    remove_client(username, client_socket)
    client_socket.close()

def broadcast(username, message):
    for client in clients:
        try:
            client.send(f"{username}: {message}".encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting to {client}: {e}")
            remove_client(clients[client], client)

def remove_client(username, client_socket):
    del clients[client_socket]
    print(f"Connection closed for {username}")

def start_server():
    create_table()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[*] Server listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        username = client_socket.recv(1024).decode('utf-8')
        clients[client_socket] = username

        print(f"[*] {username} connected from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, username))
        client_handler.start()


if __name__ == "__main__":
    start_server()
