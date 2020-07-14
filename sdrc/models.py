from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

import datetime


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    active_project = models.BooleanField(default=False)
    principal_investigator = models.BooleanField(default=False)

def __str__(self):
    return self.active_project

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Project(models.Model):
    TRANCHE_CHOICES = (
        ('First Tranche', 'First Tranche'),
        ('Second Tranche', 'Second Tranche'),
        ('Third Tranche', 'Third Tranche'),
        ('Final Tranche', 'Final Tranche')
    )
    accountNumber = models.IntegerField()
    principalInvestigator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    projectTitle = models.CharField(max_length=1000)
    fundingAgency = models.CharField(max_length=1000)
    progress = models.IntegerField(default=0, null=True)
    projectCost = models.DecimalField(max_digits=12,decimal_places=2)
    nowDate = models.DateField()
    startDate = models.DateField()
    endDate = models.DateField()
    files = models.FileField(null=True, blank=True)
    contractFile = models.FileField(upload_to='files', null=True, blank=True)
    finalReport = models.FileField(upload_to='files', null=True, blank=True)
    dateFinished = models.DateField(null=True, blank=True)
    projectOverview = models.TextField()
    status = models.CharField(max_length=100, default="In Progress")
    dateReceived = models.DateField(null=True)
    budgetSpent = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    budgetRemaining = models.DecimalField(max_digits=20, decimal_places=2, default=projectCost)
    hasTranche=models.BooleanField(default=False, null=True)
    trancheStatus = models.CharField(max_length=100, null=True, blank=True)
    tranche = models.CharField(max_length=100, choices=TRANCHE_CHOICES, null=True, blank=True)
    trancheAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0.00)
    totalExpense = models.DecimalField(max_digits=20, decimal_places=2,null=True,default=0)
    remarks = models.CharField(max_length=5000, null=True, blank=True)

    def __str__(self):
        return self.projectTitle

    def get_name(self):
        return self.principalInvestigator.first_name + " " + self.principalInvestigator.last_name

    def get_email(self):
        return self.principalInvestigator.email

    def get_daysLeft(self):
        end = self.endDate
        curr = datetime.date.today()
        return (end-curr).days


    def get_strDaysLeft(self):
        end = self.endDate
        curr = datetime.date.today()
        return str(end-curr).split(",")[0]

    def get_contract_file(self):
        return self.contractFile

    def members_as_list(self):
        return self.projectMember.split(',')

    def tranche_as_list(self):
        return self.tranche.split(',')

    def getBudgetSpent(self):
        expense = self.totalExpense
        total = self.trancheAmount
        return total - expense

    def getBudgetStatus(self):
        budget = self.trancheAmount
        remaining = self.budgetRemaining
        status = (remaining / budget ) * 100
        return status

    def getBudgetOverrun(self):
        expense = self.totalExpense
        budget = self.projectCost
        overrun = ((expense - budget)/budget) * 100
        return overrun

    def get_percentage_completed(self):
        if self.task_set.all():
            all_task = self.task_set.all().count()
            completed_task = Task.objects.filter(project=self.id, taskStatus='Completed').count()
            return (completed_task / all_task) * 100
        else:
            return 0

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    member = models.ForeignKey(User, default='1', on_delete=models.CASCADE)
    email = models.CharField(max_length=100)
    role = models.CharField(max_length=1000)

    def __str__(self):
        return self.role

class Milestone(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    milestoneName = models.CharField(max_length=1000, null=False)
    milestonestartDate = models.DateField(blank=True, null=True)
    milestoneendDate = models.DateField(blank=True, null=True)
    milestoneFinished = models.DateField(blank=True, null=True)
    milestoneStatus = models.CharField(max_length=30, default='Not Started')
    trancheAmount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    nowDate = models.DateField()

    def __str__(self):
        return self.milestoneName

    def get_daysLeft(self):
        end = self.milestoneendDate
        curr = datetime.date.today()
        return (end-curr).days

    def get_finished_task(self):
        if self.task_set.all():
            all_task = self.task_set.all().count()
            completed_task = Task.objects.filter(milestone=self.id, taskStatus='Completed').count()
            return (completed_task/all_task) * 100

    def in_progress_task(self):
        if self.task_set.all():
            return (Task.objects.filter(milestone=self.id, taskStatus='In Progress').count() / self.task_set.all().count()) * 100

    def not_started_task(self):
        if self.task_set.all():
            return (Task.objects.filter(milestone=self.id, taskStatus='Not Started').count() / self.task_set.all().count()) * 100

    def delayed_task(self):
        if self.task_set.all():
            return (Task.objects.filter(milestone=self.id, taskendDate__lt=datetime.date.today(), taskStatus='Not Started').count() + \
               Task.objects.filter(milestone=self.id, taskendDate__lt=datetime.date.today(), taskStatus='In Progress').count()
                / self.task_set.all().count()) * 100

class Task(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, default='1', on_delete=models.CASCADE)
    taskName = models.CharField(max_length=1000, null=True)
    assignedTo = models.CharField(max_length=30, null=False)
    taskstartDate = models.DateField(blank=True, null=True)
    taskendDate = models.DateField(blank=True, null=True)
    taskFinished = models.DateField(blank=True, null=True)
    taskStatus = models.CharField(max_length=30, default='Not Started')
    taskFile = models.FileField(null=True, upload_to='files')
    nowDate = models.DateField(null=True, blank=True)

    def get_daysLeft(self):
        end = self.taskendDate
        curr = datetime.date.today()
        return (end-curr).days

    def in_progress_task(self):
        return Task.objects.filter(taskStatus='In Progress').count() / Task.objects.all().count()

    def not_started_task(self):
        return Task.objects.filter(taskStatus='Not Started').count()

    def delayed_task(self):
        return Task.objects.filter(taskendDate__lt=datetime.date.today(), taskStatus='Not Started').count() + \
               Task.objects.filter(taskendDate__lt=datetime.date.today(), taskStatus='In Progress').count()




class IncidentReport(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, default='1', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, default='1', on_delete=models.CASCADE)
    category = models.CharField(max_length=1000)
    issueEncountered = models.CharField(max_length=1000)
    issueDescription = models.CharField(max_length=5000)
    issuePriority = models.CharField(max_length=20)
    dateEncountered = models.DateField()
    issueStatus = models.BooleanField(default=False)
    issueResolution = models.CharField(max_length=1000, default='N/A')
    nowDate = models.DateField()
    file = models.FileField(null=True, upload_to='files')
    resolvedBy = models.ForeignKey(User, default='1', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.issueEncountered



class ProjectContract(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    role = models.CharField(max_length=100)
    torNumber = models.IntegerField()
    objectives = models.TextField()
    approveDate = models.DateField(null=True)
    responsibleParty = models.CharField(max_length=200)
    status = models.CharField(max_length=100, default="For Review", blank=True)

    def __str__(self):
        return self.project.projectTitle

class ProjectExpense(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    expenseName = models.CharField(max_length=1000,null=True)
    expenseQuantity = models.CharField(max_length=10,null=True)
    expenseAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    expenseTotal = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    expenseDate = models.CharField(max_length=20,null=True)
    expenseReceipt = models.FileField(null=True)



class Book(models.Model):

    name = models.CharField(max_length=255)
    isbn_number = models.CharField(max_length=13)

    class Meta:
        db_table = 'book'

    def __str__(self):
        return self.name

class Report(models.Model):
    reportTitle = models.CharField(max_length=50)
    datefrom = models.DateField(null=True)
    dateto = models.DateField(null=True)
    nowDate = models.DateField()

    def __str__(self):
        return self.reportTitle

class BudgetCategory(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE,null=True)
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=50,null=True)
    quantity = models.IntegerField(null= True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    allocatedAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    subtotal = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    def __str__(self):
        return self.title


class ProjectExpense(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    category = models.ForeignKey(BudgetCategory, default='1', on_delete=models.CASCADE)
    expenseType = models.CharField(max_length=1000, null=True)
    itemType = models.CharField(max_length=1000, null=True)
    expenseName = models.CharField(max_length=1000,null=True)
    expenseLocation = models.CharField(max_length=1000,null=True)
    expenseQuantity = models.CharField(max_length=10,null=True)
    expenseDescription = models.CharField(max_length=5000, null=True)
    amountRequested = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    currency = models.CharField(max_length=10, null=True)
    expenseAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    expenseTotal = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    expenseDate = models.CharField(max_length=20,null=True)
    fromDate = models.CharField(max_length=20,null=True)
    toDate = models.CharField(max_length=20,null=True)
    expenseReceipt = models.FileField(null=True, upload_to='files')
    destination = models.CharField(null=True,max_length=50)
    mode = models.CharField(null=True, max_length=50)
    times = models.IntegerField(null=True)
    days = models.IntegerField(null=True)
    venue = models.CharField(null=True, max_length=50)
    status = models.CharField(null=True, max_length=50)
    remarks=models.CharField(max_length=1000,null=True)
    nowDate = models.DateField()


    def __str__(self):
        return self.expenseName

class Reallocation (models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    category_selected_for_reallocation =  models.CharField(max_length=100, null=True)
    category_requested =  models.CharField(max_length=100, null=True)
    dateRequested = models.DateField(default=timezone.now)
    dateApproved = models.DateField(null=True)
    status = models.CharField(max_length=20, default='For Review')
    remarks = models.CharField(max_length=1000, null=True)
    amountReallocated = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return self.category_requested



class BudgetExtension(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    dateRequested = models.DateField(default=timezone.now)
    amountRequested = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    approvedAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    reason = models.CharField(max_length=1000)
    status = models.CharField(max_length=20)
    remarks = models.CharField(max_length=1000)
    file = models.FileField(null=True, upload_to='files')
    nowDate = models.DateField()

class ProjectExtension(models.Model):
    project = models.ForeignKey(Project, default='1', on_delete=models.CASCADE)
    dateRequested = models.DateField(null=True)
    approvedDate = models.DateField(null=True)
    reason = models.CharField(max_length=1000, null=True)
    status = models.CharField(max_length=20,null=True)
    remarks = models.CharField(max_length=1000,null=True)
    nowDate = models.DateField(null=True)

class FirstVisit(models.Model):
    url = models.URLField()
    user = models.ForeignKey(User, default='1', on_delete=models.CASCADE)