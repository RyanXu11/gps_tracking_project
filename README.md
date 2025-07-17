# GPS Tracking Project

CST8276 Database Course Team Project - GPS Track Recording and Analysis System

## Project Overview

A web-based GPS track upload, storage, and visualization analysis system. Users can upload GPX files, and the system will parse the data and store it in a PostgreSQL database, providing interactive maps and statistical charts for track analysis.

## Tech Stack

- **Backend**: Python + Flask
- **Database**: PostgreSQL 
- **Frontend**: HTML/CSS/JavaScript + Google Maps API
- **Data Processing**: pandas, numpy, gpxpy
- **Visualization**: Google Maps API (primary), Plotly (analytics charts)
- **Deployment**: (TBD)

## Project Structure

```
gps_tracking_project/
├── app/                        # Flask application
│   ├── routes/                 # HTML templates
│   │   ├── __init__.py         # initial file for routes
│   │   ├── animation.py        # Routes for animation 
│   │   ├── api.py              # API routes for AJAX requests and data retrieval
│   │   ├── login.py            # Routes for login
│   │   ├── main.py             # Main application routes, Handles home page, dashboard, and general navigation
│   │   ├── signup.py           # Routes for signup
│   │   ├── speed.py            # Track speed processing route
│   │   └── upload.py           # File upload and processing routes
│   ├── templates/              # HTML templates
│   │   ├── base.html           # Universal master page (including navigation, footer) 
│   │   ├── dashboard_public.html      # dashborad for public tracks
│   │   ├── dashboard.html      # dashborad for "My tracks"
│   │   ├── login.html          # login page
│   │   ├── signup.html         # signup page
│   │   ├── speed_chart.html    # recalculate the max speed by different sampling
│   │   ├── track_animation.html        # track animation page
│   │   ├── upload_sucess.html  # upload sucess feedback page
│   │   └── upload.html         # upload page
│   ├── __init__.py             # "firmware" for the project, not only a package statement
│   └── models.py               # Database models
├── database/                   # Database related
│   ├── schema1.sql             # Database schema solution 1
│   └── schema2.sql             # Database schema solution 2, the final
├── gpx_tools/                  # GPX processing tools
│   ├── __init__.py             # extracted key fields, convert to JSON from gpx_processor.py
│   ├── gpx_processor.py        # GPX parsing and processing
│   └── utils.py                # tools for gpx processing
├── settings/                   # config and constants
│   ├── config.py
│   └── constants.py
├── static/                     # Static files
│   ├── css/                    # css files
│   │   ├── animation.css
│   │   ├── ...
│   │   └── upload.css      
│   └── js/                     # JavaScript files
│   │   ├── base.js           
│   │   ├── dashboard.js   
│   │   ├── speed_chart.js        
│   │   ├── upload_success.js          
│   │   └── upload.js 
├── settings/                   # config and constants
├    ├── config.py              # Configuration file
├    └── constants.py           # constants file
├── tests/                      # Test files
│   └── test_database.py        # Unit test
├── environment.yml             # Conda environment configuration
├── README.md                   # Readme
├── requirements.txt            # Python dependencies
├── .gitignore                  # git ignore configuration
└── run.py                      # Application startup file

```

## Environment Setup

### 1. Clone Project
```bash
git clone [repository-url]
cd gps_tracking_project
```

### 2. Create Python Environment
#### 2.1 Recommended - Conda(with environment.yml)
```bash
conda env create -f environment.yml
conda activate gps_tracking
```

#### 2.2 Pip (if Conda is not available)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# On macOS/Linux
source venv/bin/activate
```

#### 2.3 Confirm Python environment
```bash
python --version     # should show Python 3.12.x
conda list           # or
pip list             # verify key packages are installed
```

### 3. Database Setup
```bash
# Create PostgreSQL user & database
CREATE USER dbgroup2 WITH PASSWORD 'cst8276G2';
ALTER USER dbgroup2 CREATEDB;

-- Create database with team user as owner
DROP DATABASE IF EXISTS gps_tracking_db;

CREATE DATABASE gps_tracking_db
    WITH 
    OWNER = dbgroup2
    ENCODING = 'UTF8';

# Run database schema
Run the schema2.sql one by one, or
psql -d gps_tracking_db -f database/schema2.sql
```

### 4. Environment Variable Configuration
Please note configuration in /settings/config.py & constants.py
Please create .env file in your root directory like:
```
# Database Configuration
DATABASE_PASSWORD=cst8276G2

# API Keys
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

```
Note:

Never commit .env file to Git
Copy .env.example and rename to .env to get started
Each developer should have their own .env file

### 5. Run Application
```bash
python run.py
```

Visit http://localhost:5000

## Features

- [X] User registration and login
- [X] GPX file upload and parsing
- [X] Track data storage in PostgreSQL
- [X] Interactive map track display
- [X] Track speed analysis charts
- [ ] Track statistical analysis charts
- [ ] Track time segment cutting functionality
- [X] Multi-user track comparison
- [X] Track animation in google map

## Team Assignment

| Member | Main Responsibility | Specific Tasks |
|--------|-------------------|----------------|
| Ryan (Team Lead) | Project coordination, Database design | PostgreSQL architecture,  GPX processing|
| Member 2 | Backend development | Flask routes,  User interface|
| Member 3 | Frontend development | HTML/CSS/JS|
| Member 4 | Map integration | Google Maps API integration |
| Member 5 | Data visualization | Plotly charts development |
| Member 6 | Testing and deployment | Functional testing, Documentation |

## Development Progress

### Sprint 1 (Week 1-2)
- [x] Project architecture design
- [x] Database schema design
- [x] Basic Flask application setup
- [x] GPX file parsing functionality

### Sprint 2 (Week 3-4)
- [x] User interface development
- [x] Database integration
- [x] File upload functionality
- [x] Basic map display

### Sprint 3 (Week 5-6)
- [x] Data visualization charts
- [x] Track analysis features
- [x] User authentication system
- [x] System testing and optimization

## Database Design

### users table
- user_id (Primary Key)
- username
- email
- password_hash
- created_at

### tracks table
- track_id (Primary Key) 
- user_id (Foreign Key)
- track_name
- description
- is_public
- gpx_file (GPX/XML)
- jsonb_waypoints JSONB,             -- Structured data after GPX parsing
- jsonb_metadata JSONB,              -- Metadata for the GPX file
- jsonb_statistics JSONB,            -- Consolidated statistics and indicators
- created_at, 
- updated_at

For detailed architecture see `database/schema2.sql` & `database/ERD_final.png`

## API Documentation

(In development...)


## License

This project is for educational purposes only.

(Last Modified Date: 2025-07-17)
