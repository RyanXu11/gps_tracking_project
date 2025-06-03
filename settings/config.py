from .constants import *
import os

class Config:
    # Database configuration
    DATABASE_URL = DATABASE_URL
    
    # Flask configuration
    SECRET_KEY = SECRET_KEY
    DEBUG = DEBUG_MODE
    
    # Upload configuration
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE
    