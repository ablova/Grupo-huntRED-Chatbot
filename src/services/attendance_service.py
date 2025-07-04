"""
Attendance Service - Real Implementation
Complete attendance tracking with geolocation
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import uuid
import logging
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..database.models import AttendanceRecord, Employee
from ..database.database import get_db

logger = logging.getLogger(__name__)

class GeolocationService:
    """Geolocation validation service"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters using Haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    @classmethod
    def is_within_office_radius(cls, user_lat: float, user_lon: float, 
                              office_locations: List[Dict[str, float]], 
                              radius_meters: int = 100) -> Tuple[bool, Optional[str]]:
        """Check if user is within office radius"""
        for office in office_locations:
            office_lat = office.get("latitude")
            office_lon = office.get("longitude")
            office_name = office.get("name", "Oficina")
            
            if office_lat and office_lon:
                distance = cls.calculate_distance(user_lat, user_lon, office_lat, office_lon)
                if distance <= radius_meters:
                    return True, office_name
        
        return False, None

class AttendanceService:
    """Real attendance service with database operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.geo_service = GeolocationService()
    
    async def check_in(self, employee_id: str, latitude: Optional[float] = None, 
                      longitude: Optional[float] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Employee check-in with geolocation validation"""
        try:
            # Check if employee already checked in today
            today = date.today()
            existing_record = self.db.query(AttendanceRecord).filter(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    func.date(AttendanceRecord.date) == today,
                    AttendanceRecord.check_in_time.isnot(None)
                )
            ).first()
            
            if existing_record:
                return {
                    "success": False,
                    "message": "Ya tienes una entrada registrada hoy",
                    "check_in_time": existing_record.check_in_time.isoformat()
                }
            
            # Validate geolocation if provided
            location_valid = True
            office_name = None
            if latitude and longitude:
                # Get office locations (in production, this would come from company settings)
                office_locations = [
                    {"latitude": 19.4326, "longitude": -99.1332, "name": "Oficina Centro"},
                    {"latitude": 19.3910, "longitude": -99.2837, "name": "Oficina Santa Fe"}
                ]
                
                location_valid, office_name = self.geo_service.is_within_office_radius(
                    latitude, longitude, office_locations, radius_meters=200
                )
            
            if latitude and longitude and not location_valid:
                return {
                    "success": False,
                    "message": "No estás dentro del área de trabajo permitida",
                    "distance_info": "Debes estar cerca de la oficina para registrar entrada"
                }
            
            # Create attendance record
            now = datetime.now()
            attendance_record = AttendanceRecord(
                id=str(uuid.uuid4()),
                employee_id=employee_id,
                date=now,
                check_in_time=now,
                location_lat=Decimal(str(latitude)) if latitude else None,
                location_lon=Decimal(str(longitude)) if longitude else None,
                notes=notes
            )
            
            self.db.add(attendance_record)
            self.db.commit()
            self.db.refresh(attendance_record)
            
            logger.info(f"Check-in recorded for employee {employee_id}")
            
            return {
                "success": True,
                "message": f"Entrada registrada exitosamente{' en ' + office_name if office_name else ''}",
                "attendance_id": attendance_record.id,
                "check_in_time": attendance_record.check_in_time.isoformat(),
                "location": office_name,
                "coordinates": {
                    "latitude": float(latitude) if latitude else None,
                    "longitude": float(longitude) if longitude else None
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in check-in for employee {employee_id}: {e}")
            raise
    
    async def check_out(self, employee_id: str, latitude: Optional[float] = None,
                       longitude: Optional[float] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Employee check-out with hours calculation"""
        try:
            # Find today's attendance record
            today = date.today()
            attendance_record = self.db.query(AttendanceRecord).filter(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    func.date(AttendanceRecord.date) == today,
                    AttendanceRecord.check_in_time.isnot(None),
                    AttendanceRecord.check_out_time.is_(None)
                )
            ).first()
            
            if not attendance_record:
                return {
                    "success": False,
                    "message": "No tienes una entrada registrada hoy o ya registraste tu salida"
                }
            
            # Validate geolocation if provided
            location_valid = True
            office_name = None
            if latitude and longitude:
                office_locations = [
                    {"latitude": 19.4326, "longitude": -99.1332, "name": "Oficina Centro"},
                    {"latitude": 19.3910, "longitude": -99.2837, "name": "Oficina Santa Fe"}
                ]
                
                location_valid, office_name = self.geo_service.is_within_office_radius(
                    latitude, longitude, office_locations, radius_meters=200
                )
            
            if latitude and longitude and not location_valid:
                return {
                    "success": False,
                    "message": "No estás dentro del área de trabajo permitida",
                    "distance_info": "Debes estar cerca de la oficina para registrar salida"
                }
            
            # Update attendance record
            now = datetime.now()
            attendance_record.check_out_time = now
            
            # Calculate hours worked
            time_diff = now - attendance_record.check_in_time
            hours_worked = Decimal(str(time_diff.total_seconds() / 3600))
            attendance_record.hours_worked = hours_worked.quantize(Decimal('0.01'))
            
            # Update location if provided
            if latitude and longitude:
                attendance_record.location_lat = Decimal(str(latitude))
                attendance_record.location_lon = Decimal(str(longitude))
            
            # Add notes if provided
            if notes:
                existing_notes = attendance_record.notes or ""
                attendance_record.notes = f"{existing_notes}\nSalida: {notes}".strip()
            
            self.db.commit()
            self.db.refresh(attendance_record)
            
            logger.info(f"Check-out recorded for employee {employee_id}")
            
            return {
                "success": True,
                "message": f"Salida registrada exitosamente{' en ' + office_name if office_name else ''}",
                "attendance_id": attendance_record.id,
                "check_in_time": attendance_record.check_in_time.isoformat(),
                "check_out_time": attendance_record.check_out_time.isoformat(),
                "hours_worked": float(attendance_record.hours_worked),
                "location": office_name,
                "coordinates": {
                    "latitude": float(latitude) if latitude else None,
                    "longitude": float(longitude) if longitude else None
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in check-out for employee {employee_id}: {e}")
            raise
    
    async def get_attendance_status(self, employee_id: str, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get current attendance status for employee"""
        try:
            if not target_date:
                target_date = date.today()
            
            attendance_record = self.db.query(AttendanceRecord).filter(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    func.date(AttendanceRecord.date) == target_date
                )
            ).first()
            
            if not attendance_record:
                return {
                    "status": "not_checked_in",
                    "message": "No has registrado entrada hoy",
                    "date": target_date.isoformat()
                }
            
            if attendance_record.check_in_time and not attendance_record.check_out_time:
                # Calculate current hours worked
                current_time = datetime.now()
                time_diff = current_time - attendance_record.check_in_time
                current_hours = time_diff.total_seconds() / 3600
                
                return {
                    "status": "checked_in",
                    "message": "Tienes entrada registrada",
                    "check_in_time": attendance_record.check_in_time.isoformat(),
                    "hours_worked_so_far": round(current_hours, 2),
                    "date": target_date.isoformat()
                }
            
            elif attendance_record.check_in_time and attendance_record.check_out_time:
                return {
                    "status": "completed",
                    "message": "Jornada completada",
                    "check_in_time": attendance_record.check_in_time.isoformat(),
                    "check_out_time": attendance_record.check_out_time.isoformat(),
                    "hours_worked": float(attendance_record.hours_worked),
                    "date": target_date.isoformat()
                }
            
            return {
                "status": "unknown",
                "message": "Estado de asistencia desconocido",
                "date": target_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting attendance status: {e}")
            raise
    
    async def get_attendance_history(self, employee_id: str, start_date: date, 
                                   end_date: date) -> List[Dict[str, Any]]:
        """Get attendance history for employee in date range"""
        try:
            records = self.db.query(AttendanceRecord).filter(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    func.date(AttendanceRecord.date) >= start_date,
                    func.date(AttendanceRecord.date) <= end_date
                )
            ).order_by(AttendanceRecord.date.desc()).all()
            
            history = []
            for record in records:
                history.append({
                    "id": record.id,
                    "date": record.date.date().isoformat(),
                    "check_in_time": record.check_in_time.isoformat() if record.check_in_time else None,
                    "check_out_time": record.check_out_time.isoformat() if record.check_out_time else None,
                    "hours_worked": float(record.hours_worked) if record.hours_worked else None,
                    "notes": record.notes,
                    "location": {
                        "latitude": float(record.location_lat) if record.location_lat else None,
                        "longitude": float(record.location_lon) if record.location_lon else None
                    }
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting attendance history: {e}")
            raise
    
    async def get_team_attendance_summary(self, manager_id: str, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get attendance summary for manager's team"""
        try:
            if not target_date:
                target_date = date.today()
            
            # Get team members
            from .employee_service import EmployeeService
            employee_service = EmployeeService(self.db)
            team_members = await employee_service.get_employees_by_manager(manager_id)
            
            summary = {
                "date": target_date.isoformat(),
                "total_team_members": len(team_members),
                "present": 0,
                "absent": 0,
                "late": 0,
                "team_details": []
            }
            
            # Standard work start time (can be configurable)
            standard_start_time = time(9, 0)  # 9:00 AM
            
            for member in team_members:
                attendance = await self.get_attendance_status(member.id, target_date)
                
                member_info = {
                    "employee_id": member.id,
                    "name": f"{member.first_name} {member.last_name}",
                    "department": member.department,
                    "status": attendance["status"]
                }
                
                if attendance["status"] == "not_checked_in":
                    summary["absent"] += 1
                    member_info["status_text"] = "Ausente"
                elif attendance["status"] in ["checked_in", "completed"]:
                    summary["present"] += 1
                    
                    # Check if late
                    if "check_in_time" in attendance:
                        check_in_time = datetime.fromisoformat(attendance["check_in_time"]).time()
                        if check_in_time > standard_start_time:
                            summary["late"] += 1
                            member_info["late"] = True
                            member_info["status_text"] = "Presente (tarde)"
                        else:
                            member_info["status_text"] = "Presente"
                    
                    member_info["check_in_time"] = attendance.get("check_in_time")
                    member_info["hours_worked"] = attendance.get("hours_worked") or attendance.get("hours_worked_so_far")
                
                summary["team_details"].append(member_info)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting team attendance summary: {e}")
            raise