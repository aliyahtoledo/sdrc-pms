from django import forms
from django.db import transaction
from django.forms import modelformset_factory, formset_factory
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import IncidentReport, Project, ProjectExpense, Milestone, BudgetExtension, ProjectMember, Task, Profile
from django.forms.utils import ErrorList

class ProjectAccountForm (forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "accountNumber",
            "projectTitle",
            "principalInvestigator",
            "fundingAgency",
            "projectCost",
            "startDate",
            "endDate",
            "files",
            "contractFile",
            "projectOverview",
            "tranche",
            "trancheAmount",
        ]

        widgets ={'accountNumber':forms.TextInput(attrs={
        'class':'form-control',

    }),'projectTitle':forms.TextInput(attrs={
        'class':'form-control',

    }),'principalInvestigator':forms.TextInput(attrs={
        'class':'form-control',

    }),'fundingAgency':forms.TextInput(attrs={
        'class':'form-control',
    }), 'startDate': forms.TextInput(attrs={
        'class': 'form-control has-feedback-left',
        'type':'date'
    }), 'endDate': forms.TextInput(attrs={
        'class': 'form-control has-feedback-left',
        'type':'date'
    }), 'projectCost': forms.TextInput(attrs={
        'class': 'form-control',
    }), 'tranche': forms.TextInput(attrs={
            'class': 'form-control',
    }), 'trancheAmount': forms.TextInput(attrs={
            'class': 'form-control',
    }),'projectOverview': forms.Textarea(attrs={
        'class': 'form-control',

    }),'contractFile': forms.FileInput(attrs={
        'data-role':"magic-overlay",
        'data-target':"#pictureBtn",
        'data-edit':"insertImage",
        })
        }


class TaskForm(forms.ModelForm):
    taskName = forms.CharField(widget=forms.TextInput(attrs={'id': 'taskName', 'name': 'taskName', 'class': 'form-control col-md-7 col-xs-12'}))
    assignedTo = forms.CharField(widget=forms.TextInput(attrs={'id': 'assignedTo', 'name': 'assignedTo', 'class': 'form-control col-md-7 col-xs-12'}))
    taskstartDate = forms.DateField(widget=forms.widgets.DateInput(attrs={'name': 'taskstartDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))
    taskendDate = forms.DateField(widget=forms.widgets.DateInput(attrs={'name': 'taskendDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))



    class Meta:
        model = Task
        fields = ['taskName', 'assignedTo', 'taskstartDate', 'taskendDate']
        

class BudgetExtensionForm(forms.Form):
    amountRequested = forms.DecimalField(widget=forms.widgets.DateInput(
        attrs={'type': 'text','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))
    reason = forms.CharField(widget=forms.TextInput(attrs={'id': 'newtaskName', 'name': 'newtaskName', 'class': 'form-control col-md-7 col-xs-12'}))

class UpdateTaskForm(forms.Form):
    newtaskName = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'newtaskName', 'name': 'newtaskName', 'class': 'form-control col-md-7 col-xs-12'}))
    newtaskstartDate = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'id': 'newtaskstartDate', 'name': 'newtaskstartDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))
    newtaskendDate = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'id': 'newtaskendDate', 'name': 'newtaskendDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))

UpdateTaskFormset = formset_factory(UpdateTaskForm, extra=1)

class GenerateReportForm(forms.Form):
    startDate = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'id': 'startDate', 'name': 'startDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))
    endDate = forms.DateField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'endDate', 'name': 'endDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))

class MilestoneForm(forms.ModelForm):
    milestoneName = forms.CharField(widget=forms.TextInput(attrs={'name': 'milestoneName', 'class': 'form-control col-md-7 col-xs-12'}))
    milestonestartDate = forms.DateField(widget=forms.widgets.DateInput(
        attrs={'id': 'milestonestartDate', 'name': 'milestonestartDate', 'type': 'date',
               'class': 'form-control col-md-7 col-xs-12'}))
    milestoneendDate = forms.DateField(widget=forms.widgets.DateInput(
        attrs={'id': 'milestoneendDate', 'name': 'milestoneendDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))
    trancheAmount = forms.CharField(widget=forms.TextInput(attrs={'name': 'trancheAmount', 'class': 'form-control col-md-7 col-xs-12', 'type': 'number'}))

    class Meta:
        model = Milestone
        fields = ['milestoneName', 'milestonestartDate', 'milestoneendDate', 'trancheAmount']

MilestoneFormset = formset_factory(MilestoneForm, extra=1)

class UpdateMilestoneForm(forms.Form):
    newmilestoneName = forms.CharField(required=False, widget=forms.TextInput(attrs={'name': 'newmilestoneName', 'type': 'text', 'class': 'form-control col-md-7 col-xs-12'}))
    newmilestonestartDate = forms.DateField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'newmilestonestartDate', 'name': 'newmilestonestartDate', 'type': 'date',
               'class': 'form-control col-md-7 col-xs-12'}))
    newmilestoneendDate = forms.DateField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'newmilestoneendDate', 'name':'newmilestoneendDate', 'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))


class BookForm(forms.Form):
    name = forms.CharField(
        label='Book Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Book Name here'
        })
    )
BookFormset = formset_factory(BookForm, extra=1)

class ProjectMemberForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    role = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))


    class Meta:
        model = ProjectMember
        fields = ['first_name', 'last_name', 'email', 'role']

ProjectMemberFormset = formset_factory(ProjectMemberForm, extra=1)

class TaskFinishedForm(forms.ModelForm):
    taskFinished = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))


    class Meta:
        model = Task
        fields = ['taskFinished']

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, label='First Name')
    last_name = forms.CharField(max_length=50, label='Last Name')
    email = forms.EmailField(max_length=254, label='Email Address')
    def clean_email(self):
        data = self.cleaned_data['email']
        if "@dlsu.edu.ph" not in data:  # any check you need
            raise forms.ValidationError("Must be a DLSU email address!")
        return data 

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('active_project',)

class ProjectForm(forms.ModelForm):
    projectTitle = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    fundingAgency = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control col-md-7 col-xs-12'}))
    projectDate = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date', 'class': 'form-control col-md-7 col-xs-12'}))

    class Meta:
        model = Project
        fields =[
        'projectTitle',
        'fundingAgency',
        'projectDate',
        ]

class ProjectAccountForm (forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "accountNumber",
            "projectTitle",
            "principalInvestigator",
            "fundingAgency",
            "startDate",
            "endDate",
            "projectCost",
            "projectOverview",
            "files",
            "contractFile",
        ]

        widgets ={'accountNumber':forms.TextInput(attrs={
        'class':'form-control',

    }),'projectTitle':forms.TextInput(attrs={
        'class':'form-control',

    }),'principalInvestigator':forms.TextInput(attrs={
        'class':'form-control',

    }),'fundingAgency':forms.TextInput(attrs={
        'class':'form-control',
    }), 'startDate': forms.TextInput(attrs={
        'class': 'form-control has-feedback-left',
        'type':'date'
    }), 'endDate': forms.TextInput(attrs={
        'class': 'form-control has-feedback-left',
        'type':'date'
    }), 'projectCost': forms.TextInput(attrs={
        'class': 'form-control',
    }),'projectOverview': forms.Textarea(attrs={
        'class': 'form-control',

    }),'contractFile': forms.FileInput(attrs={
        'data-role':"magic-overlay",
        'data-target':"#pictureBtn",
        'data-edit':"insertImage",
        })
        }

class IncidentForm(forms.ModelForm):
    issueEncountered = forms.CharField(label='Issue encountered', max_length=1000, widget=forms.TextInput(attrs={'class': 'form-control col-md-9 col-xs-12'}))
    issueDescription = forms.CharField(label='Description of the issue', max_length=5000, widget=forms.TextInput(attrs={'class': 'form-control col-md-9 col-xs-12'}))
    dateEncountered = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date', 'class': 'form-control col-md-9 col-xs-12'}))

    class Meta:
        model = IncidentReport
        fields = ['issueEncountered', 'issueDescription', 'dateEncountered']


class PersonnelForm(forms.Form):
    Expense_Title = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'id': 'personnelCategory', 'value':'Personnel', 'readonly':'readonly', 'name': 'personnelCategory', 'class': 'form-control col-md-7 col-xs-12'}))
    Personnel_Budget = forms.DecimalField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'personnelBudgetAllocated', 'name': 'personnelBudgetAllocated', 'type': 'text','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))

class TravelForm(forms.Form):
   Category= forms.CharField(required=False, widget=forms.TextInput(
        attrs={'id': 'travelCategory', 'value':'Travel', 'readonly':'readonly', 'name': 'travelCategory', 'class': 'form-control col-md-7 col-xs-12'}))
   Travel_Budget = forms.DecimalField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'travelBudgetAllocated', 'name': 'travelBudgetAllocated', 'type': 'text','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))


class FieldForm(forms.Form):
   Expense_Category= forms.CharField(required=False, widget=forms.TextInput(
        attrs={'id': 'fieldCategory', 'value':'Fieldwork', 'readonly':'readonly','name': 'fieldCategory', 'class': 'form-control col-md-7 col-xs-12'}))
   Fieldwork_Budget = forms.DecimalField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'fieldBudgetAllocated', 'name': 'fieldBudgetAllocated', 'type': 'text','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))


class OperatingForm (forms.Form):
   Category_Title= forms.CharField(required=False, widget=forms.TextInput(
        attrs={'id': 'operatingCategory', 'name': 'operatingCategory', 'value':'Operating', 'readonly':'readonly','class': 'form-control col-md-7 col-xs-12'}))
   Operating_Budget = forms.DecimalField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'operatingBudgetAllocated', 'name': 'operatingBudgetAllocated', 'type': 'text','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))

class OthersForm (forms.Form):
   Category_Name= forms.CharField(required=False, widget=forms.TextInput(
        attrs={'id': 'otherCategory', 'name': 'otherCategory', 'value':'Others', 'readonly':'readonly', 'class': 'form-control col-md-7 col-xs-12'}))
   Other_Budget = forms.DecimalField(required=False, widget=forms.widgets.DateInput(
        attrs={'id': 'otherBudgetAllocated', 'name': 'otherBudgetAllocated', 'type': 'text','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))


class ChangePasswordForm (forms.Form):
    password1 = forms.CharField(required=True, widget=forms.widgets.PasswordInput(
        attrs={'id': 'password1', 'name': 'password1', 'type': 'password','required':'required',
               'class': 'form-control col-md-7 col-xs-12'}))
    password2 = forms.CharField(required=True, widget=forms.widgets.PasswordInput(
        attrs={'id': 'password2', 'name': 'password2', 'type': 'password', 'required': 'required',
               'class': 'form-control col-md-7 col-xs-12'}))