"""
HuntRED® v2 - Dashboards Service
Complete interactive dashboards and data visualization system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum
import math

logger = logging.getLogger(__name__)

class DashboardType(Enum):
    EXECUTIVE = "executive"
    HR_ANALYTICS = "hr_analytics"
    PAYROLL = "payroll"
    ATTENDANCE = "attendance"
    PERFORMANCE = "performance"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOM = "custom"

class WidgetType(Enum):
    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    AREA_CHART = "area_chart"
    HEATMAP = "heatmap"
    TABLE = "table"
    GAUGE = "gauge"
    PROGRESS_BAR = "progress_bar"
    METRIC_TREND = "metric_trend"
    FUNNEL_CHART = "funnel_chart"
    SCATTER_PLOT = "scatter_plot"
    CALENDAR_HEATMAP = "calendar_heatmap"

class RefreshFrequency(Enum):
    REAL_TIME = "real_time"
    EVERY_MINUTE = "every_minute"
    EVERY_5_MINUTES = "every_5_minutes"
    EVERY_15_MINUTES = "every_15_minutes"
    EVERY_HOUR = "every_hour"
    DAILY = "daily"
    MANUAL = "manual"

class DashboardsService:
    """Complete dashboards and data visualization system"""
    
    def __init__(self, db):
        self.db = db
        
        # Predefined dashboard templates
        self.dashboard_templates = {
            "executive_overview": {
                "name": "Executive Overview",
                "description": "High-level company metrics for executives",
                "type": DashboardType.EXECUTIVE.value,
                "refresh_frequency": RefreshFrequency.EVERY_15_MINUTES.value,
                "widgets": [
                    {
                        "id": "total_employees",
                        "type": WidgetType.KPI_CARD.value,
                        "title": "Total Employees",
                        "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                        "data_source": "employees_count",
                        "config": {
                            "icon": "users",
                            "color": "blue",
                            "trend": True,
                            "comparison": "previous_month"
                        }
                    },
                    {
                        "id": "monthly_payroll",
                        "type": WidgetType.KPI_CARD.value,
                        "title": "Monthly Payroll",
                        "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                        "data_source": "payroll_total",
                        "config": {
                            "icon": "dollar-sign",
                            "color": "green",
                            "format": "currency",
                            "trend": True
                        }
                    },
                    {
                        "id": "attendance_rate",
                        "type": WidgetType.GAUGE.value,
                        "title": "Attendance Rate",
                        "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                        "data_source": "attendance_rate",
                        "config": {
                            "min": 0,
                            "max": 100,
                            "unit": "%",
                            "thresholds": [
                                {"value": 85, "color": "red"},
                                {"value": 95, "color": "yellow"},
                                {"value": 100, "color": "green"}
                            ]
                        }
                    },
                    {
                        "id": "turnover_rate",
                        "type": WidgetType.KPI_CARD.value,
                        "title": "Turnover Rate",
                        "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                        "data_source": "turnover_rate",
                        "config": {
                            "icon": "trending-down",
                            "color": "red",
                            "format": "percentage",
                            "trend": True,
                            "invert_trend": True
                        }
                    },
                    {
                        "id": "revenue_trend",
                        "type": WidgetType.LINE_CHART.value,
                        "title": "Revenue Trend (12 months)",
                        "position": {"x": 0, "y": 2, "width": 6, "height": 4},
                        "data_source": "revenue_monthly",
                        "config": {
                            "x_axis": "month",
                            "y_axis": "revenue",
                            "color": "#10B981",
                            "smooth": True,
                            "show_points": True
                        }
                    },
                    {
                        "id": "department_headcount",
                        "type": WidgetType.BAR_CHART.value,
                        "title": "Headcount by Department",
                        "position": {"x": 6, "y": 2, "width": 6, "height": 4},
                        "data_source": "department_headcount",
                        "config": {
                            "x_axis": "department",
                            "y_axis": "count",
                            "color": "#3B82F6",
                            "horizontal": True
                        }
                    },
                    {
                        "id": "budget_utilization",
                        "type": WidgetType.PROGRESS_BAR.value,
                        "title": "Budget Utilization by Department",
                        "position": {"x": 0, "y": 6, "width": 12, "height": 3},
                        "data_source": "budget_utilization",
                        "config": {
                            "show_percentage": True,
                            "color_scheme": "gradient",
                            "stacked": False
                        }
                    }
                ]
            },
            "hr_analytics": {
                "name": "HR Analytics Dashboard",
                "description": "Comprehensive HR metrics and analytics",
                "type": DashboardType.HR_ANALYTICS.value,
                "refresh_frequency": RefreshFrequency.EVERY_HOUR.value,
                "widgets": [
                    {
                        "id": "employee_satisfaction",
                        "type": WidgetType.GAUGE.value,
                        "title": "Employee Satisfaction Score",
                        "position": {"x": 0, "y": 0, "width": 4, "height": 3},
                        "data_source": "satisfaction_score",
                        "config": {
                            "min": 1,
                            "max": 5,
                            "unit": "/5",
                            "decimals": 1
                        }
                    },
                    {
                        "id": "hiring_funnel",
                        "type": WidgetType.FUNNEL_CHART.value,
                        "title": "Hiring Funnel",
                        "position": {"x": 4, "y": 0, "width": 4, "height": 3},
                        "data_source": "hiring_funnel",
                        "config": {
                            "stages": ["Applications", "Screening", "Interviews", "Offers", "Hires"],
                            "colors": ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6"]
                        }
                    },
                    {
                        "id": "diversity_metrics",
                        "type": WidgetType.PIE_CHART.value,
                        "title": "Workforce Diversity",
                        "position": {"x": 8, "y": 0, "width": 4, "height": 3},
                        "data_source": "diversity_metrics",
                        "config": {
                            "category": "gender",
                            "show_labels": True,
                            "show_percentages": True
                        }
                    },
                    {
                        "id": "retention_by_tenure",
                        "type": WidgetType.BAR_CHART.value,
                        "title": "Retention Rate by Tenure",
                        "position": {"x": 0, "y": 3, "width": 6, "height": 4},
                        "data_source": "retention_by_tenure",
                        "config": {
                            "x_axis": "tenure_range",
                            "y_axis": "retention_rate",
                            "color": "#6366F1"
                        }
                    },
                    {
                        "id": "performance_distribution",
                        "type": WidgetType.AREA_CHART.value,
                        "title": "Performance Score Distribution",
                        "position": {"x": 6, "y": 3, "width": 6, "height": 4},
                        "data_source": "performance_distribution",
                        "config": {
                            "x_axis": "score_range",
                            "y_axis": "employee_count",
                            "fill": True,
                            "color": "#F59E0B"
                        }
                    },
                    {
                        "id": "training_completion",
                        "type": WidgetType.HEATMAP.value,
                        "title": "Training Completion by Department",
                        "position": {"x": 0, "y": 7, "width": 12, "height": 4},
                        "data_source": "training_completion",
                        "config": {
                            "x_axis": "department",
                            "y_axis": "training_program",
                            "value": "completion_rate",
                            "color_scale": "green"
                        }
                    }
                ]
            },
            "payroll_dashboard": {
                "name": "Payroll Dashboard",
                "description": "Payroll processing and cost analysis",
                "type": DashboardType.PAYROLL.value,
                "refresh_frequency": RefreshFrequency.DAILY.value,
                "widgets": [
                    {
                        "id": "total_payroll_cost",
                        "type": WidgetType.KPI_CARD.value,
                        "title": "Total Payroll Cost",
                        "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                        "data_source": "total_payroll",
                        "config": {
                            "format": "currency",
                            "icon": "credit-card",
                            "color": "blue"
                        }
                    },
                    {
                        "id": "avg_salary",
                        "type": WidgetType.KPI_CARD.value,
                        "title": "Average Salary",
                        "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                        "data_source": "average_salary",
                        "config": {
                            "format": "currency",
                            "icon": "trending-up",
                            "color": "green"
                        }
                    },
                    {
                        "id": "payroll_by_department",
                        "type": WidgetType.DONUT_CHART.value,
                        "title": "Payroll Cost by Department",
                        "position": {"x": 6, "y": 0, "width": 6, "height": 4},
                        "data_source": "payroll_by_department",
                        "config": {
                            "show_labels": True,
                            "show_values": True,
                            "format": "currency"
                        }
                    },
                    {
                        "id": "overtime_trend",
                        "type": WidgetType.LINE_CHART.value,
                        "title": "Overtime Hours Trend",
                        "position": {"x": 0, "y": 2, "width": 6, "height": 4},
                        "data_source": "overtime_trend",
                        "config": {
                            "x_axis": "month",
                            "y_axis": "overtime_hours",
                            "color": "#EF4444"
                        }
                    },
                    {
                        "id": "payroll_compliance",
                        "type": WidgetType.TABLE.value,
                        "title": "Payroll Compliance Status",
                        "position": {"x": 0, "y": 6, "width": 12, "height": 4},
                        "data_source": "payroll_compliance",
                        "config": {
                            "columns": ["Employee", "IMSS Status", "ISR Status", "INFONAVIT Status", "Last Updated"],
                            "sortable": True,
                            "filterable": True,
                            "pagination": True
                        }
                    }
                ]
            }
        }
        
        # Color palettes for charts
        self.color_palettes = {
            "default": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"],
            "blue": ["#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD", "#DBEAFE"],
            "green": ["#065F46", "#10B981", "#34D399", "#6EE7B7", "#A7F3D0"],
            "red": ["#991B1B", "#EF4444", "#F87171", "#FCA5A5", "#FEE2E2"],
            "purple": ["#581C87", "#8B5CF6", "#A78BFA", "#C4B5FD", "#E9D5FF"],
            "gradient": ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe"]
        }
    
    async def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard"""
        try:
            dashboard_id = str(uuid.uuid4())
            
            # Use template if specified
            template_name = dashboard_data.get("template")
            if template_name and template_name in self.dashboard_templates:
                template = self.dashboard_templates[template_name]
                # Merge template with provided data
                for key, value in template.items():
                    if key not in dashboard_data:
                        dashboard_data[key] = value
            
            # Create dashboard
            dashboard = {
                "id": dashboard_id,
                "name": dashboard_data["name"],
                "description": dashboard_data.get("description", ""),
                "type": dashboard_data.get("type", DashboardType.CUSTOM.value),
                "owner_id": dashboard_data.get("owner_id"),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "settings": {
                    "refresh_frequency": dashboard_data.get("refresh_frequency", RefreshFrequency.EVERY_15_MINUTES.value),
                    "auto_refresh": dashboard_data.get("auto_refresh", True),
                    "theme": dashboard_data.get("theme", "light"),
                    "grid_size": dashboard_data.get("grid_size", {"columns": 12, "rows": 12}),
                    "responsive": dashboard_data.get("responsive", True)
                },
                "permissions": {
                    "viewers": dashboard_data.get("viewers", []),
                    "editors": dashboard_data.get("editors", []),
                    "public": dashboard_data.get("public", False)
                },
                "widgets": dashboard_data.get("widgets", []),
                "filters": dashboard_data.get("filters", []),
                "metadata": {
                    "tags": dashboard_data.get("tags", []),
                    "category": dashboard_data.get("category"),
                    "version": 1
                }
            }
            
            # Validate dashboard
            validation_result = await self._validate_dashboard(dashboard)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Initialize widget data
            for widget in dashboard["widgets"]:
                widget["id"] = widget.get("id", str(uuid.uuid4()))
                widget["created_at"] = datetime.now()
                widget["last_updated"] = datetime.now()
            
            # Save dashboard
            # await self._save_dashboard(dashboard)
            
            logger.info(f"Dashboard {dashboard_id} created successfully")
            
            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "dashboard": dashboard
            }
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_dashboard(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Validate dashboard configuration"""
        
        # Check required fields
        if not dashboard.get("name"):
            return {"valid": False, "error": "Dashboard name is required"}
        
        # Validate widgets
        widgets = dashboard.get("widgets", [])
        for widget in widgets:
            if not widget.get("type"):
                return {"valid": False, "error": "Widget type is required"}
            
            if not widget.get("data_source"):
                return {"valid": False, "error": f"Data source required for widget {widget.get('title', 'Untitled')}"}
            
            # Validate position
            position = widget.get("position", {})
            required_pos_fields = ["x", "y", "width", "height"]
            for field in required_pos_fields:
                if field not in position:
                    return {"valid": False, "error": f"Widget position {field} is required"}
        
        return {"valid": True}
    
    async def get_dashboard_data(self, dashboard_id: str, 
                               date_range: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get dashboard with real-time data"""
        try:
            # Get dashboard configuration
            dashboard = await self._get_dashboard(dashboard_id)
            if not dashboard:
                return {"success": False, "error": "Dashboard not found"}
            
            # Set default date range if not provided
            if not date_range:
                date_range = {
                    "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "end_date": datetime.now().isoformat()
                }
            
            # Load data for each widget
            widget_data = {}
            for widget in dashboard["widgets"]:
                try:
                    data = await self._load_widget_data(widget, date_range)
                    widget_data[widget["id"]] = data
                except Exception as e:
                    logger.error(f"Error loading data for widget {widget['id']}: {e}")
                    widget_data[widget["id"]] = {"error": str(e)}
            
            # Apply dashboard filters
            if dashboard.get("filters"):
                widget_data = await self._apply_dashboard_filters(widget_data, dashboard["filters"])
            
            # Calculate dashboard metrics
            dashboard_metrics = await self._calculate_dashboard_metrics(dashboard, widget_data)
            
            result = {
                "success": True,
                "dashboard": dashboard,
                "widget_data": widget_data,
                "metrics": dashboard_metrics,
                "generated_at": datetime.now(),
                "date_range": date_range
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Get dashboard configuration"""
        # Mock implementation - in real app, query from database
        if dashboard_id == "exec_dashboard":
            return self.dashboard_templates["executive_overview"]
        elif dashboard_id == "hr_dashboard":
            return self.dashboard_templates["hr_analytics"]
        elif dashboard_id == "payroll_dashboard":
            return self.dashboard_templates["payroll_dashboard"]
        
        return None
    
    async def _load_widget_data(self, widget: Dict[str, Any], 
                              date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Load data for a specific widget"""
        
        data_source = widget["data_source"]
        widget_type = widget["type"]
        
        # Mock data generation based on data source
        if data_source == "employees_count":
            return await self._generate_employees_count_data(date_range)
        elif data_source == "payroll_total":
            return await self._generate_payroll_total_data(date_range)
        elif data_source == "attendance_rate":
            return await self._generate_attendance_rate_data(date_range)
        elif data_source == "turnover_rate":
            return await self._generate_turnover_rate_data(date_range)
        elif data_source == "revenue_monthly":
            return await self._generate_revenue_trend_data(date_range)
        elif data_source == "department_headcount":
            return await self._generate_department_headcount_data()
        elif data_source == "budget_utilization":
            return await self._generate_budget_utilization_data()
        elif data_source == "satisfaction_score":
            return await self._generate_satisfaction_score_data()
        elif data_source == "hiring_funnel":
            return await self._generate_hiring_funnel_data()
        elif data_source == "diversity_metrics":
            return await self._generate_diversity_metrics_data()
        elif data_source == "retention_by_tenure":
            return await self._generate_retention_by_tenure_data()
        elif data_source == "performance_distribution":
            return await self._generate_performance_distribution_data()
        elif data_source == "training_completion":
            return await self._generate_training_completion_data()
        elif data_source == "average_salary":
            return await self._generate_average_salary_data()
        elif data_source == "payroll_by_department":
            return await self._generate_payroll_by_department_data()
        elif data_source == "overtime_trend":
            return await self._generate_overtime_trend_data(date_range)
        elif data_source == "payroll_compliance":
            return await self._generate_payroll_compliance_data()
        else:
            return {"error": f"Unknown data source: {data_source}"}
    
    async def _generate_employees_count_data(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate employees count data"""
        return {
            "value": 247,
            "previous_value": 235,
            "change": 12,
            "change_percentage": 5.1,
            "trend": "up",
            "format": "number"
        }
    
    async def _generate_payroll_total_data(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate payroll total data"""
        return {
            "value": 12750000.00,
            "previous_value": 12350000.00,
            "change": 400000.00,
            "change_percentage": 3.2,
            "trend": "up",
            "format": "currency",
            "currency": "MXN"
        }
    
    async def _generate_attendance_rate_data(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate attendance rate data"""
        return {
            "value": 94.2,
            "min": 0,
            "max": 100,
            "unit": "%",
            "status": "good",
            "threshold_color": "green"
        }
    
    async def _generate_turnover_rate_data(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate turnover rate data"""
        return {
            "value": 8.5,
            "previous_value": 12.3,
            "change": -3.8,
            "change_percentage": -30.9,
            "trend": "down",
            "format": "percentage",
            "status": "good"
        }
    
    async def _generate_revenue_trend_data(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate revenue trend data"""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        revenue_data = [
            {"month": month, "revenue": 8500000 + (i * 150000) + (math.sin(i) * 500000)}
            for i, month in enumerate(months)
        ]
        
        return {
            "data": revenue_data,
            "x_axis": "month",
            "y_axis": "revenue",
            "format": "currency",
            "currency": "MXN"
        }
    
    async def _generate_department_headcount_data(self) -> Dict[str, Any]:
        """Generate department headcount data"""
        departments = [
            {"department": "Tecnología", "count": 85},
            {"department": "Ventas", "count": 62},
            {"department": "Marketing", "count": 28},
            {"department": "RRHH", "count": 15},
            {"department": "Finanzas", "count": 18},
            {"department": "Operaciones", "count": 39}
        ]
        
        return {
            "data": departments,
            "x_axis": "department",
            "y_axis": "count"
        }
    
    async def _generate_budget_utilization_data(self) -> Dict[str, Any]:
        """Generate budget utilization data"""
        departments = [
            {"department": "Tecnología", "allocated": 5000000, "spent": 3750000, "percentage": 75.0},
            {"department": "Ventas", "allocated": 3000000, "spent": 2400000, "percentage": 80.0},
            {"department": "Marketing", "allocated": 2000000, "spent": 1600000, "percentage": 80.0},
            {"department": "RRHH", "allocated": 1500000, "spent": 1200000, "percentage": 80.0},
            {"department": "Finanzas", "allocated": 1000000, "spent": 750000, "percentage": 75.0},
            {"department": "Operaciones", "allocated": 2500000, "spent": 1875000, "percentage": 75.0}
        ]
        
        return {
            "data": departments,
            "category": "department",
            "value": "percentage",
            "format": "percentage"
        }
    
    async def _generate_satisfaction_score_data(self) -> Dict[str, Any]:
        """Generate satisfaction score data"""
        return {
            "value": 4.2,
            "min": 1,
            "max": 5,
            "unit": "/5",
            "status": "good",
            "benchmark": 3.8,
            "industry_avg": 3.9
        }
    
    async def _generate_hiring_funnel_data(self) -> Dict[str, Any]:
        """Generate hiring funnel data"""
        funnel_data = [
            {"stage": "Applications", "count": 1250, "percentage": 100.0},
            {"stage": "Screening", "count": 375, "percentage": 30.0},
            {"stage": "Interviews", "count": 125, "percentage": 10.0},
            {"stage": "Offers", "count": 25, "percentage": 2.0},
            {"stage": "Hires", "count": 18, "percentage": 1.4}
        ]
        
        return {
            "data": funnel_data,
            "stage": "stage",
            "value": "count",
            "conversion_rates": [30.0, 33.3, 20.0, 72.0]
        }
    
    async def _generate_diversity_metrics_data(self) -> Dict[str, Any]:
        """Generate diversity metrics data"""
        diversity_data = [
            {"category": "Mujeres", "count": 142, "percentage": 57.5},
            {"category": "Hombres", "count": 105, "percentage": 42.5}
        ]
        
        return {
            "data": diversity_data,
            "category": "category",
            "value": "percentage",
            "format": "percentage"
        }
    
    async def _generate_retention_by_tenure_data(self) -> Dict[str, Any]:
        """Generate retention by tenure data"""
        tenure_data = [
            {"tenure_range": "0-6 months", "retention_rate": 85.2},
            {"tenure_range": "6-12 months", "retention_rate": 92.1},
            {"tenure_range": "1-2 years", "retention_rate": 94.8},
            {"tenure_range": "2-5 years", "retention_rate": 96.3},
            {"tenure_range": "5+ years", "retention_rate": 98.1}
        ]
        
        return {
            "data": tenure_data,
            "x_axis": "tenure_range",
            "y_axis": "retention_rate",
            "format": "percentage"
        }
    
    async def _generate_performance_distribution_data(self) -> Dict[str, Any]:
        """Generate performance distribution data"""
        performance_data = [
            {"score_range": "1.0-2.0", "employee_count": 8},
            {"score_range": "2.0-3.0", "employee_count": 25},
            {"score_range": "3.0-4.0", "employee_count": 142},
            {"score_range": "4.0-5.0", "employee_count": 72}
        ]
        
        return {
            "data": performance_data,
            "x_axis": "score_range",
            "y_axis": "employee_count"
        }
    
    async def _generate_training_completion_data(self) -> Dict[str, Any]:
        """Generate training completion heatmap data"""
        departments = ["Tecnología", "Ventas", "Marketing", "RRHH", "Finanzas"]
        programs = ["Seguridad", "Compliance", "Liderazgo", "Técnico", "Soft Skills"]
        
        heatmap_data = []
        for dept in departments:
            for program in programs:
                completion_rate = 60 + (hash(f"{dept}{program}") % 40)  # Mock data 60-100%
                heatmap_data.append({
                    "department": dept,
                    "training_program": program,
                    "completion_rate": completion_rate
                })
        
        return {
            "data": heatmap_data,
            "x_axis": "department",
            "y_axis": "training_program",
            "value": "completion_rate",
            "format": "percentage"
        }
    
    async def _generate_average_salary_data(self) -> Dict[str, Any]:
        """Generate average salary data"""
        return {
            "value": 51650.00,
            "previous_value": 49800.00,
            "change": 1850.00,
            "change_percentage": 3.7,
            "trend": "up",
            "format": "currency",
            "currency": "MXN"
        }
    
    async def _generate_payroll_by_department_data(self) -> Dict[str, Any]:
        """Generate payroll by department data"""
        payroll_data = [
            {"department": "Tecnología", "amount": 4387500, "percentage": 34.4},
            {"department": "Ventas", "amount": 3201250, "percentage": 25.1},
            {"department": "Marketing", "amount": 1446250, "percentage": 11.3},
            {"department": "RRHH", "amount": 775000, "percentage": 6.1},
            {"department": "Finanzas", "amount": 929750, "percentage": 7.3},
            {"department": "Operaciones", "amount": 2010250, "percentage": 15.8}
        ]
        
        return {
            "data": payroll_data,
            "category": "department",
            "value": "amount",
            "format": "currency",
            "currency": "MXN"
        }
    
    async def _generate_overtime_trend_data(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overtime trend data"""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        overtime_data = [
            {"month": month, "overtime_hours": 450 + (i * 25) + (math.sin(i) * 100)}
            for i, month in enumerate(months)
        ]
        
        return {
            "data": overtime_data,
            "x_axis": "month",
            "y_axis": "overtime_hours",
            "format": "number",
            "unit": "hours"
        }
    
    async def _generate_payroll_compliance_data(self) -> Dict[str, Any]:
        """Generate payroll compliance table data"""
        employees = [
            {
                "Employee": "Juan Pérez",
                "IMSS Status": "✅ Compliant",
                "ISR Status": "✅ Compliant", 
                "INFONAVIT Status": "✅ Compliant",
                "Last Updated": "2024-01-15"
            },
            {
                "Employee": "María García",
                "IMSS Status": "✅ Compliant",
                "ISR Status": "⚠️ Pending",
                "INFONAVIT Status": "✅ Compliant",
                "Last Updated": "2024-01-14"
            },
            {
                "Employee": "Carlos López",
                "IMSS Status": "❌ Issue",
                "ISR Status": "✅ Compliant",
                "INFONAVIT Status": "✅ Compliant",
                "Last Updated": "2024-01-13"
            }
        ]
        
        return {
            "data": employees,
            "total_records": len(employees),
            "page": 1,
            "per_page": 10
        }
    
    async def _apply_dashboard_filters(self, widget_data: Dict[str, Any], 
                                     filters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply dashboard-level filters to widget data"""
        # Mock filter application
        return widget_data
    
    async def _calculate_dashboard_metrics(self, dashboard: Dict[str, Any], 
                                         widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall dashboard metrics"""
        
        metrics = {
            "total_widgets": len(dashboard["widgets"]),
            "widgets_with_data": len([w for w in widget_data.values() if "error" not in w]),
            "widgets_with_errors": len([w for w in widget_data.values() if "error" in w]),
            "data_freshness": datetime.now(),
            "load_time_ms": 250,  # Mock load time
            "cache_hit_rate": 85.2
        }
        
        return metrics
    
    async def create_custom_widget(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom widget"""
        try:
            widget_id = str(uuid.uuid4())
            
            widget = {
                "id": widget_id,
                "title": widget_data["title"],
                "type": widget_data["type"],
                "data_source": widget_data["data_source"],
                "position": widget_data.get("position", {"x": 0, "y": 0, "width": 4, "height": 3}),
                "config": widget_data.get("config", {}),
                "created_at": datetime.now(),
                "created_by": widget_data.get("created_by"),
                "query": widget_data.get("query"),  # Custom SQL/query for data
                "refresh_interval": widget_data.get("refresh_interval", 300),  # seconds
                "filters": widget_data.get("filters", [])
            }
            
            # Validate widget
            validation_result = await self._validate_widget(widget)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Save widget
            # await self._save_widget(widget)
            
            logger.info(f"Custom widget {widget_id} created successfully")
            
            return {
                "success": True,
                "widget_id": widget_id,
                "widget": widget
            }
            
        except Exception as e:
            logger.error(f"Error creating custom widget: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_widget(self, widget: Dict[str, Any]) -> Dict[str, Any]:
        """Validate widget configuration"""
        
        required_fields = ["title", "type", "data_source"]
        for field in required_fields:
            if not widget.get(field):
                return {"valid": False, "error": f"Widget {field} is required"}
        
        # Validate widget type
        valid_types = [wt.value for wt in WidgetType]
        if widget["type"] not in valid_types:
            return {"valid": False, "error": f"Invalid widget type: {widget['type']}"}
        
        return {"valid": True}
    
    async def export_dashboard(self, dashboard_id: str, format: str = "pdf") -> Dict[str, Any]:
        """Export dashboard to various formats"""
        try:
            # Get dashboard data
            dashboard_data = await self.get_dashboard_data(dashboard_id)
            if not dashboard_data["success"]:
                return dashboard_data
            
            export_id = str(uuid.uuid4())
            
            if format == "pdf":
                export_result = await self._export_to_pdf(dashboard_data, export_id)
            elif format == "excel":
                export_result = await self._export_to_excel(dashboard_data, export_id)
            elif format == "image":
                export_result = await self._export_to_image(dashboard_data, export_id)
            else:
                return {"success": False, "error": f"Unsupported export format: {format}"}
            
            return {
                "success": True,
                "export_id": export_id,
                "format": format,
                "file_url": export_result["file_url"],
                "generated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error exporting dashboard: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_to_pdf(self, dashboard_data: Dict[str, Any], export_id: str) -> Dict[str, Any]:
        """Export dashboard to PDF"""
        # Mock PDF generation
        file_url = f"/exports/{export_id}.pdf"
        return {"file_url": file_url}
    
    async def _export_to_excel(self, dashboard_data: Dict[str, Any], export_id: str) -> Dict[str, Any]:
        """Export dashboard data to Excel"""
        # Mock Excel generation
        file_url = f"/exports/{export_id}.xlsx"
        return {"file_url": file_url}
    
    async def _export_to_image(self, dashboard_data: Dict[str, Any], export_id: str) -> Dict[str, Any]:
        """Export dashboard to image"""
        # Mock image generation
        file_url = f"/exports/{export_id}.png"
        return {"file_url": file_url}
    
    async def get_dashboard_analytics(self, dashboard_id: str, 
                                    date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Get analytics for dashboard usage"""
        try:
            # Mock analytics data
            analytics = {
                "dashboard_id": dashboard_id,
                "period": date_range,
                "usage_metrics": {
                    "total_views": 1250,
                    "unique_viewers": 45,
                    "avg_session_duration": "8.5 minutes",
                    "bounce_rate": 12.3,
                    "most_viewed_widgets": [
                        {"widget_id": "total_employees", "views": 890},
                        {"widget_id": "revenue_trend", "views": 750},
                        {"widget_id": "attendance_rate", "views": 680}
                    ]
                },
                "performance_metrics": {
                    "avg_load_time": "2.1 seconds",
                    "cache_hit_rate": 87.5,
                    "error_rate": 0.8,
                    "uptime": 99.9
                },
                "user_engagement": {
                    "interactions_per_session": 12.3,
                    "filter_usage": 68.2,
                    "export_requests": 23,
                    "sharing_frequency": 8.5
                }
            }
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard analytics: {e}")
            return {"success": False, "error": str(e)}

# Global dashboards service
def get_dashboards_service(db) -> DashboardsService:
    """Get dashboards service instance"""
    return DashboardsService(db)