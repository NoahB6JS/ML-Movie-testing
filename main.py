import customtkinter as ctk
import sqlite3
from api_movie import get_popular_movie


def setup_database():
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )
    """)

    db.commit()
    db.close()


def create_user(username):
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        db.commit()
        success = True
    except:
        success = False

    db.close()
    return success


def user_exists(username):
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    db.close()
    return user is not None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("400x300")
        self.title("Movie System")

        setup_database()
        self.login_screen()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()


    def login_screen(self):
        self.clear()

        ctk.CTkLabel(self, text="Login", font=("Arial", 24)).pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        ctk.CTkButton(self, text="Login", command=self.login).pack(pady=5)
        ctk.CTkButton(self, text="Create Account", command=self.create_account).pack(pady=5)

        self.message = ctk.CTkLabel(self, text="")
        self.message.pack(pady=10)

    def login(self):
        username = self.username_entry.get()

        if user_exists(username):
            self.home_screen(username)
        else:
            self.message.configure(text="User not found")

    def create_account(self):
        username = self.username_entry.get()

        if create_user(username):
            self.message.configure(text="Account created!")
        else:
            self.message.configure(text="Username already exists")


    def home_screen(self, username):
        self.clear()

        ctk.CTkLabel(
            self,
            text=f"Hello, {username}",
            font=("Arial", 24)
        ).pack(pady=100)
        
        




def show_account_data():
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    db.close()


app = App()
app.mainloop()
show_account_data()