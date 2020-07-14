"""sdrc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views

from sdrc import settings

app_name = 'sdrc'

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^request_reimbursement/$', views.request_reimbursement, name='request_reimbursement'),
    url(r'^milestone_list/$', views.milestone_list, name='milestone_list'),
    url(r'^task_list/$', views.task_list, name='task_list'),
    url(r'^member_list/$', views.member_list, name='member_list'),
    url(r'^(?P<id>\d+)/update-budget-plan/$', views.updateBudgetPlan, name='update-budget-plan'),
    url(r'^incidentreport_summary/$', views.incidentreport_summary, name='incidentreport_summary'),
    url(r'^user_list/$', views.user_list, name='user_list'),
    url(r'^projectbudget_overview/$', views.projectbudget_overview, name='projectbudget_overview'),
    url(r'^view_reimbursements/$', views.view_reimbursements, name='view_reimbursements'),
    url(r'^request_cashadvance/$', views.cashadvance, name='cashadvance'),
    url(r'^view_cashadvance/$', views.cashadvance_admin, name='cashadvance_admin'),
    url(r'^request_procurement/$', views.requestprocurement, name='requestprocurement'),
    url(r'^view_procurement/$', views.requestprocurement_admin, name='requestprocurement_admin'),
url(r'^requestbudgetextension/$', views.request_budget_extension, name='request_budget_extension'),
    url(r'^change_password/$', views.change_password, name='change_password'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^password_reset/$', auth_views.PasswordResetView.as_view(), name='password_reset'),
    url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^password_reset/complete/$', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='sdrc/login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(template_name='sdrc/login.html'), name='logout'),
    url(r'^create-budget-plan/$', views.create_budget, name='create-budget-plan'),
    url(r'^view-budget-plan/$', views.budget_plan_create, name='create-budget'),
    url(r'^create-expense-tracker/$', views.create_expense_tracker, name='create-expense-tracker'),
    url(r'^create-project-account/$', views.create_project_account, name='create-account'),
    url(r'^adminindex/$', views.AdminIndexView.as_view(), name='adminindex'),
    url(r'^view_reallocation/$', views.view_reallocation, name='adminindex'),
    url(r'^viewpastprojects/$', views.view_past_projects, name='pastprojects'),
    url(r'^systemlocked/$', views.dashboard_locked, name='systemlocked'),
    url(r'^ganttchart/$', views.GanttChartView, name='ganttchart'),
    url(r'^request_final/$', views.request_final, name='request_final'),
    url(r'^addmembers/$', views.add_members, name='addmembers'),
    url(r'^create-budget-details/$', views.create_budget_details, name='create-budget'),
    url(r'^view_projectextension/$', views.projectextension, name='projectextension'),
    url(r'^expensereport/$', views.expense_report, name='expense-report'),
    url(r'^budget-status/$', views.view_budget_status, name='budget-status', ),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^incidentreport/$', views.IncidentReportsView, name='incidentreport'),
    url(r'^createmilestone/$', views.create_project, name='createmilestone'),
    url(r'^resolvedissues/$', views.resolved_issues, name='resolvedissues'),
    url(r'^samplegantt/$', views.SampleGanttView, name='samplegantt'),
    url(r'^budgetextension/$', views.view_budget_extension, name='budgetextension'),
    url(r'^tor-DLSU/$', views.create_term_of_reference_DLSU, name='tor-DLSU'),
    url(r'^piindex/$', views.PIIndexView, name='piindex'),
    url(r'^view-projects/$', views.view_projects, name='view-projects'),
    url(r'^projectcharter/$', views.create_project_charter, name='projectcharter'),
    url(r'^appointmentform/$', views.AppointmentFormView.as_view(), name='appointmentform'),
    url(r'^createincidentreport/$', views.incident_report_post, name='createincidentreport'),
    url(r'^expensetracking/$', views.ExpenseTracking, name='expensetracking'),
    url(r'^(?P<id>\d+)/update-project/$', views.update_project_account, name='update'),
    url(r'^expenselist/$', views.ExpenseListView.as_view(), name='expenselist'),
    url(r'^budgetextensionform/$', views.budget_extension_form, name='budgetextensionform'),
    url(r'^uploadprojectinformation/$', views.UploadProjectInformationView.as_view(), name='uploadprojectinformation'),
    url(r'^milestonestatus/$', views.MilestoneStatusView, name='milestonestatus'),
    url(r'^financialreport/$', views.FinancialReportView.as_view(), name='financialreport'),
    url(r'^viewprojectstatus/$', views.ProjectStatusView.as_view(), name='projectstatus'),
    url(r'^createbudget/$', views.create_budget, name='createbudget'),
    url(r'^projectbudget/$', views.ProjectBudgetView.as_view(), name='projectbudget'),
    url(r'^createtasks/$', views.create_tasks, name='createtask'),
    url(r'^progressreport/$', views.progress_report, name='progressreport'),
    url(r'^accomplishmentreport/$', views.accomplishment_report, name='accomplishmentreport'),
    url(r'^generatereports/$', views.generate_reports, name='generatereports'),
    url(r'^projectcompletion/$', views.project_completion, name='projectcompletion'),
    url(r'^uploadfinalreport/$', views.final_report, name='uploadfinalreport'),
    url(r'^viewcompleteprojects/$', views.complete_projects, name='viewcompleteprojects'),
    url(r'^projectstatus/$', views.project_status, name='projectstatus'),
    url(r'^reportsarchive/$', views.reports_archive, name='reportsarchive'),
url(r'^inventoryrequest/$', views.inventory_report, name='inventoryrequest'),
url(r'^inventoryrequestadmin/$', views.inventory_report_admin, name='inventoryrequestadmin'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
