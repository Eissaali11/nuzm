"""
Migration script to rebuild GeofenceSession records from existing GeofenceEvent data.
Run this once after adding the GeofenceSession model to populate historical session data.

Usage:
    python -c "from migrations.rebuild_geofence_sessions import rebuild_sessions; rebuild_sessions()"
"""

from app import app, db
from models import GeofenceEvent, GeofenceSession, Geofence, Employee
from utils.geofence_session_manager import SessionManager
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rebuild_sessions(clear_existing=False):
    """
    Rebuild all GeofenceSession records from existing GeofenceEvent data.
    This migration is idempotent - it will skip events that already have sessions.
    
    Args:
        clear_existing: If True, delete all existing sessions before rebuilding (default: False)
    """
    with app.app_context():
        logger.info("Starting GeofenceSession rebuild migration...")
        
        # Option to clear existing sessions
        if clear_existing:
            logger.warning("Clearing all existing GeofenceSession records...")
            GeofenceSession.query.delete()
            db.session.commit()
            logger.info("All existing sessions cleared.")
        
        # Get all geofences
        geofences = Geofence.query.all()
        
        total_events = 0
        total_sessions_created = 0
        total_sessions_updated = 0
        
        for geofence in geofences:
            logger.info(f"Processing geofence: {geofence.name} (ID: {geofence.id})")
            
            # Get all events for this geofence, ordered by time
            events = GeofenceEvent.query.filter_by(
                geofence_id=geofence.id
            ).order_by(
                GeofenceEvent.recorded_at.asc()
            ).all()
            
            logger.info(f"  Found {len(events)} events")
            
            # Process events per employee
            employee_events = {}
            for event in events:
                if event.employee_id not in employee_events:
                    employee_events[event.employee_id] = []
                employee_events[event.employee_id].append(event)
            
            # Process each employee's events
            session_manager = SessionManager()
            
            for employee_id, emp_events in employee_events.items():
                logger.info(f"  Processing {len(emp_events)} events for employee {employee_id}")
                
                for event in emp_events:
                    total_events += 1
                    
                    # Skip events that already have associated sessions (idempotency check)
                    if event.event_type == 'enter':
                        existing_session = GeofenceSession.query.filter_by(
                            entry_event_id=event.id
                        ).first()
                        if existing_session:
                            logger.debug(f"    Skipping enter event {event.id} - already has session")
                            continue
                    
                    elif event.event_type == 'exit':
                        existing_session = GeofenceSession.query.filter_by(
                            exit_event_id=event.id
                        ).first()
                        if existing_session:
                            logger.debug(f"    Skipping exit event {event.id} - already has session")
                            continue
                    
                    try:
                        if event.event_type == 'enter':
                            session = session_manager.process_enter_event(employee_id, geofence.id, event)
                            if session:
                                total_sessions_created += 1
                                logger.debug(f"    Created session for enter event at {event.recorded_at}")
                        
                        elif event.event_type == 'exit':
                            session = session_manager.process_exit_event(employee_id, geofence.id, event)
                            if session:
                                if session.exit_time:
                                    total_sessions_updated += 1
                                    logger.debug(f"    Updated session for exit event at {event.recorded_at}")
                                else:
                                    total_sessions_created += 1
                                    logger.debug(f"    Created synthetic session for exit event at {event.recorded_at}")
                    
                    except Exception as e:
                        logger.error(f"    Error processing event {event.id}: {str(e)}")
                        continue
                
                # Commit after each employee to avoid losing progress
                db.session.commit()
        
        logger.info("Migration completed!")
        logger.info(f"  Total events processed: {total_events}")
        logger.info(f"  Sessions created: {total_sessions_created}")
        logger.info(f"  Sessions updated: {total_sessions_updated}")
        
        # Summary statistics
        total_sessions = GeofenceSession.query.count()
        active_sessions = GeofenceSession.query.filter_by(is_active=True).count()
        closed_sessions = GeofenceSession.query.filter_by(is_active=False).count()
        
        logger.info(f"\nFinal statistics:")
        logger.info(f"  Total sessions in database: {total_sessions}")
        logger.info(f"  Active sessions: {active_sessions}")
        logger.info(f"  Closed sessions: {closed_sessions}")
        
        return {
            'events_processed': total_events,
            'sessions_created': total_sessions_created,
            'sessions_updated': total_sessions_updated,
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'closed_sessions': closed_sessions
        }


if __name__ == '__main__':
    rebuild_sessions()
