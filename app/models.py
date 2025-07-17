from app import get_db_connection
from settings.constants import SQL_QUERIES, TIMEZONE_STR
from psycopg2.extras import Json, RealDictCursor
import pytz
from datetime import datetime

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
            
    @staticmethod
    def get_by_email(email):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_USER_BY_EMAIL'], (email,))
                user = cursor.fetchone()
                return user
            
class Login:
    @staticmethod
    def verify_login(email, password_hash):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['VERIFY_LOGIN'],(email,password_hash))
                rowExist = cursor.fetchone()
                return bool(rowExist)

class Register:
    @staticmethod
    def verify_registration(email):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['VERIFY_UNIQUE_EMAIL'],(email,))
                emailExist = cursor.fetchone()
                return bool(emailExist)

    @staticmethod
    def register_user(username,user_email,password_hash):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['CREATE_USER'],(username,user_email,password_hash))
                new_user_id = cursor.fetchone()['user_id']
                conn.commit()
                return new_user_id

class Track:
    @staticmethod
    def create(user_id, track_name, description=None, is_public=False):
        """Create basic track record without GPX data"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['CREATE_BASIC_TRACK'], (user_id, track_name, description, is_public))
                track_id = cursor.fetchone()['track_id']
                conn.commit()
                return track_id
    
    @staticmethod
    def create_with_gpx_data(
        user_id,
        track_name,
        gpx_file_content,
        file_hash,
        jsonb_waypoints,
        jsonb_metadata,
        jsonb_statistics,
        description=None,
        is_public=False
    ):
        """
        Create a new track with GPX data using new three-field structure
        
        Args:
            user_id: User ID
            track_name: Name of the track
            gpx_file_content: Raw GPX file content (bytes)
            file_hash: MD5 hash of the file
            jsonb_waypoints: List of waypoint objects
            jsonb_metadata: Metadata object
            jsonb_statistics: Statistics object with nested structure
            description: Optional track description
            is_public: Whether track is public
            
        Returns:
            track_id of the created track
        """
        try:            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert track record with new three-field structure
                    print(f"Debug: user_id = {user_id}")
                    print(f"Debug: gpx_file_content length = {len(gpx_file_content) if gpx_file_content else 'None'}")
                    print(f"Debug: jsonb_waypoints count = {len(jsonb_waypoints) if jsonb_waypoints else 'None'}")
                    print(f"Debug: jsonb_metadata type = {type(jsonb_metadata)}")
                    print(f"Debug: jsonb_statistics type = {type(jsonb_statistics)}")
                    
                    cursor.execute(SQL_QUERIES['CREATE_FULL_TRACK'], (
                        user_id, track_name, description, is_public,
                        gpx_file_content, file_hash, 
                        Json(jsonb_waypoints),   # Direct waypoints array
                        Json(jsonb_metadata),    # Metadata object
                        Json(jsonb_statistics)   # Statistics object
                    ))

                    result = cursor.fetchone()
                                    
                    if result:
                        track_id = result['track_id']
                        conn.commit()
                        return track_id
                    else:
                        raise Exception("Failed to insert track")
                                        
        except Exception as e:
            print(f"Error creating track: {e}")
            raise
    
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
        """Get track by ID including GPX data with new three-field structure"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_TRACKS_BY_TRACK'], (track_id,))
                track = cursor.fetchone()
                
                # Convert UTC times to local timezone if they exist in jsonb_statistics
                if track and track.get('jsonb_statistics'):
                    stats = track['jsonb_statistics']
                    if 'basic_metrics' in stats:
                        basic_metrics = stats['basic_metrics']
                        if 'start_time' in basic_metrics:
                            basic_metrics['start_time'] = Track.convert_utc_to_local_str(basic_metrics['start_time'])
                        if 'end_time' in basic_metrics:
                            basic_metrics['end_time'] = Track.convert_utc_to_local_str(basic_metrics['end_time'])
                
                return track
    

    @staticmethod
    def get_by_public():
        """Get all public tracks with their data"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_PUBLIC_TRACKS'])
                tracks = cursor.fetchall()

                processed_tracks = []
                for track in tracks:
                    if track:  # Ensure we have a track record
                        # Convert to dictionary if it's not already one
                        if not isinstance(track, dict):
                            track_dict = dict(track)
                        else:
                            track_dict = track
                    # Convert UTC times to local timezone if they exist in jsonb_statistics
                    if track_dict.get('jsonb_statistics'):
                        stats = track_dict['jsonb_statistics']
                        if 'basic_metrics' in stats:
                            basic_metrics = stats['basic_metrics']
                            if 'start_time' in basic_metrics:
                                basic_metrics['start_time'] = Track.convert_utc_to_local_str(basic_metrics['start_time'])
                            if 'end_time' in basic_metrics:
                                basic_metrics['end_time'] = Track.convert_utc_to_local_str(basic_metrics['end_time'])
                    processed_tracks.append(track_dict)
                return processed_tracks

    @staticmethod
    def get_by_user(user_id):
        """Get all tracks for a user with new three-field structure"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_TRACKS_BY_USER'], (user_id,))
                tracks = cursor.fetchall()
                
                # Convert UTC times for each track
                for track in tracks:
                    if track.get('jsonb_statistics'):
                        stats = track['jsonb_statistics']
                        if 'basic_metrics' in stats:
                            basic_metrics = stats['basic_metrics']
                            if 'start_time' in basic_metrics:
                                basic_metrics['start_time'] = Track.convert_utc_to_local_str(basic_metrics['start_time'])
                            if 'end_time' in basic_metrics:
                                basic_metrics['end_time'] = Track.convert_utc_to_local_str(basic_metrics['end_time'])
                
                return tracks

    @staticmethod
    def update_statistics(track_id, jsonb_statistics):
        """
        Update track statistics with new processing results using new structure
        
        Args:
            track_id: Track ID to update
            jsonb_statistics: New statistics object with processing results
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(SQL_QUERIES['UPDATE_TRACK_STATISTICS'], (
                        Json(jsonb_statistics),
                        track_id
                    ))
                    conn.commit()
                    
        except Exception as e:
            print(f"Error updating track statistics: {e}")
            raise

    @staticmethod
    def delete_by_id(track_id, user_id):
        """
        Securely delete a track by ID and user ID with error handling

        Args:
            track_id: ID of the track to delete
            user_id: ID of the track owner (for security)
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(SQL_QUERIES['DELETE_TRACK'], (track_id, user_id))
                    conn.commit()

        except Exception as e:
            print(f"Error deleting track (track_id={track_id}, user_id={user_id}): {e}")
            raise


    @staticmethod
    def get_tracks_by_processing_method(user_id, method_name, method_value=True):
        """
        Get tracks that used specific processing method (updated for new structure)
        
        Args:
            user_id: User ID
            method_name: Processing method name (e.g., 'IQR_Outlier', 'Moving_Average')
            method_value: Boolean value to match (default True)
            
        Returns:
            List of tracks that used the specified processing method
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Updated SQL query to use new jsonb_statistics structure
                cursor.execute(SQL_QUERIES['GET_TRACKS_BY_PROCESSING_METHOD'], (
                    user_id, method_name, method_value
                ))
                tracks = cursor.fetchall()
                return tracks
    
    @staticmethod
    def get_tracks_by_distance_range(user_id, min_distance, max_distance):
        """
        Get tracks within distance range (updated for new structure)
        
        Args:
            user_id: User ID
            min_distance: Minimum distance in km
            max_distance: Maximum distance in km
            
        Returns:
            List of tracks within distance range
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Updated SQL query to use new jsonb_statistics structure
                cursor.execute(SQL_QUERIES['GET_TRACKS_BY_DISTANCE_RANGE'], (
                    user_id, min_distance, max_distance
                ))
                tracks = cursor.fetchall()
                return tracks
    
    @staticmethod
    def get_waypoints_summary(track_id, limit=10):
        """
        Get summary of waypoints for a track (new method for waypoints array)
        
        Args:
            track_id: Track ID
            limit: Maximum number of waypoints to return
            
        Returns:
            Dictionary with waypoint summary
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_TRACK_WAYPOINTS_SUMMARY'], (track_id, limit))
                result = cursor.fetchone()
                return result
    
    @staticmethod
    def get_track_metadata(track_id):
        """
        Get metadata for a specific track
        
        Args:
            track_id: Track ID
            
        Returns:
            Metadata dictionary
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['GET_TRACK_METADATA'], (track_id,))
                result = cursor.fetchone()
                return result['jsonb_metadata'] if result else None
    
    @staticmethod
    def convert_utc_to_local(dt_utc, timezone_str=TIMEZONE_STR):
        """Convert UTC datetime to local timezone"""
        if dt_utc is None:
            return None
        local_tz = pytz.timezone(timezone_str)
        if dt_utc.tzinfo is None:
            dt_utc = pytz.utc.localize(dt_utc)
        return dt_utc.astimezone(local_tz)
    
    @staticmethod
    def convert_utc_to_local_str(dt_str, timezone_str=TIMEZONE_STR):
        """Convert UTC datetime string to local timezone string"""
        if not dt_str:
            return None
        try:
            dt_utc = datetime.fromisoformat(dt_str)
            local_tz = pytz.timezone(timezone_str)
            local_dt = dt_utc.astimezone(local_tz)
            return local_dt.isoformat()
        except Exception as e:
            print(f"Error converting datetime string {dt_str}: {e}")
            return dt_str
        
    @staticmethod
    def update_visibility(track_id, is_public):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES['UPDATE_TRACK_VISIBILITY'], (is_public, track_id))
                conn.commit()
