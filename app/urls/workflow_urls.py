#Ubicacion /home/pablollh/app/urls/workflow_urls.py

from django.urls import path
from app.views.workflow_views import (
    WorkflowStageListView,
    WorkflowStageCreateView,
    WorkflowStageUpdateView,
    WorkflowStageDeleteView
)

urlpatterns = [
    path('<int:business_unit_id>/stages/', WorkflowStageListView.as_view(), name='workflow_stage_list'),
    path('<int:business_unit_id>/stages/create/', WorkflowStageCreateView.as_view(), name='workflow_stage_create'),
    path('<int:business_unit_id>/stages/<int:stage_id>/update/', WorkflowStageUpdateView.as_view(), name='workflow_stage_update'),
    path('<int:business_unit_id>/stages/<int:stage_id>/delete/', WorkflowStageDeleteView.as_view(), name='workflow_stage_delete'),
]