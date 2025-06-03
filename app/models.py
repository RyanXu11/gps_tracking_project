from app import get_db_connection
from settings.constants import SQL_QUERIES, TIMEZONE_STR
import json
import pytz

class User:
    @staticmethod
    def get_by_id(user_id):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_USER_BY_ID'], (user_id,))
                user = cursor.fetchone()
                return user
    
    @staticmethod
    def get_by_username(username):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_USER_BY_USERNAME'], (username,))
                user = cursor.fetchone()
                return user

class Track:
    @staticmethod
    def create(user_id, track_name, description=None):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['CREATE_BASIC_TRACK'], (user_id, track_name, description))
                track_id = cursor.fetchone()['track_id']
                conn.commit()
                return track_id
    
    @staticmethod
    def create_with_gpx_data(user_id, track_name, jsonb_data, extracted_fields, gpx_file_content, file_hash, skip_points=1, description=None):
        """
        Create track record with complete GPX data
        
        Args:
            user_id: User ID
            track_name: Track name
            jsonb_data: JSONB data for jsonb_track_data column
            extracted_fields: Dictionary with extracted fields (start_time, end_time, etc.)
            gpx_file_content: Binary content of GPX file
            file_hash: MD5 hash of file content
            skip_points: Skip points used for speed calculation
            description: Optional description
            
        Returns:
            track_id: Created track ID
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # Execute insert using SQL constant
                    cursor.execute(SQL_QUERIES['CREATE_FULL_TRACK'], (
                        user_id,
                        track_name,
                        description,
                        gpx_file_content,  # Store binary content directly
                        json.dumps(jsonb_data),
                        extracted_fields.get('start_time'),
                        extracted_fields.get('end_time'),
                        extracted_fields.get('total_distance'),
                        extracted_fields.get('total_duration'),
                        extracted_fields.get('max_speed'),
                        extracted_fields.get('avg_speed'),
                        file_hash,
                        skip_points
                    ))
                    
                    track_id = cursor.fetchone()['track_id']
                    conn.commit()
                    
                    return track_id
                    
                except Exception as e:
                    conn.rollback()
                    raise Exception(f"Error creating track with GPX data: {str(e)}")
    
    @staticmethod
    def check_duplicate_by_hash(user_id, file_hash):
        """
        Check if a file with the same hash already exists for the user
        
        Args:
            user_id: User ID
            file_hash: MD5 hash of file content
            
        Returns:
            Boolean indicating if duplicate exists
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['CHECK_DUPLICATE_HASH'], (user_id, file_hash))
                result = cursor.fetchone()
                return result['count'] > 0


    @staticmethod
    def get_by_id(track_id):
        """Get track by ID including GPX data"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_TRACKS_BY_TRACK'], (track_id,))
                track = cursor.fetchone()
                track['start_time'] = Track.convert_utc_to_local(track['start_time'])
                track['end_time'] = Track.convert_utc_to_local(track['end_time'])                
                return track

    
    @staticmethod
    def get_by_user(user_id):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_TRACKS_BY_USER'], (user_id,))
                tracks = cursor.fetchall()
                return tracks

            
    @staticmethod
    def update_statistics(track_id, jsonb_data, extracted_fields, skip_points):
        """Update track statistics with new calculations"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(SQL_QUERIES['UPDATE_TRACK'], (
                        json.dumps(jsonb_data),
                        extracted_fields.get('max_speed'),
                        skip_points,
                        track_id
                    ))
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    raise Exception(f"Error updating track statistics: {str(e)}")     
    
    @staticmethod
    def convert_utc_to_local(dt_utc, timezone_str=TIMEZONE_STR):
        if dt_utc is None:
            return None
        local_tz = pytz.timezone(timezone_str)
        if dt_utc.tzinfo is None:
            dt_utc = pytz.utc.localize(dt_utc)
        return dt_utc.astimezone(local_tz) 