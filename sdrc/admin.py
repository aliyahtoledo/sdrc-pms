from django.contrib import admin
from .models import Project, IncidentReport, Milestone, ProjectExpense, BudgetExtension, ProjectContract, ProjectMember, Task,BudgetCategory, Report, ProjectExtension, Profile, Reallocation, FirstVisit


admin.site.register(Project)
admin.site.register(IncidentReport)
admin.site.register(Milestone)
admin.site.register(ProjectExpense)
admin.site.register(BudgetExtension)
admin.site.register(ProjectContract)
admin.site.register(ProjectMember)
admin.site.register(Task)
admin.site.register(BudgetCategory)
admin.site.register(Report)
admin.site.register(ProjectExtension)
admin.site.register(Profile)
admin.site.register(Reallocation)
admin.site.register(FirstVisit)