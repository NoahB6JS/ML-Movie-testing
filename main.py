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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_api_id TEXT UNIQUE,
        title TEXT,
        poster_url TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        movie_id INTEGER,
        status TEXT CHECK(status IN ('liked', 'disliked', 'wishlist')),
        UNIQUE(user_id, movie_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(movie_id) REFERENCES movies(id)
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

def get_user_id(username):
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    db.close()
    return row[0] if row else None

def get_or_create_movie(api_id, title, poster_url):
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO movies (movie_api_id, title, poster_url) VALUES (?, ?, ?)",
                   (api_id, title, poster_url))
    cursor.execute("SELECT id FROM movies WHERE movie_api_id=?", (api_id,))
    movie_id = cursor.fetchone()[0]
    db.commit()
    db.close()
    return movie_id

def set_movie_status(user_id, movie_id, status):
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()
    cursor.execute("""
    INSERT INTO user_movies (user_id, movie_id, status)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id, movie_id)
    DO UPDATE SET status=excluded.status
    """, (user_id, movie_id, status))
    db.commit()
    db.close()

def get_user_movies(user_id, status):
    db = sqlite3.connect("movies.db")
    cursor = db.cursor()
    cursor.execute("""
    SELECT m.title, m.poster_url 
    FROM movies m 
    JOIN user_movies um ON m.id = um.movie_id 
    WHERE um.user_id=? AND um.status=?
    """, (user_id, status))
    rows = cursor.fetchall()
    db.close()
    return rows

# ---------------- APP ---------------- #
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Movie App")
        self.state("zoomed")  # Fullscreen

        setup_database()
        self.login_screen()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ---------------- Login ---------------- #
    def login_screen(self):
        self.clear()
        ctk.CTkLabel(self, text="Login", font=("Arial", 30, "bold")).pack(pady=40)
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=300)
        self.username_entry.pack(pady=10)
        ctk.CTkButton(self, text="Login", command=self.login, width=200).pack(pady=5)
        ctk.CTkButton(self, text="Create Account", command=self.create_account, width=200).pack(pady=5)
        self.message = ctk.CTkLabel(self, text="", font=("Arial", 14))
        self.message.pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        if user_exists(username):
            self.user_id = get_user_id(username)
            self.home_screen(username)
        else:
            self.message.configure(text="User not found")

    def create_account(self):
        username = self.username_entry.get()
        if create_user(username):
            self.message.configure(text="Account created!")
        else:
            self.message.configure(text="Username already exists")

    # ---------------- Home Screen ---------------- #
    def home_screen(self, username):
        self.clear()
        ctk.CTkLabel(self, text=f"Hello, {username}!", font=("Arial", 30, "bold")).pack(pady=20)

        top_bar = ctk.CTkFrame(self, fg_color="#1e293b")
        top_bar.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(top_bar, text="Discover", command=lambda: self.home_screen(username)).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(top_bar, text="Rate", command=lambda: None).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkButton(top_bar, text="Account", command=lambda: self.account_page(username)).grid(row=0, column=2, padx=10, pady=10)

        self.scrollable_frame = self.create_scrollable_frame()
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Add movies
        for _ in range(20):
            self.add_movie_widget(self.scrollable_frame)

    def create_scrollable_frame(self):
        container = ctk.CTkFrame(self, fg_color="#0f172a")
        canvas = ctk.CTkCanvas(container, bg="#0f172a", highlightthickness=0)
        scroll_frame = ctk.CTkFrame(canvas, fg_color="#0f172a")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_frame.bind("<Configure>", on_frame_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        container.scroll_frame = scroll_frame
        return container

    def add_movie_widget(self, parent):
        title, poster_url = get_popular_movie()
        frame = ctk.CTkFrame(parent.scroll_frame, fg_color="#1e293b", corner_radius=10)
        frame.pack(pady=10, padx=10, fill="x")

        movie = {"id": title, "title": title, "poster": poster_url}  # Use title as dummy id

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

        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10)

        ctk.CTkLabel(info_frame, text=title, font=("Arial", 18, "bold")).pack(anchor="nw", pady=10)

        ctk.CTkButton(info_frame, text="Like", command=lambda m=movie: self.like_movie(m)).pack(pady=5)
        ctk.CTkButton(info_frame, text="Dislike", command=lambda m=movie: self.dislike_movie(m)).pack(pady=5)
        ctk.CTkButton(info_frame, text="Wishlist", command=lambda m=movie: self.wishlist_movie(m)).pack(pady=5)

    # ---------------- Movie Status ---------------- #
    def like_movie(self, movie):
        movie_id = get_or_create_movie(movie["id"], movie["title"], movie["poster"])
        set_movie_status(self.user_id, movie_id, "liked")

    def dislike_movie(self, movie):
        movie_id = get_or_create_movie(movie["id"], movie["title"], movie["poster"])
        set_movie_status(self.user_id, movie_id, "disliked")

    def wishlist_movie(self, movie):
        movie_id = get_or_create_movie(movie["id"], movie["title"], movie["poster"])
        set_movie_status(self.user_id, movie_id, "wishlist")

    # ---------------- Account Page ---------------- #
    def account_page(self, username):
        self.clear()
        ctk.CTkLabel(self, text=f"{username}'s Account", font=("Arial", 30, "bold")).pack(pady=20)

        top_bar = ctk.CTkFrame(self, fg_color="#1e293b")
        top_bar.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(top_bar, text="Discover", command=lambda: self.home_screen(username)).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(top_bar, text="Rate", command=lambda: None).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkButton(top_bar, text="Account", command=lambda: self.account_page(username)).grid(row=0, column=2, padx=10, pady=10)

        self.scrollable_frame = self.create_scrollable_frame()
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for status, color in [("liked", "#14b8a6"), ("disliked", "#ef4444"), ("wishlist", "#facc15")]:
            ctk.CTkLabel(self.scrollable_frame.scroll_frame, text=status.capitalize(), font=("Arial", 24, "bold"), text_color=color).pack(anchor="w", pady=10)
            movies = get_user_movies(self.user_id, status)
            for title, poster_url in movies:
                frame = ctk.CTkFrame(self.scrollable_frame.scroll_frame, fg_color="#1e293b", corner_radius=10)
                frame.pack(pady=5, fill="x")
                photo = None
                if poster_url and poster_url != "N/A":
                    try:
                        response = requests.get(poster_url)
                        img_data = response.content
                        img = Image.open(BytesIO(img_data))
                        img = img.resize((80, 120))
                        photo = ImageTk.PhotoImage(img)
                    except:
                        pass
                poster_label = ctk.CTkLabel(frame, image=photo, text="")
                poster_label.image = photo
                poster_label.pack(side="left", padx=10, pady=10)
                ctk.CTkLabel(frame, text=title, font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()