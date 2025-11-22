# Python Smart Attendance Application

A real-time, AI-powered smart attendance system built using **Python** and **OpenCV**. The application automatically detects student faces through a webcam feed and instantly marks their attendance for the lecture hour. This eliminates manual roll-calls and provides a fast, automated, and efficient workflow.

---

## 🚀 Features

* 🎥 **Real-time face detection** using OpenCV
* 🧑‍🎓 **Automatic student identification**
* 📝 **Instant attendance marking**
* 📊 **Dashboard for viewing attendance logs**
* 📁 **Data stored securely (CSV/Database)**
* 🔄 **Duplicate prevention for each session**

---

## 🛠 Tech Stack

* Python
* OpenCV
* NumPy
* Tkinter / Flask (depending on dashboard implementation)
* CSV / SQLite for data logging

---

## 📂 Project Structure

```
/Smart-Attendance/
│── main.py
│── detect_and_mark.py
│── dashboard.py
│── models/ (face data)
│── dataset/ (student images)
│── attendance/ (logs)
│── requirements.txt
│── README.md
```

---

## ▶️ How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the main application:

```bash
python main.py
```

---

## 📸 Working

1. The webcam captures the classroom feed.
2. OpenCV detects and identifies student faces.
3. Attendance is automatically marked with timestamps.
4. The dashboard displays live and past records.

---

## 📌 GitHub Topics

```
python, opencv, computer-vision, face-detection, face-recognition,
attendance-system, smart-attendance, automation, ai-project,
real-time-detection, image-processing, student-attendance
```
