# dashboard.py
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import os
import pandas as pd
from datetime import datetime, time
from PIL import Image, ImageTk

from database import init_db, get_conn
from core_recognition import FaceRecognizer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TeacherDashboard:
    def __init__(self):
        print("[TEACHER] Starting Smart Attendance...")
        init_db()
        self.root = ctk.CTk()
        self.root.title("Teacher Attendance Dashboard")
        self.root.geometry("1400x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.recognizer = None
        self.cap = None
        self.is_running = False
        self.current_user = None
        self.frame_queue = []  # GUI-safe frame buffer

        threading.Thread(target=self.init_recognizer, daemon=True).start()
        self.login_screen()

    def init_recognizer(self):
        try:
            self.recognizer = FaceRecognizer()
            print(f"[TEACHER] Loaded {len(self.recognizer.known_encodings)} students.")
        except Exception as e:
            messagebox.showerror("Error", f"Recognizer failed: {e}")

    # ==================== LOGIN ====================
    def login_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        frame = ctk.CTkFrame(self.root)
        frame.pack(expand=True, fill="both", padx=300, pady=250)

        ctk.CTkLabel(frame, text="Teacher Login", font=("Arial", 32)).pack(pady=30)
        self.user_entry = ctk.CTkEntry(frame, placeholder_text="Username", width=300)
        self.user_entry.pack(pady=12)
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300)
        self.pass_entry.pack(pady=12)
        ctk.CTkButton(frame, text="Login", width=200, command=self.login).pack(pady=20)

    def login(self):
        if self.user_entry.get() == "admin" and self.pass_entry.get() == "admin123":
            self.current_user = "admin"
            self.main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid login")

    # ==================== MAIN DASHBOARD ====================
    def main_dashboard(self):
        for w in self.root.winfo_children():
            w.destroy()

        sidebar = ctk.CTkFrame(self.root, width=230, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(sidebar, text="Teacher Panel", font=("Arial", 18, "bold")).pack(pady=25)
        ctk.CTkLabel(sidebar, text=f"Hi, {self.current_user}", font=("Arial", 12)).pack(pady=5)

        nav = [
            ("Live Camera", self.show_live),
            ("Today's List", self.show_today),
            ("Add Student", self.add_student_dialog),
            ("Logout", self.login_screen)
        ]
        for text, cmd in nav:
            ctk.CTkButton(sidebar, text=text, command=cmd, height=45).pack(pady=8, padx=20, fill="x")

        self.content = ctk.CTkFrame(self.root)
        self.content.pack(fill="both", expand=True, padx=15, pady=15)

        self.show_live()

    # ==================== LIVE CAMERA ====================
    def show_live(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Live Classroom Camera", font=("Arial", 26, "bold")).pack(pady=10)

        self.cam_label = tk.Label(self.content, bg="#1e1e1e")
        self.cam_label.pack(pady=10, expand=True)

        self.root.after(1000, self.start_camera)

        ctk.CTkLabel(self.content, text="Present Today", font=("Arial", 18)).pack(pady=(20,5))
        tree_frame = ctk.CTkFrame(self.content)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("Name", "Class", "Time")
        self.live_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols:
            self.live_tree.heading(c, text=c)
            self.live_tree.column(c, width=150, anchor="center")
        self.live_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tree_frame, command=self.live_tree.yview)
        sb.pack(side="right", fill="y")
        self.live_tree.config(yscrollcommand=sb.set)

        self.load_today_attendance()
        self.schedule_daily_export()

        # Start GUI update loop
        self.root.after(50, self.update_gui_from_queue)

    def start_camera(self):
        if self.cap is not None:
            return
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Webcam not found.")
                return
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 854)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.is_running = True
            threading.Thread(target=self.process_frames, daemon=True).start()
            print("[CAMERA] Started successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Camera failed: {e}")

    # ==================== BACKGROUND PROCESSING ====================
    def process_frames(self):
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            if self.recognizer:
                results = self.recognizer.recognize(frame)
                for (x, y, w, h, name, score) in results:
                    if name not in ["Unknown", "Error"]:
                        self.mark_attendance(name)  # DB + CSV + UI

                    # Draw on frame
                    color = (0, 255, 0) if name not in ["Unknown", "Error"] else (0, 0, 255)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                    label = f"{name} ({score:.2f})" if name not in ["Unknown", "Error"] else name
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # Convert and queue for GUI
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (854, 480))
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.frame_queue.append(imgtk)

            # Limit queue size
            if len(self.frame_queue) > 5:
                self.frame_queue.pop(0)

    # ==================== GUI UPDATE (SAFE) ====================
    def update_gui_from_queue(self):
        if self.frame_queue:
            imgtk = self.frame_queue.pop(0)
            try:
                self.cam_label.imgtk = imgtk
                self.cam_label.configure(image=imgtk)
            except:
                pass  # Widget destroyed
        if self.is_running:
            self.root.after(50, self.update_gui_from_queue)

    # ==================== INSTANT MARK + CSV ====================
    def mark_attendance(self, name):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE name=?", (name,))
        student = c.fetchone()
        if not student:
            conn.close()
            return
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT 1 FROM attendance WHERE student_id=? AND date=?", (student[0], today))
        if not c.fetchone():
            now = datetime.now().strftime("%H:%M:%S")
            c.execute("INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)",
                      (student[0], today, now))
            conn.commit()
            print(f"[MARKED] {name} @ {now}")

            # INSTANT CSV UPDATE
            self.update_csv_immediately(name, today, now)

            # INSTANT TABLE UPDATE
            self.root.after(0, self.load_today_attendance)
        conn.close()

    def update_csv_immediately(self, name, date_str, time_str):
        filename = 'Attendance.csv'
        if not os.path.exists(filename):
            pd.DataFrame(columns=['Name', 'Date', 'Time']).to_csv(filename, index=False)

        df = pd.read_csv(filename)
        if not ((df['Name'] == name) & (df['Date'] == date_str)).any():
            new_row = pd.DataFrame({'Name': [name], 'Date': [date_str], 'Time': [time_str]})
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(filename, index=False)
            print(f"[CSV] {name} added")

    def load_today_attendance(self):
        for i in self.live_tree.get_children():
            self.live_tree.delete(i)
        try:
            conn = get_conn()
            c = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute('''SELECT s.name, c.name, a.time FROM attendance a
                         JOIN students s ON a.student_id = s.id
                         JOIN classes c ON s.class_id = c.id
                         WHERE a.date = ? ORDER BY a.time''', (today,))
            for row in c.fetchall():
                self.live_tree.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            print(f"[DB ERROR] {e}")

    # ==================== 5 PM EXPORT (Mon–Fri) ====================
    def schedule_daily_export(self):
        now = datetime.now()
        target_time = time(17, 0)
        target = datetime.combine(now.date(), target_time)
        if now.weekday() >= 5:
            days_ahead = 7 - now.weekday()
            target = target.replace(day=now.day + days_ahead)
        elif now > target:
            target = target.replace(day=now.day + 1)
        delay_ms = int((target - now).total_seconds() * 1000)
        self.root.after(delay_ms, self.export_and_reschedule)

    def export_and_reschedule(self):
        self.export_today()
        self.schedule_daily_export()

    def export_today(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = get_conn()
            df = pd.read_sql_query("""
                SELECT s.name AS Student, c.name AS Class, a.time AS Time
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                WHERE a.date = ?
            """, conn, params=(today,))
            conn.close()
            if not df.empty:
                df.to_csv(f"Attendance_{today}.csv", index=False)
                print(f"[EXPORTED] Attendance_{today}.csv")
        except Exception as e:
            print(f"[EXPORT ERROR] {e}")

    # ==================== ADD STUDENT ====================
    def add_student_dialog(self):
        if not self.cap or not self.cap.isOpened():
            messagebox.showwarning("Camera Off", "Camera not running!")
            return
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Student")
        dialog.geometry("400x300")

        ctk.CTkLabel(dialog, text="New Student", font=("Arial", 18)).pack(pady=20)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="Name")
        name_entry.pack(pady=10)
        class_entry = ctk.CTkEntry(dialog, placeholder_text="Class")
        class_entry.pack(pady=10)

        def save():
            name = name_entry.get().strip()
            cls = class_entry.get().strip()
            if not name or not cls:
                messagebox.showerror("Error", "Fill all fields")
                return
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Error", "Camera failed")
                return
            os.makedirs(f"ImagesAttendance/{cls}", exist_ok=True)
            path = f"ImagesAttendance/{cls}/{name}.jpg"
            cv2.imwrite(path, frame)
            messagebox.showinfo("Success", f"Added {name}")
            dialog.destroy()
            threading.Thread(target=self.init_recognizer, daemon=True).start()

        ctk.CTkButton(dialog, text="Capture & Save", command=save).pack(pady=20)

    def show_today(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Today's Attendance", font=("Arial", 26)).pack(pady=20)
        self.show_live()

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def on_close(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()

# ==================== RUN ====================
if __name__ == "__main__":
    app = TeacherDashboard()
    app.root.mainloop()