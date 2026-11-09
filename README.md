# 🎓 College Timetable & AI Resource Scheduler

[![GitHub Pages](https://img.shields.io/badge/Live%20Website-GitHub%20Pages-blue?style=for-the-badge&logo=github)](https://2503a52753-Purna.github.io/College_timetable_generator/)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/2503a52753-Purna/College_timetable_generator)

An automated College Timetable Management System featuring constraint-satisfaction scheduling for colleges, departments, batches, sections, faculty, and laboratories.

---

## 🌐 Live Website (GitHub Pages)

Direct 24/7 Web App:
👉 **[https://2503a52753-Purna.github.io/College_timetable_generator/](https://2503a52753-Purna.github.io/College_timetable_generator/)**

- **Filter by College:** SR University, Kakatiya University, NIT Warangal, Osmania University, JNTU Hyderabad
- **Filter by Role:** Student Batch / Section or Faculty member
- **Interactive AI Scheduler:** Test constraint-satisfaction algorithm with zero room/faculty collisions
- **Print / PDF:** Single-click schedule export

---

## 🚀 Run Locally

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python college_timetable_system/app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

- **Admin Login:** [http://127.0.0.1:5000/admin-login](http://127.0.0.1:5000/admin-login)
  - **Username:** `superadmin`
  - **Password:** `admin123`

---

## ☁️ 24/7 Cloud Backend Deployment (Render)

1. Open [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints) or click the **Deploy to Render** button above.
2. Connect this repository: `2503a52753-Purna/College_timetable_generator`.
3. Render automatically provisions the web service via `render.yaml`.
4. URL format: `https://timetable-generator.onrender.com`
