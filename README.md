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
│   │   ├── api.py              # API routes for AJAX requests and data retrieval 
│   │   ├── main.py             # Main application routes, Handles home page, dashboard, and general navigation  
│   │   ├── speed.py            # Track speed processing route
│   │   └── upload.py           # File upload and processing routes
│   ├── templates/              # HTML templates
│   │   ├── base.html           # Universal master page (including navigation, footer) 
│   │   ├── dashboard.html      # dashborad 
│   │   ├── index.html          # homepage
│   │   ├── speed_chart.html    # recalculate the max speed by different sampling
│   │   ├── upload_sucess.html  # upload sucess feedback page
│   │   ├── upload.html         # upload page
│   │   └── ....html            # others pages
│   ├── __init__.py             # "firmware" for the project, not only a package statement
│   └── models.py               # Database models
├── database/                   # Database related
│   ├── schema1.sql             # Database schema solution 1
│   └── schema2.sql             # Database schema solution 2, the final
├── gpx_tools/                  # GPX processing tools
│   ├── __init__.py             # extracted key fields, convert to JSON from gpx_processor.py
│   ├── gpx_processor.py        # GPX parsing and processing
│   └── utils.py                # tools for gpx processing
├── sample_data/                # gpx files processing workspace
│   ├── temp/
│   └── processed/
├── static/                     # Static files
│   ├── css/                    # css files
│   │   └── style.css      
│   └── js/                     # JavaScript files
│   │   ├── common.js           # common script for other js files 
│   │   ├── dashboard.js   
│   │   ├── index.js        
│   │   ├── uploads.js          # uploads page
│   │   └── others.js 
├── settings/                   # config and constants
├    ├── config.py              # Configuration file
├    └── constants.py           # constants file
├── tests/                      # Test files
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
psql -d gps_tracking_db -f database/schema.sql
```

### 4. Environment Variable Configuration
Copy `.env.example` to `.env` and fill in configuration:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/gps_tracking_db
FLASK_SECRET_KEY=your-secret-key
GOOGLE_MAPS_API_KEY=your-google-api-key
```

### 5. Run Application
```bash
python run.py
```

Visit http://localhost:5000

## Features

- [ ] User registration and login
- [X] GPX file upload and parsing
- [ ] Track data storage in PostgreSQL
- [ ] Interactive map track display
- [ ] Track statistical analysis charts
- [ ] Track time segment cutting functionality
- [ ] Multi-user track comparison

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
- [ ] User interface development
- [ ] Database integration
- [x] File upload functionality
- [ ] Basic map display

### Sprint 3 (Week 5-6)
- [ ] Data visualization charts
- [ ] Track analysis features
- [ ] User authentication system
- [ ] System testing and optimization

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

For detailed architecture see `database/schema2.sql` & `database/ERD2.png`

## API Documentation

(In development...)


## License

This project is for educational purposes only.
