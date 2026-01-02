import customtkinter as ctk
import sqlite3
from api_movie import get_popular_movie  
import requests
from io import BytesIO
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- DATABASE ---------------- #

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

# ---------------- APP ---------------- #

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("450x600")
        self.title("Movie System")

        setup_database()
        self.login_screen()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # -------- LOGIN SCREEN -------- #
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

    # -------- HOME SCREEN (Scrollable Movie Feed) -------- #
    def home_screen(self, username):
        self.clear()

        ctk.CTkLabel(self, text=f"Hello, {username}!", font=("Arial", 24)).pack(pady=10)
        
        ctk.CTkButton(self, text="Discover").pack(pady=10)
        ctk.CTkButton(self, text="Rate").pack(pady=10)
        ctk.CTkButton(
            self,
            text="Account",
            command=lambda: self.account_page(username)).pack(pady=10)
        # Canvas + Scrollbar for scrolling
        canvas = ctk.CTkCanvas(self, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Frame inside canvas to hold movie widgets
        self.inner_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Add multiple movies
        for i in range(15):  
            self.add_movie_widget(self.inner_frame)

       
        self.inner_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def add_movie_widget(self, parent):
        title, poster_url = get_popular_movie()

        frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="#2b2b2b")
        frame.pack(pady=10, padx=10, fill="x")

        
        photo = None
        if poster_url and poster_url != "N/A":
            try:
                response = requests.get(poster_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((120, 180))
                photo = ImageTk.PhotoImage(img)
            except:
                pass

        poster_label = ctk.CTkLabel(frame, image=photo, text="")
        poster_label.image = photo  
        poster_label.pack(side="left", padx=10, pady=10)

        # Title
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10)

        title_label = ctk.CTkLabel(info_frame, text=title, font=("Arial", 16))
        title_label.pack(anchor="nw", pady=10)
        #------------Like button
        like_button = ctk.CTkButton(info_frame, text="Like", command=lambda t=title: self.like_movie(t))
        like_button.pack(anchor="nw", pady=10)
        #------------Dislike button
        dislike_button = ctk.CTkButton(info_frame, text="Dislike", command=lambda t=title: self.like_movie(t))
        dislike_button.pack(anchor="nw", pady=10)
        #------------watchlist button
        watchlater_button = ctk.CTkButton(info_frame, text="Watch later", command=lambda t=title: self.like_movie(t))
        watchlater_button.pack(anchor="nw", pady=10)
        

    def like_movie(self, title):
        print(f"You liked: {title}")
        
    def account_page(self, username):
        self.clear()

        ctk.CTkButton(
            self,
            text="Discover",
            command=lambda: self.home_screen(username)
        ).pack(pady=10)

        ctk.CTkButton(self, text="Rate").pack(pady=10)
        ctk.CTkButton(self, text="Account").pack(pady=10)
    
    

# ---------------- DEBUG FUNCTION ---------------- #
def show_account_data():
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    db.close()


if __name__ == "__main__":
    app = App()
    app.mainloop()
    show_account_data()