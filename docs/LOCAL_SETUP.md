# OneDesk local setup

This guide sets up OneDesk on a local Windows, macOS, or Linux machine. The current application uses MySQL for accounts and productivity data; a working MySQL connection is required to sign in and use the workspace.

## Prerequisites

- Python 3.13 (the project targets Python 3.13; other versions may work but are not the supported setup).
- MySQL Server 8.x, running locally or reachable over your network.
- Git, if you are cloning the repository.

On Windows, install Python from [python.org](https://www.python.org/downloads/) and MySQL Server from [MySQL Community Downloads](https://dev.mysql.com/downloads/mysql/). On macOS or Linux, use your preferred package manager or the official installers. Make sure the MySQL service is started before continuing.

## Get the project and install dependencies

Clone the repository, or open the project folder you already have:

```powershell
git clone https://github.com/RajRishabh15/OneDesk-Tkinter.git
cd OneDesk-Tkinter
```

Create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either allow scripts for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again, or use Command Prompt with `.venv\Scripts\activate.bat`.

On macOS/Linux, use `python3.13 -m venv .venv` and `source .venv/bin/activate` instead.

Install the Python packages:

```shell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Tkinter is included with many Python installers. On some Linux distributions, install the system package for Tkinter (often named `python3-tk`) if importing `tkinter` fails.

## Create the MySQL database

From the project root, run the schema script with a MySQL administrator account. It creates the `onedesk` database and its tables; it does not drop existing tables.

```shell
mysql -u root -p < setup_db.sql
```

Enter the MySQL administrator password when prompted. If the `mysql` command is not on your PATH, run this through MySQL Workbench or provide the full path to the MySQL client.

The application should use a separate local MySQL account rather than the root account. In a MySQL client, create one and grant access to this database (replace the password with a strong, private value):

```sql
CREATE USER 'onedesk_app'@'localhost' IDENTIFIED BY 'replace-with-a-strong-secret';
GRANT SELECT, INSERT, UPDATE, DELETE ON onedesk.* TO 'onedesk_app'@'localhost';
```

If you already created this account, do not run `CREATE USER` again. Adjust the host part (for example, `'onedesk_app'@'%'`) only if the app connects from a different machine, and restrict network access appropriately.

## Configure the application

Copy `.env.example` to `.env.local` in the project root, then edit `.env.local` with the credentials and host for your MySQL server:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=onedesk
DB_USER=onedesk_app
DB_PASSWORD=replace_with_a_real_secret
```

Do not commit `.env.local` or share its contents. It is ignored by Git. Environment variables named `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` override values in this file.

## Verify and start OneDesk

With the virtual environment active and MySQL running, verify connectivity:

```shell
python check_db_connection.py
```

The command should report the database name and MySQL version. If it fails, check that MySQL is running, the host and port are correct, the database setup completed, and the configured account can connect to `onedesk`.

Start the desktop application:

```shell
python main.py
```

Create an account from the sign-in screen, or use the demo sign-in option to explore. Account passwords are stored as modern password hashes; never put plaintext passwords or real credentials in source files.

## Local data and backups

OneDesk keeps app preferences and backup/import files locally. Use **Settings → Data Management** to export or restore a backup. Backups can contain personal productivity data, so store them securely. Keep a separate backup before changing or rebuilding an existing database; `setup_db.sql` creates missing objects but does not migrate an older schema.

## Troubleshooting

- **`DB_USER is required` or `DB_PASSWORD is required`:** check that `.env.local` exists in the project root and contains the corresponding non-empty settings.
- **Connection refused / cannot reach MySQL:** start the MySQL service and confirm `DB_HOST` and `DB_PORT`.
- **Access denied:** check the MySQL username, password, account host, and grants.
- **Unknown database or missing tables:** run `setup_db.sql` against the intended MySQL server.
- **MySQL driver missing:** activate the project virtual environment and run `python -m pip install -r requirements.txt`.
- **Tkinter import error on Linux:** install your distribution's Tkinter package, then run the app again.

