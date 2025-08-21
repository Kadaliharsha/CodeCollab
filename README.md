# CodeCollab

Welcome to **CodeCollab** — a collaborative coding platform designed for real-time problem solving, code sharing, and peer learning. CodeCollab enables users to join virtual rooms, tackle coding challenges together, and see live code updates and results, making it ideal for interviews, hackathons, classrooms, and peer programming.

---

## 🚀 What is CodeCollab?

CodeCollab is an interactive web application that empowers multiple users to collaborate on coding problems in real time. Each room features a shared code editor, live output panel, and problem descriptions, allowing participants to write, execute, and submit code together. Submissions are automatically judged against test cases for instant feedback.

---

## 🛠️ Technologies Used

- **Python** (Flask, SQLAlchemy): Backend API, room management, user authentication, and code execution logic.
- **HTML & Tailwind CSS**: Modern, responsive UI for the code editor and rooms.
- **Socket.IO**: Real-time communication between clients for instant code updates and room events.
- **PostgreSQL**: Persistent database for users, rooms, problems, and test cases.
- **Docker** (suggested): Isolated code execution environment (extensible for interview safety).
- **JavaScript**: Frontend interactivity and WebSocket event handling.

---

## 🧑‍💻 Core Features

- **Live Collaboration:** Join rooms, edit code together, and see real-time changes.
- **Problem Panel:** Every room displays a coding challenge with description and starter code.
- **Code Execution & Auto-Judging:** Instantly run code or submit it for automated test case evaluation.
- **User Authentication:** Register and log in (JWT-ready).
- **Database Seeding:** Preloaded with classic coding problems (e.g., Reverse String, Two Sum).
- **Scalable Design:** Easily add new problems and extend judging logic.

---

## 🎯 Why Recruiters and Hiring Managers Love CodeCollab

- **Showcases Backend & Frontend Skills:** Demonstrates your ability to build scalable, real-time web apps using modern Python and JavaScript technologies.
- **Code Quality & Architecture:** Organized with clear separation of models, routes, templates, and configuration.
- **Testable & Extensible:** Seeded test cases and modular execution logic for easy expansion.
- **Interview-Ready:** Perfect for technical interviews, pair programming, and classroom use.

---

## 📝 Getting Started

1. **Clone the repo:**  
   ```bash
   git clone https://github.com/Kadaliharsha/CodeCollab.git
   ```
2. **Install dependencies:**  
   - Python libraries: Flask, SQLAlchemy, Flask-SocketIO, etc.
   - Frontend: Tailwind via CDN, Socket.IO JS.
3. **Configure environment:**  
   Edit `config.py` for database connection details.
4. **Seed the database:**  
   ```bash
   python seed.py
   ```
5. **Run the app:**  
   ```bash
   python run.py
   ```
6. **Open in browser:**  
   Visit `http://localhost:5001/room/<room_id>` to join a room.

---

## 📚 Example Problems

- Reverse a String
- Two Sum
- Easily add more in `seed.py`!

---

## 📦 Folder Structure

- `app/` — Main application code: models, API routes, templates.
- `run.py` — App entry point.
- `seed.py` — Database seeder.
- `config.py` — Configuration settings.

---

## ❤️ Contributing

Open to issues, suggestions, and pull requests — let’s make collaborative coding better together!

---

## 🔗 Links

- [Live Demo (if available)](https://github.com/Kadaliharsha/CodeCollab)
- [See All My Projects](https://github.com/Kadaliharsha)

---

> **Ready to revolutionize how you code together? Try CodeCollab!**
