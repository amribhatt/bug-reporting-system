import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from config import get_database_name, BUG_REPORT_CONFIG


class IncidentDatabase:
    """Database handler for managing incidents/bug reports."""
    
    def __init__(self, db_path: str | None = None):
        """Initialize the database connection and create tables if needed."""
        self.db_path = db_path or get_database_name()
        self.init_database()
    
    def init_database(self):
        """Create the incidents table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    user_email TEXT,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    date_observed TEXT NOT NULL,
                    date_created TEXT NOT NULL,
                    status TEXT DEFAULT 'Open',
                    level INTEGER DEFAULT 2,
                    last_updated TEXT,
                    FOREIGN KEY (user_id) REFERENCES sessions(user_id)
                )
            """)
            
            # Add level column to existing table if it doesn't exist
            try:
                conn.execute("ALTER TABLE incidents ADD COLUMN level INTEGER DEFAULT 2")
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            conn.commit()
    
    def create_incident(self, user_id: str, user_name: str, user_email: str,
                       category: str, description: str, date_observed: str, level: int = 2) -> Dict:
        """Create a new incident record."""
        # Generate incident ID
        incident_count = self.get_incident_count_for_user(user_id)
        incident_id = BUG_REPORT_CONFIG["bug_id_format"].format(
            prefix=BUG_REPORT_CONFIG["bug_id_prefix"],
            id=incident_count + 1
        )
        
        date_created = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO incidents 
                (id, user_id, user_name, user_email, category, description, 
                 date_observed, date_created, status, level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (incident_id, user_id, user_name, user_email, category, 
                  description, date_observed, date_created, BUG_REPORT_CONFIG["default_status"], level))
            conn.commit()
        
        return {
            "id": incident_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email,
            "category": category,
            "description": description,
            "date_observed": date_observed,
            "date_created": date_created,
            "status": BUG_REPORT_CONFIG["default_status"],
            "level": level
        }
    
    def get_incidents_for_user(self, user_id: str) -> List[Dict]:
        """Get all incidents for a specific user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM incidents 
                WHERE user_id = ? 
                ORDER BY date_created DESC
            """, (user_id,))
            
            incidents = []
            for row in cursor.fetchall():
                incidents.append(dict(row))
            
            return incidents
    
    def get_incident_count_for_user(self, user_id: str) -> int:
        """Get the count of incidents for a user (for ID generation)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM incidents WHERE user_id = ?
            """, (user_id,))
            return cursor.fetchone()[0]
    
    def update_incident_status(self, incident_id: str, user_id: str, new_status: str) -> Optional[Dict]:
        """Update the status of an incident."""
        last_updated = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # First, get the current incident
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM incidents 
                WHERE id = ? AND user_id = ?
            """, (incident_id, user_id))
            
            incident = cursor.fetchone()
            if not incident:
                return None
            
            old_status = incident['status']
            
            # Update the status
            conn.execute("""
                UPDATE incidents 
                SET status = ?, last_updated = ?
                WHERE id = ? AND user_id = ?
            """, (new_status, last_updated, incident_id, user_id))
            conn.commit()
            
            # Return updated incident info
            updated_incident = dict(incident)
            updated_incident['status'] = new_status
            updated_incident['last_updated'] = last_updated
            updated_incident['old_status'] = old_status
            
            return updated_incident
    
    def get_incident_by_id(self, incident_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific incident by ID for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM incidents 
                WHERE id = ? AND user_id = ?
            """, (incident_id, user_id))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_incidents(self) -> List[Dict]:
        """Get all incidents (admin function)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM incidents 
                ORDER BY date_created DESC
            """)
            
            incidents = []
            for row in cursor.fetchall():
                incidents.append(dict(row))
            
            return incidents 