# Nowpad

A minimal Django web app for personal capture and organization. Quickly capture notes/tasks and organize them through fast inline editing.

## Features

- **Fast Capture**: Dedicated page to add items quickly with one required field (Note)
- **Fast Organize**: View and rapidly edit many records inline without page reloads
- **Mobile Ready**: Works on both desktop and mobile browsers
- **Windows 95 Aesthetic**: Minimalist retro utility design

## Quick Start

### Local Development

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

5. **Access the app:**
   - Add items: http://127.0.0.1:8000/x9K3pQ7v2/add/
   - Organize: http://127.0.0.1:8000/x9K3pQ7v2/organize/

### PythonAnywhere Deployment

1. Create a new web app on PythonAnywhere (Free tier works)
2. Upload the project files
3. Set up a virtual environment and install requirements
4. Configure WSGI to point to `nowpad.wsgi:application`
5. Set `DEBUG = False` in settings.py
6. Update `ALLOWED_HOSTS` with your PythonAnywhere domain
7. Run migrations
8. Collect static files: `python manage.py collectstatic`

## Security Note

This app uses security-by-obscurity with an unguessable URL prefix (`x9K3pQ7v2`). For production, consider:

1. Changing the `URL_SECRET_PREFIX` in `nowpad/settings.py` to your own random string
2. Generating a new `SECRET_KEY`
3. Setting `DEBUG = False`

## Data Model

### Item (main table)
- **note**: The captured text (required)
- **type**: Idea, Journey, Project, or Action
- **action_length**: 5 minutes, 15 minutes, 1 hour, or 3 hours (only for Actions)
- **time_frame**: Now, Today, This Week, This Month, or Future
- **value**: 1-5 rating
- **difficulty**: 1-5 rating
- **score**: Computed as `value + (6 - difficulty)` for prioritization
- **status**: Open, Complete, Archive, or Remove
- **life_category**: Optional category reference
- **date_created**: Auto-set on creation
- **date_completed**: Auto-set when status becomes Complete

### LifeCategory (supporting table)
- **name**: Category name (unique)

## Usage

### Add Page
- Type your note in the large text area
- Optionally set type, time frame, value, difficulty, and category
- Click "Save Item" (sticky at bottom)

### Organize Page
- Filter by status, time frame, type, or category
- Click column headers to sort
- Edit any field inline - changes save automatically
- On mobile, tap a card to expand and edit

## Tech Stack

- Django 4.2
- SQLite database
- Vanilla JavaScript (no frameworks)
- Windows 95 inspired CSS

