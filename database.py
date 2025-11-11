# database.py
import sqlite3
from datetime import datetime
import os

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS classes (
                 id INTEGER PRIMARY KEY,
                 name TEXT UNIQUE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                 id INTEGER PRIMARY KEY,
                 name TEXT,
                 class_id INTEGER,
                 image_path TEXT,
                 FOREIGN KEY(class_id) REFERENCES classes(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                 id INTEGER PRIMARY KEY,
                 student_id INTEGER,
                 date TEXT,
                 time TEXT,
                 FOREIGN KEY(student_id) REFERENCES students(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT UNIQUE,
                 password TEXT)''')
    
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
              ("admin", "admin123"))
    
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_NAME)