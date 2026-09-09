# College Timetable System

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in a browser. Other devices on the same network can use the computer's local IP address, for example `http://192.168.1.20:5000`.

## Admin authentication

The app uses Flask server-side sessions. The public timetable is available at `/`; management is protected at `/admin` and `/api/*` write routes. Configure a strong secret and a Werkzeug password hash before starting the server:

```powershell
$env:SECRET_KEY = 'replace-with-a-long-random-value'
$env:ADMIN_USERNAME = 'admin'
$env:ADMIN_PASSWORD_HASH = 'paste-a-werkzeug-generated-password-hash'
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('replace-with-your-password'))"
```

Set `SESSION_COOKIE_SECURE=1` when serving over HTTPS. Do not commit credentials or the generated hash to source control.

## Publish on the internet

1. Create a repository containing this project folder.
2. Create a free Web Service on [Render](https://render.com) and connect the repository.
3. Render will use `render.yaml`, install the requirements, generate `SECRET_KEY`, and start the app with Gunicorn.
4. In the Render service environment settings, set `ADMIN_PASSWORD_HASH` to the output of `generate_password_hash` shown above.
5. Share the HTTPS URL Render provides.

The application currently uses SQLite, so its data is intended for demos and small deployments. Use a hosted database before relying on it for permanent production data.

## Deploy on PythonAnywhere

1. Create a PythonAnywhere account and open a Bash console.
2. Upload or clone this project into your home directory, for example:

	```bash
	cd ~
	git clone YOUR_REPOSITORY_URL college_timetable_system
	cd college_timetable_system/college_timetable_system
	```

3. Create a virtual environment using the Python version selected for the web app and install dependencies:

	```bash
	mkvirtualenv --python=/usr/bin/python3.10 college-timetable-env
	pip install -r requirements.txt
	```

4. Create the initial database and seed data:

	```bash
	python -c "import app"
	```

5. In the **Web** tab, create a new Flask web app. Select the same Python version and virtual environment.
6. Set the **Source code** directory to:

	```text
	/home/YOUR_USERNAME/college_timetable_system/college_timetable_system
	```

7. Open the WSGI configuration file shown in the Web tab and replace its contents with:

	```python
	import os
	import sys

	project_dir = '/home/YOUR_USERNAME/college_timetable_system/college_timetable_system'
	if project_dir not in sys.path:
		 sys.path.insert(0, project_dir)

	os.environ.setdefault('SECRET_KEY', 'replace-with-a-long-random-secret')
	os.environ.setdefault('SESSION_COOKIE_SECURE', '1')

	from app import app as application
	```

8. Replace `YOUR_USERNAME` and set a strong unique `SECRET_KEY`. Do not commit that secret.
9. Click **Reload** in the Web tab, then open the PythonAnywhere URL shown there.

The first login is the seeded Super Admin account: `superadmin` / `admin123`. Change that password immediately from the Admin Access section after deployment. SQLite persists on PythonAnywhere, but the free plan is best suited to demos and small deployments.