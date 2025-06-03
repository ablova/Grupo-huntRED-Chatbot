from django.urls import path
from django.contrib.auth.decorators import login_required
from app.ats.views.workflow_views import (
    WorkflowStageListView, WorkflowStageCreateView,
    WorkflowStageUpdateView, WorkflowStageDeleteView
)

urlpatterns = [
    path('<int:business_unit_id>/stages/', 
         login_required(WorkflowStageListView.as_view()), 
         name='workflow_stage_list'),
    path('<int:business_unit_id>/stages/create/', 
         login_required(WorkflowStageCreateView.as_view()), 
         name='workflow_stage_create'),
    path('<int:business_unit_id>/stages/<int:stage_id>/update/', 
         login_required(WorkflowStageUpdateView.as_view()), 
         name='workflow_stage_update'),
    path('<int:business_unit_id>/stages/<int:stage_id>/delete/', 
         login_required(WorkflowStageDeleteView.as_view()), 
         name='workflow_stage_delete'),
] 