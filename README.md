# Laureon Sample Location Management (SLM)

Laureon SLM is a web application built with Django for managing and tracking the physical locations of laboratory samples. It provides a hierarchical system for defining storage locations and a control interface for managing the samples within them.

## Key Features

* **Hierarchical Location Configuration**: Define multi-level storage locations (e.g., Room > Freezer > Rack > Box) with custom rules.
* **Grid-Based Space Management**: Locations can be configured as simple containers or as grids with addressable spaces (e.g., an 8x12 rack) using an A1, B2 coordinate system.
* **Sample Tracking**: Create, edit, and delete individual samples, assigning them to specific locations or spaces.
* **Bulk Operations**: Perform bulk creation and deletion of samples to streamline data entry.
* **Search**: Quickly find samples by name, lot number, or other attributes.
* **Production-Ready**: Configured for deployment with security and static file management best practices.

---

## Local Development Setup

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.9+
* Pip (Python package installer)
* PostgreSQL Server (running locally)

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <your-new-repository-url>
    ```

    ```bash
    cd Laureon_SLM
    ```

2.  **Create and activate a virtual environment:**
   
    **On macOS/Linux**
    ```bash
    python3 -m venv env
    ```

    ```bash
    source env/bin/activate
    ```

    **On Windows**
    ```bash
    python -m venv env
    ```

    ```bash
    .\env\Scripts\activate
    ```

3.  **Install the required packages:**
    * This project requires a PostgreSQL database. First, install the database driver:
      
        ```bash
        pip install psycopg2-binary
        ```
    * Then, install the rest of the application's dependencies:
      
        ```bash
        pip install -r requirements.txt
        ```

4.  **Create the local environment variables file (`.env`):**
    * In the root of the project, create a new file named `.env`.
    * Add the following content to the file, replacing the placeholder values as needed. You can generate a new, random `SECRET_KEY`.
      
        ```env
        # .env - LOCAL DEVELOPMENT SETTINGS
        SECRET_KEY='your-strong-secret-key-for-development'
        DEBUG=True
        ALLOWED_HOSTS=127.0.0.1,localhost
        DATABASE_URL='postgres://YourUser:YourPassword@localhost:5432/laureon_slm_db'
        ```
    * **Note**: Make sure you have created a PostgreSQL database named `laureon_slm_db` (or whatever you choose) and that the user and password are correct.

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser to access the admin and the app:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000/slm/main_menu/`.

---

## Production Deployment Notes

This section provides a checklist for deploying the application to a production environment.

1.  **Production Environment Variables (`.env`):**
    * Your production server must have its own `.env` file with production-specific settings. **Do not commit your production `.env` file to Git.**
    * The `SECRET_KEY` must be a different, long, and random value.
    * `DEBUG` must be set to `False`.
    * `ALLOWED_HOSTS` should be a comma-separated list of your production domain(s) (e.g., `laureon.com,www.laureon.com`).
      
        ```env
        # .env - PRODUCTION SETTINGS
        SECRET_KEY='your-different-very-strong-production-secret-key'
        DEBUG=False
        ALLOWED_HOSTS=laureon.com,www.laureon.com
        DATABASE_URL='postgres://ProdUser:ProdPassword@prod-db-host:5432/laureon_slm_prod_db'
        ```

2.  **Collect Static Files:**
    * Before deploying, you must run the `collectstatic` command. This gathers all static files (CSS, JavaScript, images) into a single directory for your web server.
      
        ```bash
        python manage.py collectstatic
        ```
    * Your web server (e.g., Nginx) should be configured to serve files from the `staticfiles` directory that this command creates.

3.  **Web Server and WSGI:**
    * Do not use the Django development server (`runserver`) in production.
    * You need to use a production-grade WSGI server like **Gunicorn** or **uWSGI** to run the application, typically behind a reverse proxy web server like **Nginx**.
