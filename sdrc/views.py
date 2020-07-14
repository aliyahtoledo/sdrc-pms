import simplejson as simplejson
from django.views.generic import TemplateView
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views import generic
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, HttpResponse, render_to_response, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from email.message import Message
from django.template import RequestContext, loader
from django.views.generic import View, CreateView
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.forms.models import model_to_dict
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import date
import datetime
import json
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from sdrc.tokens import account_activation_token
from sdrc.models import Project, IncidentReport, Milestone, ProjectExpense, BudgetExtension, ProjectContract, \
	ProjectMember, Task, BudgetCategory, Report, ProjectExtension, Profile, Reallocation, FirstVisit
from sdrc.forms import GenerateReportForm, ProjectForm, IncidentForm, TaskFinishedForm, \
	SignUpForm, ProfileForm, MilestoneFormset, ProjectMemberForm, \
 \
	MilestoneForm, TaskForm, UpdateTaskForm, UpdateMilestoneForm, ProjectAccountForm, OthersForm, OperatingForm, \
	FieldForm, TravelForm, PersonnelForm, BudgetExtensionForm, ChangePasswordForm

currentdate = datetime.date.today()
milestone_count = Milestone.objects.all().filter(milestoneStatus=True).count()
project_count = Project.objects.all().filter(endDate__lte=currentdate).count()
notif_count = milestone_count + project_count


# for notif


def account_activation_sent(request):
	template_name = 'sdrc/account_activation_sent.html'

	return render(request, template_name)

def dashboard_locked(request):
	template_name = 'sdrc/lockeddashboard.html'
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
	if Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True, endDate__lte=datetime.date.today()):
		if request.method == 'POST':
			dateRequested = request.POST.get('dateRequested')
			reason = request.POST.get('reason')

			extension = ProjectExtension(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
										 dateRequested=dateRequested, reason=reason,
										 nowDate=datetime.date.today(), status='For Review')
			extension.save()
			return HttpResponseRedirect('/systemlocked/')

	extension = []
	approved = []
	currentdate = datetime.date.today()
	if project.projectextension_set.all:
		for p in ProjectExtension.objects.filter(project=project):
			if p.status == 'Approved' and p.approvedDate > currentdate:
				approved.append(p)
			else:
				extension.append(p)
	print(approved)
	print(extension)

	if approved:
		activeproject = []
		inactiveproject= []


		current_user = request.user
		if not Milestone.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)):
			model = Project.objects.filter(principalInvestigator=current_user.id, dateFinished__isnull=True)
			all_milestones = Milestone.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)).count()
			all_tasks = Task.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)).count()
			print(all_milestones)
			print(all_tasks)
			context = {'project': model, 'all_milestones': all_milestones, 'all_tasks': all_tasks,
					   'notifications': get_notifications(request), 'activeproject': activeproject, 'approved': approved}
			return render(request, 'sdrc/PI_dashboard.html', context)

		if Milestone.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)):
			milestone_final = Milestone.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True))
			all_milestones = Task.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)).count()
			finished_milestones = Task.objects.filter(taskStatus='Completed', project=Project.objects.get(
				principalInvestigator=current_user.id, dateFinished__isnull=True)).count()
			if finished_milestones:
				percentage_completed = (finished_milestones / all_milestones) * 100
				print(percentage_completed)
			else:
				percentage_completed = 0

			array = []
			array_1 = []
			notstarted_array = []
			inprogress_array = []
			completed_array = []

			for m in Milestone.objects.filter(
					project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
				project = Project.objects.get(principalInvestigator=request.user.id,
											  dateFinished__isnull=True).projectTitle
				milestone = Milestone.objects.get(id=m.id).milestoneName
				milestonestartDate = Milestone.objects.get(id=m.id).milestonestartDate
				milestoneendDate = Milestone.objects.get(id=m.id).milestoneendDate
				nowday = datetime.date.today()

				array1 = [milestone, (milestonestartDate - nowday).days, (milestoneendDate - nowday).days, project]
				array_1.append(array1)

			for m in Task.objects.filter(
					project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
				id = Task.objects.get(id=m.id).id
				milestone = Task.objects.get(id=m.id).milestone.milestoneName
				milestonestartDate = Task.objects.get(id=m.id).milestone.milestonestartDate
				milestoneendDate = Task.objects.get(id=m.id).milestone.milestoneendDate
				name = Task.objects.get(id=m.id).taskName
				resource = Task.objects.get(id=m.id).assignedTo
				nowday = datetime.date.today()
				startdate = Task.objects.get(id=m.id).taskstartDate
				enddate = Task.objects.get(id=m.id).taskendDate
				status = 0
				if "Not Started" in m.taskStatus:
					status = 0
					array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
					notstarted_array.append(array1)
				elif "In Progress" in m.taskStatus:
					status = 50
					array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
					inprogress_array.append(array1)
				elif "Completed" in m.taskStatus:
					status = 100
					array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
					completed_array.append(array1)

				print(completed_array)
				print(inprogress_array)
				print(notstarted_array)
				array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
				array.append(array1)

			in_progress_task = (Task.objects.filter(taskStatus='In Progress', project=Project.objects.get(
				principalInvestigator=current_user.id, dateFinished__isnull=True)).count())
			not_started_task = (Task.objects.filter(taskStatus='Not Started', project=Project.objects.get(
				principalInvestigator=current_user.id, dateFinished__isnull=True)).count())
			delayed_task = (Task.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True),
				taskStatus='In Progress',
				taskendDate__lt=datetime.date.today()).count() + Task.objects.filter(
				taskStatus='Not Started', taskendDate__lt=datetime.date.today()).count())
			array_task = [not_started_task, in_progress_task, finished_milestones, delayed_task]
			in_progress = Task.objects.filter(taskStatus='In Progress', project=Project.objects.get(
				principalInvestigator=current_user.id, dateFinished__isnull=True))
			not_started = Task.objects.filter(taskStatus='Not Started', project=Project.objects.get(
				principalInvestigator=current_user.id, dateFinished__isnull=True))
			delayed = Task.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True),
				taskStatus='In Progress',
				taskendDate__lt=datetime.date.today()), Task.objects.filter(
				taskStatus='Not Started', taskendDate__lt=datetime.date.today())

			finished = Task.objects.filter(taskStatus='Completed', project=Project.objects.get(
				principalInvestigator=current_user.id, dateFinished__isnull=True))
			datenow = datetime.date.today()
			model = Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)
			all_tasks = Task.objects.filter(
				project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True))

			print("delayed:")
			print(delayed)
			context = {'project': model, 'milestone': milestone_final, 'in_progress_task': in_progress_task,
					   'all_tasks': all_tasks, 'not_started_task': not_started_task, 'delayed_task': delayed_task,
					   'datenow': datenow, 'all_milestones': all_milestones, 'finished_milestones': finished_milestones,
					   'percentage_completed': percentage_completed, 'notifications': get_notifications(request),
					   'in_progress': in_progress, 'delayed': delayed, 'not_started': not_started, 'finished': finished,
					   'array_task': array_task, 'array': array, 'array_1': array_1, 'activeproject': activeproject,
					   'notstarted_array': notstarted_array, 'inprogress_array': inprogress_array,
					   'completed_array': completed_array, 'approved': approved}

			return render(request, 'sdrc/PI_dashboard.html', context)


	return render(request, template_name, context={'extension': extension,
												   'currentdate': currentdate})


def projectextension(request):
	template_name = 'sdrc/projectextension.html'

	extensions = ProjectExtension.objects.all()

	if request.method == 'POST':
		extensionID = request.POST.get('extensionID')
		projectID = request.POST.get('projectID')
		status = request.POST.get('status')
		remarks = request.POST.get('remarks')
		approvedDate = request.POST.get('approvedDate')

		if status == 'For Revisions' or status == 'Disapproved':
			extension = ProjectExtension.objects.get(id=extensionID)
			extension.status = status
			extension.remarks = remarks
			extension.save(update_fields=['status', 'remarks'])
			user = User.objects.get(id=extension.project.principalInvestigator.id)
			subject = '[SDRC] Project Extension Status'
			message = 'Your project extension status has been changed to: "' + status + '" with remarks: "' + remarks + '".'
			email_from = settings.EMAIL_HOST_USER
			recipient_list = [user.email]

			send_mail(subject, message, email_from, recipient_list)
		elif status == 'Approved':
			extension = ProjectExtension.objects.get(id=extensionID, project=projectID)
			extension.status = status
			extension.remarks = remarks
			extension.approvedDate = approvedDate
			extension.save(update_fields=['approvedDate', 'status', 'remarks'])
			user = User.objects.get(id=extension.project.principalInvestigator.id)
			subject = '[SDRC] Project Extension Status'
			message = 'Your project extension status has been changed to: "' + status + '" with approved date: "' + approvedDate + '". Make sure the project is finished before the approved date. If you exceed the approved date, the system will be locked again.'
			email_from = settings.EMAIL_HOST_USER
			recipient_list = [user.email]
			send_mail(subject, message, email_from, recipient_list)
	return render(request, template_name, context={'extensions': extensions, 'notifications': get_notifications(request)})

def create_project_account(request):
	if request.method == "POST":
		accountNumber = request.POST.get("accountNumber")
		projectTitle = request.POST.get("projectTitle")
		PI = request.POST.get("principalInvestigator")
		principalInvestigator = User.objects.get(id=PI)
		fundingAgency = request.POST.get("fundingAgency")
		startDate = request.POST.get("startDate")
		endDate = request.POST.get("endDate")
		cost = request.POST.get("projectCost")
		projectCost = float(cost.replace(',', ''))
		projectOverview = request.POST.get("projectOverview")
		files = request.FILES.get("files")
		budget = request.POST.get('trancheAmount')
		trancheAmount = float(budget.replace(',', ''))
		dateReceived = request.POST.get('dateReceived')
		hasTranche = request.POST.get('hasTranche')

		if hasTranche == "Yes":
			hasTranche = True

		else:
			hasTranche = False
		project = Project(
			accountNumber=accountNumber,
			projectTitle=projectTitle,
			projectOverview=projectOverview,
			principalInvestigator=principalInvestigator,
			fundingAgency=fundingAgency,
			startDate=startDate,
			endDate=endDate,
			nowDate=datetime.date.today(),
			projectCost=projectCost,
			contractFile=files,
			budgetRemaining=projectCost,
			trancheAmount=trancheAmount, dateReceived=dateReceived,
			hasTranche=hasTranche,
		)
		project.save()

		user = User.objects.get(id=PI)
		profile = Profile.objects.get(user=user)
		profile.active_project = True
		profile.principal_investigator = True
		profile.save()
		subject = '[SDRC] Project Assignment'
		message = 'You have been assigned the project entitled: ' + projectTitle + '.' + 'Please contact SDRC Admin to get your account details if you are new to the system. Otherwise, log in to the system. Thank you!'
		email_from = settings.EMAIL_HOST_USER
		recipient_list = [user.email]

		send_mail(subject, message, email_from, recipient_list)
		return redirect('/view-budget-plan/')

	users = User.objects.filter(is_staff=False).exclude(profile__active_project=True)
	projects = Project.objects.all()

	context = {'user': users, 'projects': projects, 'notifications': get_notifications(request)}
	return render(request, 'sdrc/create_project_account.html', context)

def expense_report(request):

	user = request.user.id
	currentdate = datetime.date.today()
	project = Project.objects.get(principalInvestigator=user, dateFinished__isnull=True)
	category = BudgetCategory.objects.filter(project=project)
	expensesum = ProjectExpense.objects.filter(project=project, status='Approved').exclude(expenseReceipt__isnull=False).values('category').annotate(sum=Sum('subtotal'))
	expense = ProjectExpense.objects.filter(project=project, status='Approved').exclude(expenseReceipt__isnull=False)
	print(expense)



	context = {'currentdate': currentdate, 'category': category, 'expensesum': expensesum, 'expense': expense, 'project': project}
	return render(request, 'sdrc/financial_report.html', context)

def final_report(request):
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
	print(project)


	incidents = IncidentReport.objects.filter(project=project, issueStatus=False)
	tasks = Task.objects.filter(project=project, taskStatus='Not Started' or 'In Progress')
	print(tasks)



	if request.method == "POST":
		report = request.FILES.get('finalReport')
		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
		profile = Profile.objects.get(user=request.user.id)
		date = datetime.date.today()
		project.finalReport = report
		project.save()



		if project.finalReport:
			project.finalReport = report
			project.status = 'For Review'
			project.save(update_fields=['finalReport', 'status'])
		   # profile.active_project = False
			#profile.save(update_fields=['active_project'])


	return render(request, 'sdrc/create_final_report.html', {'notifications': get_notifications(request), 'project': project, 'incidents': incidents, 'tasks': tasks})


def complete_projects(request):
	projects = Project.objects.all()
	project = []

	for p in projects:
		if p.dateFinished:
			project.append(p)

	print(projects)

	context = {'project': project}

	return render(request, 'sdrc/viewcompleteprojects.html', context)


def create_term_of_reference_DLSU(request):
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
	user = User.objects.get(id=request.user.id)
	if request.method == "POST":
		torNumber = request.POST.get("torNumber")
		name = request.POST.get("name")
		role = request.POST.get("role")
		budget = request.POST.get("amount")
		objectives = request.POST.get("objectives")
		responsibleParty = request.POST.get("responsibleParty")

		ProjectContract.objects.create(
			project=project,
			torNumber=torNumber,
			name=name,
			budget=budget,
			role=role,
			objectives=objectives,
			responsibleParty=responsibleParty,
		)

	return render(request, 'sdrc/create_tor_DLSU.html', context={'project': project, 'user': user})


def create_budget_details(request):
	all_projects = Project.objects.all()

	if request.method == "POST":
		project = request.POST.get("project")
		projectBudget = Project.objects.get(id=project)
		tranche = request.POST.get("tranche")
		amount = request.POST.get("amount")
		trancheDate = request.POST.get("dateOfRelease")
		# budget = Budget(project=projectBudget,dateReceived=trancheDate,tranche=tranche,trancheAmount=amount)
		# budget.save()

	return render(request, 'sdrc/create_budget_details.html', {'all_projects': all_projects})


def update_project_account(request, id=None):
	instance = get_object_or_404(Project, id=id)
	form = ProjectAccountForm(request.POST or None, instance=instance)
	if form.is_valid():
		instance = form.save(commit=False)
		print(form.cleaned_data.get("title"))
		print(form.cleaned_data.get("accountNumber"))
		instance.save()
		return HttpResponseRedirect("/view-projects/")
	user = User.objects.filter(profile__active_project=False, profile__principal_investigator=False).exclude(is_staff=True)
	context = {
		'user': user,
		'instance': instance,
		'form': form,
	}
	return render(request, 'sdrc/update_project_account.html', context)

def updateBudgetPlan(request, id=None):

	if request.user.is_staff:

		project = Project.objects.get(id=id, dateFinished__isnull=True)
		category = BudgetCategory.objects.filter(project=project)
		if request.method == 'POST':
			for c in category:
				cid= c.id.__str__()
				categoryID = request.POST.get('category_id'+cid)
				title = request.POST.get('title' + cid)
				quantity = request.POST.get('pax' + cid)
				amount = request.POST.get('amount' + cid)
				subtotal = request.POST.get('subtotal' + cid)
				if cid == categoryID:
					budgetcategory = BudgetCategory.objects.get(id=c.id)
					budgetcategory.title = title
					budgetcategory.quantity = quantity
					budgetcategory.amount = amount
					budgetcategory.subtotal = subtotal
					budgetcategory.save(update_fields=['title','quantity','amount','subtotal'])
			messages.success(request,'Succesfully Updated!')
			return redirect('/create-budget-plan/')


		context={
			'projects':project,
			'category':category
		}
		return render(request, 'sdrc/update_budgetplan.html',context)

def projectbudget_overview(request):
	project = Project.objects.filter(dateFinished__isnull=True)
	nowDate = datetime.date.today()
	return render(request, 'sdrc/projectbudgetoverview.html', context={'project': project, 'nowDate': nowDate})

def reports_archive(request):
	reports = Report.objects.all()

	if request.method == "POST":
		projectTitle = request.POST.get('projectTitle')
		if projectTitle == "Project Completion Report":
			startDate = request.POST.get('startDate')
			endDate = request.POST.get('endDate')
			request.session['startDate'] = startDate
			request.session['endDate'] = endDate
			return redirect('/projectcompletion/')
		elif projectTitle == "Project Status Report":
			nowDate = request.POST.get('nowDate')
			request.session['nowDate'] = nowDate
			return redirect('/projectstatus/')
		elif projectTitle == "Incident Report Summary":
			startDate = request.POST.get('startDate')
			endDate = request.POST.get('endDate')
			request.session['startDate'] = startDate
			request.session['endDate'] = endDate
			return redirect('/incidentreport_summary/')


	context = {'reports': reports, 'notifications': get_notifications(request)}
	return render(request, 'sdrc/reportsarchive.html', context)

def generate_reports(request):
	form = GenerateReportForm()
	template = loader.get_template("sdrc/generatereports.html")
	currentdate = datetime.date.today()
	startDate = ()
	endDate = ()

	if request.method == 'POST':
		reportTitle = request.POST.get('reportTitle')
		if reportTitle == "Project Completion Report" or reportTitle == 'Incident Report Summary' or reportTitle == 'Project Budget Overview':
			form = GenerateReportForm(request.POST)
			if form.is_valid():

				startDate = request.POST.get('startDate')
				endDate = request.POST.get('endDate')
				request.session['startDate'] = startDate
				request.session['endDate'] = endDate
				report = Report(reportTitle=reportTitle, datefrom=startDate, dateto=endDate, nowDate=datetime.date.today())
				report.save()
				if reportTitle == 'Project Completion Report':
					return redirect('/projectcompletion/')
				elif reportTitle == 'Incident Report Summary':
					return redirect('/incidentreport_summary/')
				elif reportTitle == 'Project Budget Overview':
					return redirect('/projectbudget_overview/')

		elif reportTitle == "Project Status Report":
			nowDate = request.POST.get('nowDate')
			request.session['nowDate'] = nowDate
			report = Report(reportTitle=reportTitle, nowDate=nowDate)
			report.save()
			return redirect('/projectstatus/')


	context = {'form': form, 'startDate': startDate, 'endDate': endDate, 'currentdate': currentdate, 'notifications': get_notifications(request)}
	return HttpResponse(template.render(context, request))


def project_completion(request):
	startDate = request.session['startDate']
	endDate = request.session['endDate']
	pstartDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
	pendDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()

	project = Project.objects.filter(dateFinished__lte=pendDate)
	print(project)

	context = {'project': project, 'startDate': startDate, 'endDate': endDate}
	return render(request, 'sdrc/projectcompletion.html', context)

def resolved_issues(request):
	all_incident_report = IncidentReport.objects.filter(issueStatus=True)

	return render(request, 'sdrc/resolvedissues.html', {'all_incident_report': all_incident_report})

def project_status(request):
	nowDate = request.session['nowDate']
	pendDate = datetime.datetime.strptime(nowDate, "%Y-%m-%d").date()
	project = Project.objects.filter(Q(endDate__gte=pendDate) | Q(dateFinished__isnull=True))

	context = {'project': project, 'currentdate': nowDate}

	return render(request, 'sdrc/projectstatus.html', context)


def view_projects(request):
	percentage_completed = []
	all_projects = Project.objects.all().order_by('nowDate')
	for project in all_projects:
		all_milestones = project.task_set.all()
		finished_milestones = project.task_set.filter(taskStatus=True)
		if not all_milestones:
			percentage_completed.append(0)
		if all_milestones:
			percentage = (finished_milestones.count() / all_milestones.count() * 100)
			percentage_completed.append(percentage)


	if request.method == "POST":
		projectUpdate = request.POST.get('projectUpdate')
		projectID = request.POST.get('projectID')
		if projectUpdate == 'Delete':
			member = Project.objects.get(id=projectID).delete()
			return HttpResponseRedirect('/view-projects/')

		ID = request.POST.get('projectID')
		project = Project.objects.get(id=ID)
		projectSubject = request.POST.get('projectSubject')
		projectMessage = request.POST.get('projectMessage')

		subject = projectSubject
		message = projectMessage
		email_from = settings.EMAIL_HOST_USER
		recipient_list = [project.get_email()]

		send_mail(subject, message, email_from, recipient_list)



	currentdate = datetime.date.today()
	user = User.objects.all()
	zipped_data = zip(all_projects, percentage_completed)
	latest_upload = Task.objects.all().order_by('-nowDate')[0]
	return render(request, 'sdrc/view_projects.html',
				  {'user': user, 'latest_upload': latest_upload, 'currentdate': currentdate, 'all_projects': all_projects, 'zipped_data': zipped_data, 'notifications': get_notifications(request)})




# VIEW CODELINES
def view_budget_status(request):
	expense = list()
	budget = list()
	project = Project.objects.all()

	# for pBudget in project:
	#     expenseparticular = Project.objects.get(id=pBudget.id).projectexpense_set.all()
	#
	# if expenseparticular: #if may laman
	#     expense.append(expenseparticular)
	# else:
	#     budget.append(pBudget)
	#
	# print(expense)
	# print(budget)
	# zipped_item = expense
	# context = {'object':  zipped_item, 'all_budget':budget,}

	return render(request, 'sdrc/view_budget_status.html', {'projects':project, 'notifications': get_notifications(request)})


class AdminIndexView(TemplateView):
	template_name = 'sdrc/dashboard.html'
	context_object_name = 'admindashboard'


def budget_extension_form(request):
	template_name = 'sdrc/budgetextensionform.html'

	if not request.user.is_staff:
		if request.user.profile.principal_investigator and request.user.profile.active_project:
			category = request.session['category']
			amount = request.session['amount']
			expense = request.session['expense']
			description = request.session['description']

			expensecategory = request.POST.get('category')
			expenseamount = request.POST.get('amount')
			reason = request.POST.get('reason')
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
			budgetcategory = BudgetCategory.objects.filter(project=project)

			for b in budgetcategory:
				if b.title == expensecategory:
					budgetrequest = BudgetExtension(project=project, category=b,
													amountRequested=expenseamount,
													reason=reason, nowDate=datetime.date.today())
					budgetrequest.save()
		elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					category = request.session['category']
					amount = request.session['amount']
					expense = request.session['expense']
					description = request.session['description']

					expensecategory = request.POST.get('category')
					expenseamount = request.POST.get('amount')
					reason = request.POST.get('reason')
					project = p
					budgetcategory = BudgetCategory.objects.filter(project=project)

					for b in budgetcategory:
						if b.title == expensecategory:
							budgetrequest = BudgetExtension(project=project, category=b,
															amountRequested=expenseamount,
															reason=reason, nowDate=datetime.date.today())
							budgetrequest.save()

	context = {'category': category,
			   'amount': amount,
			   'expense': expense,
			   'description': description,
			   'notifications': get_notifications(request)}
	return render(request, template_name, context)

def view_past_projects(request):
	template_name = 'sdrc/view_past_projects.html'

	projects = Project.objects.filter(principalInvestigator=request.user.id, dateFinished__isnull=False)
	reportform = request.POST.get('reportform')

	if reportform == 'Accomplishment':
		projectID = request.POST.get('projectID')
		project = Project.objects.get(id=projectID)
		return render(request, 'sdrc/accomplishmentreport.html', context={'project': project, 'currentdate': datetime.date.today()})
	elif reportform == 'Financial':
		projectID = request.POST.get('projectID')
		project = Project.objects.get(id=projectID)
		category = BudgetCategory.objects.filter(project=project)
		expensesum = ProjectExpense.objects.filter(project=project, status='Approved').exclude(
			expenseReceipt__isnull=True).values('category').annotate(sum=Sum('expenseTotal'))
		expense = ProjectExpense.objects.filter(project=project, status='Approved').exclude(
			expenseReceipt__isnull=True)
		return render(request, 'sdrc/budgetreport.html', context={'project': project, 'currentdate': datetime.date.today(), 'category': category, 'expensesum': expensesum, 'expense': expense})
	return render(request, template_name, context={'projects': projects})

def request_final(request):
	template_name = 'sdrc/request_final.html'

	projects = Project.objects.filter(dateFinished__isnull=True).exclude(finalReport="")
	print(projects)
	projectID = request.POST.get('projectID')
	status = request.POST.get('status')
	remarks = request.POST.get('remarks')
	if projectID:
		if status == 'For Revisions':
			project = Project.objects.get(id=projectID)
			project.status = status
			project.remarks = remarks
			project.save(update_fields=['status', 'remarks'])
			subject = '[SDRC] Final Project Status'
			message = 'The status of your final project has been changed to: "' + status + '" with the remarks: "' + remarks + '".'
			email_from = settings.EMAIL_HOST_USER
			recipient_list = [project.principalInvestigator.email]

			send_mail(subject, message, email_from, recipient_list)

		elif status == 'Completed':
			project = Project.objects.get(id=projectID)
			project.status = status
			project.remarks = remarks
			project.dateFinished = datetime.date.today()
			project.save(update_fields=['status', 'remarks', 'dateFinished'])
			profile = Profile.objects.get(user=project.principalInvestigator.id)
			profile.active_project = False
			profile.principal_investigator=False
			profile.save(update_fields=['active_project', 'principal_investigator'])

			users = User.objects.all()
			members = ProjectMember.objects.filter(project=project)
			for m in members:
				for u in users:
					if m.member.id == u.id:
						prof = Profile.objects.get(user=u)
						prof.active_project=False
						prof.save(update_fields=['active_project'])

			subject = '[SDRC] Final Project Status'
			message = 'The status of your final project has been changed to: "' + status + '" with the remarks: "' + remarks + '".'
			email_from = settings.EMAIL_HOST_USER
			recipient_list = [project.principalInvestigator.email]

			send_mail(subject, message, email_from, recipient_list)


	return render(request, template_name, context={'projects': projects, 'notifications': get_notifications(request)})

def PIIndexView(request):
	template_name = 'sdrc/PI_dashboard.html'
	context_object_name = 'pidashboard'

	if request.user.is_staff:
		deadline = Project.objects.filter(endDate__lte=datetime.date.today())
		all_projects = Project.objects.all()
		allprojects = []
		percentage_completed = []
		for p in all_projects:
			if not p.dateFinished:
				allprojects.append(p)


				all_milestones = p.task_set.all()
				finished_milestones = p.task_set.filter(taskStatus='Completed')
				if all_milestones:
					percentage = (finished_milestones.count() / all_milestones.count() * 100)
					percentage_completed.append(percentage)
				if not p.task_set.all():
					percentage = 0
					percentage_completed.append(percentage)
		print(allprojects)

		all_budget = []
		projects = Project.objects.filter(dateFinished__isnull=True)
		for p in projects:
			if p.budgetRemaining <= 0:
				if not p.dateFinished:
					all_budget.append(p)

		print("budget:")
		print(all_budget)

		if request.method == 'POST':
			ID = request.POST.get('projectID')
			project = Project.objects.get(id=ID)
			projectSubject = request.POST.get('projectSubject')
			projectMessage = request.POST.get('projectMessage')

			subject = projectSubject
			message = projectMessage
			email_from = settings.EMAIL_HOST_USER
			recipient_list = [project.get_email()]

			send_mail(subject, message, email_from, recipient_list)

		array = [['Project', 'Budget', 'Expense']]

		for p in projects:
			projectTitle = p.projectTitle
			projectCost = p.projectCost
			projectExpense = p.totalExpense

			cost = simplejson.dumps(Decimal(projectCost))
			expense = simplejson.dumps(Decimal(projectExpense))
			array1 = [projectTitle, cost, expense]
			array.append(array1)
			print(array1)

		print(array)
		currentdate = datetime.date.today()
		zipped_data = zip(all_projects, percentage_completed)
		context = {'allprojects': allprojects, 'array': json.dumps(array), 'all_budget': all_budget, 'currentdate': currentdate, 'projects': projects, 'deadline': deadline, 'zipped_data': zipped_data,
				   'notifications': get_notifications(request)}
		return render(request, 'sdrc/dashboard.html', context)


	if request.method == 'POST':
		milestone = Milestone.objects.get(pk=request.POST.get('milestone'))
		milestone.milestoneStatus = True
		milestone.save()

	current_user = request.user

	display_project = []
	for m in ProjectMember.objects.all():
		for u in User.objects.all():
			if u == request.user:
				if m.member == u:
					print("ayus")
					if u.profile.active_project and not u.profile.principal_investigator:
						print("ewan")
						for p in Project.objects.all():
							if p == m.project and not p.dateFinished:
								print("ganun")
								display_project.append(p)

	if display_project:
		for dp in display_project:


			if not Milestone.objects.filter(project=dp):
				model = Project.objects.filter(principalInvestigator=current_user.id, dateFinished__isnull=True)
				all_milestones = Milestone.objects.filter(
						project=dp).count()
				all_tasks = Task.objects.filter(project=dp).count()
				print(all_milestones)
				print(all_tasks)
				context = {'project': model, 'all_milestones': all_milestones, 'all_tasks': all_tasks,
							   }
				return render(request, 'sdrc/member_dashboard.html', context)

			if Milestone.objects.filter(project=dp):
				upcoming = []
				days_left = []
				name = request.user.first_name + ' ' + request.user.last_name
				for task in Task.objects.filter(project=dp, assignedTo=name).order_by('taskendDate').exclude(taskStatus='Completed'):
					if task.get_daysLeft() <= 30:
						upcoming.append(task)
						days_left.append(task.get_daysLeft())
				print("days left:")
				print(days_left)

				milestone_final = Milestone.objects.filter(project=dp)
				all_milestones = Task.objects.filter(project=dp).count()
				finished_milestones = Task.objects.filter(taskStatus='Completed', project=dp).count()
				if finished_milestones:
					percentage_completed = (finished_milestones / all_milestones) * 100
					print(percentage_completed)
				else:
					percentage_completed = 0

				array = []
				array_1 = []
				notstarted_array = []
				inprogress_array = []
				completed_array = []

				for m in Milestone.objects.filter(project=dp):
					project = dp.projectTitle
					milestone = Milestone.objects.get(id=m.id).milestoneName
					milestonestartDate = Milestone.objects.get(id=m.id).milestonestartDate
					milestoneendDate = Milestone.objects.get(id=m.id).milestoneendDate
					nowday = datetime.date.today()


					array1 = [milestone, (milestonestartDate - nowday).days, (milestoneendDate - nowday).days, project]
					array_1.append(array1)

				full_name = request.user.first_name + " " + request.user.last_name
				for m in Task.objects.filter(project=dp, assignedTo=full_name):
					id = Task.objects.get(id=m.id).id
					milestone = Task.objects.get(id=m.id).milestone.milestoneName
					milestonestartDate = Task.objects.get(id=m.id).milestone.milestonestartDate
					milestoneendDate = Task.objects.get(id=m.id).milestone.milestoneendDate
					name = Task.objects.get(id=m.id).taskName
					resource = Task.objects.get(id=m.id).assignedTo
					nowday = datetime.date.today()
					startdate = Task.objects.get(id=m.id).taskstartDate
					enddate = Task.objects.get(id=m.id).taskendDate
					status = 0
					if "Not Started" in m.taskStatus:
						status = 0
						array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
						notstarted_array.append(array1)
					elif "In Progress" in m.taskStatus:
						status = 50
						array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
						inprogress_array.append(array1)
					elif "Completed" in m.taskStatus:
						status = 100
						array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
						completed_array.append(array1)

					print(completed_array)
					print(inprogress_array)
					print(notstarted_array)
					array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
					array.append(array1)

				in_progress_task = (Task.objects.filter(taskStatus='In Progress', project=dp).count())
				not_started_task = (Task.objects.filter(taskStatus='Not Started', project=dp).count())
				delayed_task = (Task.objects.filter(project=dp,
														taskStatus='In Progress',
														taskendDate__lt=datetime.date.today()).count() + Task.objects.filter(
						taskStatus='Not Started', taskendDate__lt=datetime.date.today()).count())
				array_task = [not_started_task, in_progress_task, finished_milestones, delayed_task]
				in_progress = Task.objects.filter(taskStatus='In Progress', project=dp)
				not_started = Task.objects.filter(taskStatus='Not Started', project=dp)
				delayed = Task.objects.filter(
					Q(project=dp,
					  taskStatus='In Progress',
					  taskendDate__lt=datetime.date.today()) | Q(
						taskStatus='Not Started', taskendDate__lt=datetime.date.today()))
				finished = Task.objects.filter(taskStatus='Completed', project=dp)
				datenow = datetime.date.today()
				model = dp
				all_tasks = Task.objects.filter(project=dp)
				print("delayed:")
				print(delayed)
				total = ProjectExpense.objects.filter(project=dp).values('category',
																			  'status').annotate(
					sum=Sum('expenseTotal')).order_by('category', 'status')
				categories = BudgetCategory.objects.filter(project=dp)
				if upcoming and days_left:
					context = {'project': model, 'upcoming_task': upcoming[0], 'days_left': days_left[0], 'milestone': milestone_final, 'in_progress_task': in_progress_task,
							   'all_tasks': all_tasks, 'not_started_task': not_started_task, 'delayed_task': delayed_task,
							   'datenow': datenow, 'all_milestones': all_milestones, 'finished_milestones': finished_milestones,
							   'percentage_completed': percentage_completed,
							   'in_progress': in_progress, 'delayed': delayed, 'not_started': not_started, 'finished': finished,
							   'array_task': array_task, 'array': array, 'array_1': array_1,
						   'notstarted_array': notstarted_array, 'inprogress_array': inprogress_array, 'completed_array': completed_array,
							   'total': total, 'categories': categories}

					return render(request, 'sdrc/member_dashboard.html', context)
				else:
					context = {'project': model,
							   'milestone': milestone_final, 'in_progress_task': in_progress_task,
							   'all_tasks': all_tasks, 'not_started_task': not_started_task,
							   'delayed_task': delayed_task,
							   'datenow': datenow, 'all_milestones': all_milestones,
							   'finished_milestones': finished_milestones,
							   'percentage_completed': percentage_completed,
							   'in_progress': in_progress, 'delayed': delayed, 'not_started': not_started,
							   'finished': finished,
							   'array_task': array_task, 'array': array, 'array_1': array_1,
							   'notstarted_array': notstarted_array, 'inprogress_array': inprogress_array,
							   'completed_array': completed_array, 'total': total, 'categories': categories}

					return render(request, 'sdrc/member_dashboard.html', context)
	else:
		# budget = Budget.objects.get(project=Project.objects.get(principalInvestigator=current_user.id).id)
		# print(budget)
		activeproject = []
		inactiveproject = []
		model = Project.objects.filter(principalInvestigator=current_user.id)

		if model:
			for m in model:
				if not m.dateFinished:
					activeproject.append(m)
				elif m.dateFinished:
					inactiveproject.append(m)
		print(activeproject)
		print(inactiveproject)

		if activeproject:

			if Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True):
				milestone_final = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True))
				all_milestones = Task.objects.filter(project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)).count()
				finished_milestones = Task.objects.filter(taskStatus='Completed', project=Project.objects.get(
					principalInvestigator=current_user.id, dateFinished__isnull=True)).count()
				if finished_milestones:
					percentage_completed = (finished_milestones / all_milestones) * 100
					print(percentage_completed)
				else:
					percentage_completed = 0
				project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
				upcoming = []
				days_left = []
				for task in Task.objects.filter(project=project).order_by('taskendDate').exclude(
						taskStatus='Completed'):
					if task.get_daysLeft() <= 30:
						upcoming.append(task.taskName)
						days_left.append(task.get_daysLeft())

				print("upcoming: eme eme ")
				print(upcoming)
				print("days_left: ")
				print(days_left)

				array = []
				array_1 = []
				notstarted_array = []
				inprogress_array = []
				completed_array = []
				project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
				total = ProjectExpense.objects.filter(project=project).values('category',
																			  'status').annotate(
					sum=Sum('expenseTotal')).order_by('category', 'status')
				print("total")
				print(total)
				for m in Milestone.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True).projectTitle
					milestone = Milestone.objects.get(id=m.id).milestoneName
					milestonestartDate = Milestone.objects.get(id=m.id).milestonestartDate
					milestoneendDate = Milestone.objects.get(id=m.id).milestoneendDate
					nowday = datetime.date.today()


					array1 = [milestone, (milestonestartDate - nowday).days, (milestoneendDate - nowday).days, project]
					array_1.append(array1)

				for m in Task.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
					id = Task.objects.get(id=m.id).id
					milestone = Task.objects.get(id=m.id).milestone.milestoneName
					milestonestartDate = Task.objects.get(id=m.id).milestone.milestonestartDate
					milestoneendDate = Task.objects.get(id=m.id).milestone.milestoneendDate
					name = Task.objects.get(id=m.id).taskName
					resource = Task.objects.get(id=m.id).assignedTo
					nowday = datetime.date.today()
					startdate = Task.objects.get(id=m.id).taskstartDate
					enddate = Task.objects.get(id=m.id).taskendDate
					status = 0
					if "Not Started" in m.taskStatus:
						status = 0
						array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
						notstarted_array.append(array1)
					elif "In Progress" in m.taskStatus:
						status = 50
						array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
						inprogress_array.append(array1)
					elif "Completed" in m.taskStatus:
						status = 100
						array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
						completed_array.append(array1)

					print(completed_array)
					print(inprogress_array)
					print(notstarted_array)
					array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
					array.append(array1)

				in_progress_task = (Task.objects.filter(taskStatus='In Progress', project=Project.objects.get(
						principalInvestigator=current_user.id, dateFinished__isnull=True)).count())
				not_started_task = (Task.objects.filter(taskStatus='Not Started', project=Project.objects.get(
						principalInvestigator=current_user.id, dateFinished__isnull=True)).count())
				delayed_task = (Task.objects.filter(project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True),
														taskStatus='In Progress',
														taskendDate__lt=datetime.date.today()).count() + Task.objects.filter(
						taskStatus='Not Started', taskendDate__lt=datetime.date.today()).count())
				array_task = [not_started_task, in_progress_task, finished_milestones, delayed_task]
				in_progress = Task.objects.filter(taskStatus='In Progress', project=Project.objects.get(
						principalInvestigator=current_user.id, dateFinished__isnull=True))
				not_started = Task.objects.filter(taskStatus='Not Started', project=Project.objects.get(
						principalInvestigator=current_user.id, dateFinished__isnull=True))
				delayed = Task.objects.filter(Q(project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True),
												  taskStatus='In Progress',
												  taskendDate__lt=datetime.date.today()) | Q(
						taskStatus='Not Started', taskendDate__lt=datetime.date.today()))
				finished = Task.objects.filter(taskStatus='Completed', project=Project.objects.get(
						principalInvestigator=current_user.id, dateFinished__isnull=True))
				datenow = datetime.date.today()
				model = Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)
				all_tasks = Task.objects.filter(project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True))
				print("delayed:")
				print(delayed)

				categories = BudgetCategory.objects.filter(project=model)

				if upcoming and days_left:
					context = {'project': model, 'milestone': milestone_final, 'in_progress_task': in_progress_task,
							   'all_tasks': all_tasks, 'not_started_task': not_started_task, 'delayed_task': delayed_task,
							   'datenow': datenow, 'all_milestones': all_milestones, 'finished_milestones': finished_milestones,
							   'percentage_completed': percentage_completed, 'notifications': get_notifications(request),
							   'in_progress': in_progress, 'delayed': delayed, 'not_started': not_started, 'finished': finished, 'categories': categories,
							   'array_task': array_task, 'total': total, 'array': array, 'array_1': array_1, 'activeproject': activeproject,
						   'notstarted_array': notstarted_array, 'inprogress_array': inprogress_array, 'completed_array': completed_array,
						   'upcoming_task': upcoming[0], 'days_left': days_left[0]}
				else:
					context = {'project': model, 'milestone': milestone_final, 'in_progress_task': in_progress_task,
							   'all_tasks': all_tasks, 'not_started_task': not_started_task,
							   'delayed_task': delayed_task,
							   'datenow': datenow, 'all_milestones': all_milestones,
							   'finished_milestones': finished_milestones,
							   'percentage_completed': percentage_completed,
							   'notifications': get_notifications(request),
							   'in_progress': in_progress, 'delayed': delayed, 'not_started': not_started,
							   'finished': finished, 'categories': categories,
							   'array_task': array_task, 'total': total, 'array': array, 'array_1': array_1,
							   'activeproject': activeproject,
							   'notstarted_array': notstarted_array, 'inprogress_array': inprogress_array,
							   'completed_array': completed_array}
				return render(request, template_name, context)
		elif inactiveproject:
			return render(request, template_name, context={'inactiveproject': inactiveproject})

		if not request.user.profile.active_project:
			return render(request, template_name, context={'inactiveproject': inactiveproject})


def expense_report(request):
	user = request.user.id
	project = Project.objects.get(principalInvestigator=user, dateFinished__isnull=True)
	category = BudgetCategory.objects.filter(project=project)
	expensesum = ProjectExpense.objects.filter(project=project, status='Approved').exclude(expenseReceipt__isnull=True).values('category').annotate(sum=Sum('expenseTotal'))
	expense = ProjectExpense.objects.filter(project=project, status='Approved').exclude(expenseReceipt__isnull=True)

	template_name = 'sdrc/budgetreport.html'
	context = {'project': project, 'category': category, 'currentdate': datetime.date.today(), 'expensesum': expensesum, 'expense': expense}
	return render(request, template_name, context)

def add_members(request):

	if request.user.is_staff:
		projectID = request.session['pid']
	elif request.user.profile.principal_investigator:
		projectID = request.user.id

	members = BudgetCategory.objects.filter(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True), category='Personnel')
	print(members)
	users = User.objects.filter(profile__active_project=False).exclude(is_staff=True)

	form = SignUpForm()

	all_milestones = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True)).order_by('milestonestartDate')
	not_complete_milestone = []

	for m in all_milestones:
		if m.get_finished_task() == 100:
			print("ALL FINISIH TASK")
			print(m.milestoneName)
		else:
			not_complete_milestone.append(m)
			milestones = not_complete_milestone[0]

	if request.method == 'POST':
		role = request.POST.getlist('role')
		amount = request.POST.getlist('amount')
		assigned = request.POST.getlist('assignedTo')

		if role:
			assignedto = []
			profile = []
			member = []
			expenses = []
			user = []
			budget = []
			totalspent = 0
			totalremaining = 0
			active = User.objects.all()
			director = User.objects.get(id=projectID)
			projectdirector = ProjectMember(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True),
									member=director, email=director.email, role='Project Director')
			projectdirector.save()
			for m in members:
				if m.category == 'Personnel':
					if m.title == 'Project Director':
						director = ProjectExpense(
							project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True), milestone=milestones,
							category=m, expenseName='Project Director', expenseQuantity='1', expenseAmount=45000,
							expenseTotal=45000, status='Approved', nowDate=datetime.date.today())
						director.save()
			for a, b, c in zip(assigned, role, amount):
				user = User.objects.get(id=a)
				profile = Profile.objects.all()
				assignedto.append(ProjectMember(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True),
									member=user, email=user.email, role=b))

				for m in members:
					if m.category == 'Personnel' and m.title == b:
						expenses.append(ProjectExpense(
							project=Project.objects.get(principalInvestigator=projectID,
														dateFinished__isnull=True),
							category=m, milestone=milestones, expenseName=b, expenseQuantity='1', expenseAmount=c,
							expenseTotal=c, nowDate=datetime.date.today()))
				for p in profile:
					if p.user == user:
						p.active_project = True
						p.save(update_fields=['active_project'])


			for a in amount:
				spent = Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True).budgetSpent + Decimal(a)
				remaining = Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True).budgetRemaining - Decimal(a)

				projectbudget = Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True)
				projectbudget.budgetSpent = spent
				projectbudget.budgetRemaining = remaining
				projectbudget.save(update_fields=['budgetSpent', 'budgetRemaining'])

			ProjectMember.objects.bulk_create(assignedto)
			ProjectExpense.objects.bulk_create(expenses)



			return HttpResponseRedirect('/addmembers/')

	projectid = request.POST.get("projectID")
	if projectid:
		request.session['pid'] = projectid
		return HttpResponseRedirect('/createtasks/')


	memberid = request.POST.get('memberid')
	if memberid:
		membername = request.POST.get('membername')
		oldmember = request.POST.get('oldmemberid')
		pmember = ProjectMember.objects.get(id=memberid)
		umember = User.objects.get(id=membername)
		pmember.member = umember
		pmember.email = umember.email
		profile = Profile.objects.get(user=umember)
		profile.active_project = True
		profile.save(update_fields=['active_project'])
		oldprofile = Profile.objects.get(user=oldmember)
		oldprofile.active_project = False
		oldprofile.save(update_fields=['active_project'])
		pmember.save(update_fields=['member', 'email'])
		assigned = oldprofile.user.first_name + ' ' + oldprofile.user.last_name
		tasks = Task.objects.filter(assignedTo=assigned)
		for t in tasks:
			t.assignedTo = pmember.member.first_name + ' ' + pmember.member.last_name
			t.save(update_fields=['assignedTo'])


		subject = '[SDRC] Project Assignment'
		message = 'You have been assigned the project entitled: ' + Project.objects.get(principalInvestigator=projectID).projectTitle + '.' + 'Please contact SDRC Admin to get your account details if you are new to the system. Otherwise, log in to the system. Thank you!'
		email_from = settings.EMAIL_HOST_USER
		recipient_list = [umember.email]

		send_mail(subject, message, email_from, recipient_list)

	member = ProjectMember.objects.filter(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True))
	memberUpdate = request.POST.get('memberUpdate')
	if memberUpdate == 'Update':
		memberID = request.POST.get('memberID')
		member = ProjectMember.objects.get(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True),
										   id=memberID)
		new_first_name = request.POST.get('new_first_name')
		new_last_name = request.POST.get('new_last_name')
		new_email = request.POST.get('new_email')
		new_role = request.POST.get('new_role')
		if new_first_name:
			member.first_name = new_first_name
			member.save(update_fields=['first_name'])
		if new_last_name:
			member.last_name = new_last_name
			member.save(update_fields=['last_name'])
		if new_email:
			member.email = new_email
			member.save(update_fields=['email'])
		if new_role:
			member.role = new_role
			member.save(update_fields=['role'])
	elif memberUpdate == 'Delete':
		memberID = request.POST.get('memberID')
		member = ProjectMember.objects.get(project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True),
										   id=memberID).delete()

		return HttpResponseRedirect('/addmembers/')


	context = {'projectmembers': members, 'notifications': get_notifications(request), 'members': ProjectMember.objects.filter(
		project=Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True)), 'project': Project.objects.get(principalInvestigator=projectID, dateFinished__isnull=True), 'form': form,
			   'users': users, 'pid': projectID}
	return render(request, 'sdrc/addmembers.html', context)


class LoginView(TemplateView):
	template_name = 'sdrc/login.html'
	context_object_name = 'login'


def view_reallocation (request):

	if request.user.is_staff:
		project = Project.objects.all()

		totalcategories =[]
		totalrealloc =[]
		totalexpense = []

		for p in project:
			categories = BudgetCategory.objects.filter(project=p)
			reallocation = Reallocation.objects.filter(project=p)
			total = ProjectExpense.objects.filter(project=p).values('project', 'category', 'status').annotate(sum=Sum('expenseTotal')).order_by('category', 'status')

			for c in categories:
				totalcategories.append(c)

			for r in reallocation:
				totalrealloc.append(r)

			for e in total:
				totalexpense.append(e)

		if request.is_ajax():
			print("ajax gumana")
			new_requestamount = request.POST.get('new_request_amount')
			new_selectedamount = request.POST.get('new_reallocated_amount')
			approveDate = request.POST.get('approved_date')
			amount_approve = request.POST.get('amount_reallocated')
			remarks = request.POST.get('remarks')
			status = request.POST.get('status')
			category_request = request.POST.get('category_requested')
			category_select = request.POST.get('category_reallocated')
			rid = json.loads(request.POST['request_id'])

			if status == 'Approve':
				print("Approve naman tangina naman")
				print(rid)
				print(status)
				print(approveDate)
				test = Reallocation.objects.get(id=rid)
				test.status = status
				test.save(update_fields=['status'])
				for p in project:
					categories = BudgetCategory.objects.filter(project=p)
					reallocation = Reallocation.objects.filter(project=p)





					for c in categories:
						if c.project == p:

							if c.title == category_request:
								c.subtotal = new_requestamount
								c.save(update_fields=['subtotal'])
							if c.title == category_select:
								c.subtotal = new_selectedamount
								c.save(update_fields=['subtotal'])




			else:
				test = Reallocation.objects.get(id=rid)
				test.status = status
				test.remarks = remarks
				test.save(update_fields=['status','remarks'])




		context ={

			'projects': project,
			'categories':totalcategories,
			'reallocations':totalrealloc,
			'expenses':totalexpense, 'notifications': get_notifications(request)
		}

		return render(request,'sdrc/view_reallocations.html',context)
	else:
		projects = Project.objects.filter(principalInvestigator=request.user.id, dateFinished__isnull=True)
		print(projects)
		return render(request, 'sdrc/view_reallocations.html', context={'projects': projects})

def user_list(request):
	users = User.objects.filter(is_staff=False)

	if request.method == 'POST':
		userID = request.POST.get('userID')

		user = User.objects.get(id=userID)
		user.delete()

	return render(request, 'sdrc/user_list.html', context={'users': users})
def incidentreport_summary(request):
	template_name = 'sdrc/incidentreportsummary.html'

	startDate = request.session['startDate']
	endDate = request.session['endDate']
	pstartDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
	pendDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()

	budget = IncidentReport.objects.filter(category='Budget', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()
	milestone = IncidentReport.objects.filter(category='Milestone/Task', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()
	deadline = IncidentReport.objects.filter(category='Deadline', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()
	data = IncidentReport.objects.filter(category='Data Gathering', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()
	member = IncidentReport.objects.filter(category='Project Member', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()
	funding = IncidentReport.objects.filter(category='Funding Agency', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()
	others = IncidentReport.objects.filter(category='Others', nowDate__lte=pendDate, nowDate__gte=pstartDate).count()

	name = User.objects.get(id=request.user.id).first_name + ' ' + User.objects.get(id=request.user.id).last_name


	incident = [budget, milestone, deadline, data, member, funding, others]
	return render(request, template_name, context={'incident': incident, 'name': name, 'fromdate': startDate, 'todate': endDate})

def IncidentReportsView(request):
	template_name = 'sdrc/viewincidentreports.html'
	context_object_name = 'incidentreport'
	model = IncidentReport

	current_user = request.user
	milestone = 0
	all_incident_report = IncidentReport.objects.all()

	if not request.user.is_staff:
		if request.user.profile.principal_investigator and request.user.profile.active_project:
			milestone = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True))
			context = {'milestone': milestone, 'users': User.objects.all(), 'notifications': get_notifications(request)}

			if request.method == 'POST':
				issueID = request.POST.get('issueID')
				issueEncountered = request.POST['issueEncountered']
				incidentInfo = IncidentReport.objects.get(id=issueID)
				issueResolution = request.POST.get('issueResolution')
				file = request.FILES.get("files")
				oldissueResolution = request.POST.get('oldissueResolution')

				if issueResolution:
					incidentInfo.issueStatus = True
					incidentInfo.issueResolution = issueResolution
					incidentInfo.file = file
					incidentInfo.resolvedBy = request.user
					incidentInfo.save()
				if oldissueResolution:
					issueID = request.POST.get('issueID')
					issue = IncidentReport.objects.get(id=issueID)
					newissueResolution = request.POST['newissueResolution']
					issue.issueResolution = newissueResolution
					issue.save(update_fields=['issueResolution'])
			return render(request, 'sdrc/viewincidentreports.html', context)
		elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					milestone = Milestone.objects.filter(
						project=p)



	context = {'all_incident_report': all_incident_report, 'milestone': milestone, 'users': User.objects.all(), 'notifications': get_notifications(request)}
	return render(request, 'sdrc/viewincidentreports.html', context)


def view_reimbursements(request):
	template_name = 'sdrc/view_reimbursements.html'
	user = ()

	projects = []

	if request.user.is_staff:
		budget_extension = Project.objects.all()

		if request.method == 'POST':
			status = request.POST.get('status')
			if status == 'Approved':
				budgetID = request.POST.get('budgetID')
				projectID = request.POST.get('projectID')
				approvedAmount = request.POST.get('approvedAmount')
				totalallocated = request.POST.get('totalallocated')
				remarks = request.POST.get('remarks')
				itemType = request.POST.get('itemType')
				budgetalloc = request.POST.get('allocatedleft')
				totalcost = request.POST.get('budgetspent')
				budget = request.POST.get('budgetremaining')

				expense = ProjectExpense.objects.get(id=budgetID)

				expense.expenseTotal = approvedAmount
				expense.expenseDate = datetime.date.today()
				expense.status = status
				expense.remarks = remarks
				project = Project.objects.get(id=projectID)
				if project.hasTranche == True:
					milestone = Milestone.objects.get(id=expense.milestone.id)
					milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
					milestone.trancheAmount = milestoneTranche
					milestone.save(update_fields=['trancheAmount'])
				expense.save()

				if itemType == 'Hotel Booking':
					category = BudgetCategory.objects.get(project=projectID, title='Accomodations')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Flight Tickets':
					category = BudgetCategory.objects.get(project=projectID, title='Transportation')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Field Expense (No Official Receipt)':
					category = BudgetCategory.objects.get(project=projectID, title='Other Expense')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Field Expense (Repair and Maintenance of Equipment)':
					category = BudgetCategory.objects.get(project=projectID, title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Scientific Equipment and Supplies':
					category = BudgetCategory.objects.get(project=projectID, title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Specialized Scientific/Laboratory Services':
					category = BudgetCategory.objects.get(project=projectID, title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Scientific Software and Databases':
					category = BudgetCategory.objects.get(project=projectID, title='Supplies and Materials')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Scientific Literature':
					category = BudgetCategory.objects.get(project=projectID, title='Supplies and Materials')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Research Dissemination Expenses':
					category = BudgetCategory.objects.get(project=projectID, title='Training')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
			else:
				budgetID = request.POST.get('budgetID')
				projectID = request.POST.get('projectID')
				remarks = request.POST.get('remarks')

				expense = ProjectExpense.objects.get(id=budgetID)
				expense.status = status
				expense.remarks = remarks
				expense.save()

		context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
		return render(request, template_name, context)


	else:
		if request.user.profile.principal_investigator and request.user.profile.active_project:
			budget_extension = ProjectExpense.objects.filter(expenseType='Reimbursement', project=Project.objects.get(
				principalInvestigator=request.user.id, dateFinished__isnull=True))
		elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					budget_extension = ProjectExpense.objects.filter(expenseType='Reimbursement', project=p)

		context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
		return render(request, template_name, context)

def inventory_report(request):
    template = 'sdrc/inventoryrequest.html'
    project = Project.objects.get(principalInvestigator = request.user.id)
    category = BudgetCategory.objects.filter(project=project,title='Equipment')
    procured = []
    for c in category:
        print(c.id)
        print(c.project)
        expense = ProjectExpense.objects.filter(project=project, status='Approved', expenseType='Procurement',
                                                category=c).values('project', 'expenseName').distinct().annotate(
            sum=Sum('expenseQuantity'))
        for e in expense:
            procured.append(e)
            print(procured)

    context = {
        'project': project,
        'procured': procured,
        'category':category
    }
    return render(request, template, context)


def inventory_report_admin(request):
    template = 'sdrc/inventoryrequestadmin.html'
    project = Project.objects.all()
    procured = []
    expenses = []

    for p in project:
        # expense = ProjectExpense.objects.filter(project=p,status='Approved',expenseType='Procurement').values('project','category','expenseName').distinct().annotate(sum=Sum('expenseQuantity'))
        category = BudgetCategory.objects.filter(project=p,title='Equipment')
        for c in category:
            print(c.id)
            print(c.project)
            expense = ProjectExpense.objects.filter(project=p, status='Approved', expenseType='Procurement',category=c).values('project', 'expenseName').distinct().annotate(sum=Sum('expenseQuantity'))
            for e in expense:
                procured.append(e)
                print(procured)

        #
        #
        # for e in expense:
        #     procured.append(e)
        # for e in expense:
            # if e.category.title == 'Equipment' and e.expenseType == 'Procurement':
            #     procured_equipment = ProjectExpense.objects.filter(project=e.project,category=e.category).values('')
            #     print("YAS")
            #     print(procured_equipment)



    context = {
        'project': project,
        'procured': procured,

    }

    return render(request, template, context)


def view_budget_extension(request):
	template_name = 'sdrc/requestbudgetextension.html'
	user = ()
	budget_extension = ()

	if request.user.is_staff:
		budget_extension = BudgetExtension.objects.all()
		# for budget in budget_extension:
		# user = User.objects.filter(id=Project.objects.get(budget=Budget.objects.get(budgetextension=budget.id).id).id)

		if request.method == 'POST':
			projectID = request.POST.get('projectID')
			budgetID = request.POST.get('budgetID')
			budget = BudgetExtension.objects.get(id=budgetID)


			print(budget)
			status = request.POST['status']
			remarks = request.POST['remarks']
			approvedAmount = request.POST.get('approvedAmount')
			if approvedAmount:
				budget.approvedAmount = approvedAmount
				budget.status = status
				budget.nowDate = datetime.date.today()
				budget.save(update_fields=['status', 'nowDate', 'approvedAmount'])
				project = Project.objects.get(id=projectID)
				project.budgetRemaining = project.budgetRemaining + Decimal(approvedAmount)
				project.save(update_fields=['budgetRemaining'])
			else:
				budget.status = status
				budget.remarks = remarks
				budget.nowDate = datetime.date.today()
				budget.save()

		context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
		return render(request, template_name, context)

	else:
		if request.user.profile.principal_investigator and request.user.profile.active_project:
			budget_extension = BudgetExtension.objects.filter(
				project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
		elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p:
							project.append(p)

			if project:
				for p in project:
					budget_extension = BudgetExtension.objects.filter(project=p)

		context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
		return render(request, template_name, context)

def create_project_charter(request):
	form = ProjectForm

	if request.method == 'GET':
		form = ProjectForm(request.GET or None)
	elif request.method == 'POST':
		form = ProjectForm(request.POST)
		if form.is_valid():
			principalInvestigator = request.POST['principalInvestigator']
			projectTitle = form.cleaned_data['projectTitle']
			fundingAgency = form.cleaned_data['fundingAgency']
			projectDate = form.cleaned_data['projectDate']
			new_project = Project(principalInvestigator=principalInvestigator, projectTitle=projectTitle,
								  fundingAgency=fundingAgency, projectDate=projectDate)
			new_project.save()

	user = User.objects.all()
	context = {'form': form, 'user': user, 'notifications': get_notifications(request)}
	return render(request, 'sdrc/projectcharter.html', context)

def milestone_list(request):
	project = Project.objects.all()

	if request.method == 'POST':
		pid = request.POST.get("projectID")
		request.session['projectID'] = pid
		return HttpResponseRedirect("/createmilestone/")

	context = {
		'projects': project,

	}
	return render(request, 'sdrc/milestone_list.html', context)

def member_list(request):
	project = Project.objects.all()

	if request.method == 'POST':
		pid = request.POST.get("projectID")
		request.session['pid'] = pid
		return HttpResponseRedirect("/addmembers/")

	context = {
		'projects': project,

	}
	return render(request, 'sdrc/member_list.html', context)

def task_list(request):
	project = Project.objects.all()

	if request.method == 'POST':
		pid = request.POST.get("projectID")
		request.session['pid'] = pid
		return HttpResponseRedirect("/createtasks/")

	context = {
		'projects': project,

	}
	return render(request, 'sdrc/task_list.html', context)

def create_project(request):
	template_name = 'sdrc/createmilestone.html'

	if request.user.is_staff:
		pid = request.session['projectID']
	elif request.user.profile.principal_investigator:
		pid = request.user.id

		project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
	formset = MilestoneForm()
	updateform = UpdateMilestoneForm()
	if request.method == 'GET':
		formset = MilestoneForm(request.GET or None)
	elif request.method == 'POST':
		formset = MilestoneForm(request.POST or None)
		if formset.is_valid():
			trancheAmount = Decimal(request.POST.get('trancheAmount'))
			if trancheAmount:
				milestonestartDate = request.POST.get('milestonestartDate')
				milestoneendDate = request.POST.get('milestoneendDate')
				project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
				milestoneName = request.POST.get('milestoneName')
				if datetime.datetime.strptime(milestonestartDate, "%Y-%m-%d").date() < project.startDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestonestartDate, "%Y-%m-%d").date() > project.endDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestoneendDate, "%Y-%m-%d").date() > project.endDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestoneendDate, "%Y-%m-%d").date() < project.startDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestoneendDate, "%Y-%m-%d").date() < datetime.datetime.strptime(milestonestartDate, "%Y-%m-%d").date():
					messages.warning(request, 'Start date cannot be later than the end date')
					return redirect('/createmilestone/')
				elif project.projectCost < trancheAmount:
					messages.warning(request, 'Tranche Amount exceeds total project budget!'
											  ' Remaining Budget: ' + str(project.projectCost))
					return redirect('/createmilestone/')
				else:
					new_milestone = Milestone(project=project, milestoneName=milestoneName,
										  milestonestartDate=milestonestartDate, milestoneendDate=milestoneendDate,
										  nowDate=datetime.date.today(), trancheAmount=trancheAmount)
					projectBudget = project.projectCost - trancheAmount
					project.projectCost = projectBudget
					project.save(update_fields=['projectCost'])
					new_milestone.save()

		else:
			milestonestartDate = request.POST.get('milestonestartDate')
			milestoneendDate = request.POST.get('milestoneendDate')
			project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
			milestoneName = request.POST.get('milestoneName')

			if milestonestartDate:
				if datetime.datetime.strptime(milestonestartDate, "%Y-%m-%d").date() < project.startDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestonestartDate, "%Y-%m-%d").date() > project.endDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestoneendDate, "%Y-%m-%d").date() > project.endDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestoneendDate, "%Y-%m-%d").date() < project.startDate:
					messages.warning(request, 'Milestone date not within the project date!')
					return redirect('/createmilestone/')
				elif datetime.datetime.strptime(milestoneendDate, "%Y-%m-%d").date() < datetime.datetime.strptime(
						milestonestartDate, "%Y-%m-%d").date():
					messages.warning(request, 'Start date cannot be later than the end date')
					return redirect('/createmilestone/')
				else:
					new_milestone = Milestone(project=project, milestoneName=milestoneName,
											  milestonestartDate=milestonestartDate, milestoneendDate=milestoneendDate,
											  nowDate=datetime.date.today())

					new_milestone.save()
					return HttpResponseRedirect('/createmilestone/')



	milestoneUpdate = request.POST.get('milestoneUpdate')
	if milestoneUpdate == 'Update':
		updateform = UpdateMilestoneForm(request.POST)
		milestoneID = request.POST.get('milestoneID')
		milestone = Milestone.objects.get(id=milestoneID)
		newmilestoneName = request.POST.get('newmilestoneName')
		newmilestonestartDate = request.POST.get('newmilestonestartDate')
		newmilestoneendDate = request.POST.get('newmilestoneendDate')

		if newmilestoneName:
			milestone.milestoneName = newmilestoneName
			milestone.save(update_fields=['milestoneName'])
		if newmilestonestartDate:
			project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
			if datetime.datetime.strptime(newmilestonestartDate, "%Y-%m-%d").date() < project.startDate:
				messages.warning(request, 'Milestone date not within the project date!')
				return redirect('/createmilestone/')
			elif datetime.datetime.strptime(newmilestonestartDate, "%Y-%m-%d").date() > project.endDate:
				messages.warning(request, 'Milestone date not within the project date!')
				return redirect('/createmilestone/')
			else:
				milestone.milestonestartDate = newmilestonestartDate
				milestone.save(update_fields=['milestonestartDate'])
		if newmilestoneendDate:
			project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
			if datetime.datetime.strptime(newmilestoneendDate, "%Y-%m-%d").date() < project.startDate:
				messages.warning(request, 'Milestone date not within the project date!')
				return redirect('/createmilestone/')
			elif datetime.datetime.strptime(newmilestoneendDate, "%Y-%m-%d").date() > project.endDate:
				messages.warning(request, 'Milestone date not within the project date!')
				return redirect('/createmilestone/')
			else:
				milestone.milestoneendDate = newmilestoneendDate
				milestone.save(update_fields=['milestoneendDate'])

	elif milestoneUpdate == 'Delete':
		milestoneID = request.POST.get('milestoneID')
		milestone = Milestone.objects.get(project=Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True),
										  id=milestoneID).delete()

		return HttpResponseRedirect('/createmilestone/')

	dontload = request.POST.get('dontload')
	if dontload:
		projectID = request.POST.get('projectID')
		request.session['pid'] = projectID
		return HttpResponseRedirect('/addmembers/')

	all_formset = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)).order_by('milestonestartDate')
	return render(request, 'sdrc/createmilestone.html',
				  {'formset': formset, 'updateform': updateform,
				   'projects': Project.objects.filter(principalInvestigator=pid, dateFinished__isnull=True),
				   'all_formset': all_formset, 'pid': pid})


def create_tasks(request):

	if request.user.is_staff:
		pid = request.session['pid']
	elif request.user.profile.principal_investigator:
		pid = request.user.id

	form = TaskForm()
	updateform = UpdateTaskForm()

	if request.method == 'GET':
		form = TaskForm(request.GET or None)
	elif request.method == 'POST':
		form = TaskForm(request.POST)
		if form.is_valid():
			project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
			taskName = request.POST.get('taskName')
			taskstartDate = request.POST.get('taskstartDate')
			taskendDate = request.POST.get('taskendDate')
			milestoneID = request.POST.get('milestoneID')
			milestone = Milestone.objects.get(id=milestoneID)
			assignedTo = request.POST.get('assignedTo')
			if datetime.datetime.strptime(taskstartDate, "%Y-%m-%d").date() < milestone.milestonestartDate:
				messages.warning(request, 'Task date not within the milestone date!')
				return redirect('/createtasks/')
			elif datetime.datetime.strptime(taskstartDate, "%Y-%m-%d").date() > milestone.milestoneendDate:
				messages.warning(request, 'Task date not within the milestone date')
				return redirect('/createtasks/')
			elif datetime.datetime.strptime(taskendDate, "%Y-%m-%d").date() > milestone.milestoneendDate:
				messages.warning(request, 'Task date not within the milestone date')
				return redirect('/createtasks/')
			elif datetime.datetime.strptime(taskendDate, "%Y-%m-%d").date() < milestone.milestonestartDate:
				messages.warning(request, 'Task date not within the milestone date')
				return redirect('/createtasks/')
			elif datetime.datetime.strptime(taskendDate, "%Y-%m-%d").date() < datetime.datetime.strptime(taskstartDate, "%Y-%m-%d").date():
				messages.warning(request, 'Start date cannot be later than the end date')
				return redirect('/createtasks/')
			else:
				task = Task(project=project, milestone=milestone, taskName=taskName, assignedTo=assignedTo, taskstartDate=taskstartDate, taskendDate=taskendDate, nowDate=datetime.date.today())
				task.save()
				return redirect('/createtasks/')

		taskUpdate = request.POST.get('taskUpdate')
		if taskUpdate == 'Update':
			updateform = UpdateTaskForm(request.POST)
			if updateform.is_valid():
				taskID = request.POST.get('taskID')
				task = Task.objects.get(project=Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True),
										id=taskID)
				newtaskName = request.POST.get('newtaskName')
				newassignedTo = request.POST.get('newassignedTo')
				newtaskstartDate = request.POST.get('newtaskstartDate')
				newtaskendDate = request.POST.get('newtaskendDate')

				if newtaskName:
					task.taskName = newtaskName
					task.save(update_fields=['taskName'])
				if newassignedTo:
					task.assignedTo = newassignedTo
					task.save(update_fields=['assignedTo'])
				if newtaskstartDate:
					task.taskstartDate = newtaskstartDate
					task.save(update_fields=['taskstartDate'])
				if newtaskendDate:
					task.taskendDate = newtaskendDate
					task.save(update_fields=['taskendDate'])
		elif taskUpdate == 'Delete':
			taskID = request.POST.get('taskID')
			task = Task.objects.get(project=Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True),
									id=taskID).delete()

			return HttpResponseRedirect('/createtasks/')

	members = ProjectMember.objects.filter(project=Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True))
	milestones = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)).order_by('milestonestartDate')

	return render(request, template_name='sdrc/createtasks.html',
				  context={'notifications': get_notifications(request), 'members': members, 'milestones': milestones,
						   'form': form, 'updateform': updateform})


class AppointmentFormView(TemplateView):
	template_name = 'sdrc/appointmentform.html'
	context_object_name = 'appointmentform'


def accomplishment_report(request):
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
	currentdate = datetime.date.today()

	context = {'project': project, 'currentdate':currentdate }

	return render(request, 'sdrc/accomplishmentreport.html', context)


def progress_report(request):
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)

	users = User.objects.all()
	milestone = Milestone.objects.filter(project=project)
	task = Task.objects.filter(project=project)
	currentdate = datetime.date.today()
	in_progress_task = (Task.objects.filter(taskStatus='In Progress', project=project).count())
	not_started_task = (Task.objects.filter(taskStatus='Not Started', project=project).count())
	delayed_task = (Task.objects.filter(project=project,
										taskStatus='In Progress',
										taskendDate__lt=datetime.date.today()).count() + Task.objects.filter(
		taskStatus='Not Started', taskendDate__lt=datetime.date.today()).count())
	finished_task = Task.objects.filter(taskStatus='Completed', project=project).count()
	milestonestatus = []
	for m in milestone:
		if m.task_set.filter(taskStatus='Not Started').count() == m.task_set.all().count():
			status = "Not Started"
			milestonestatus.append(status)
		if m.task_set.filter(taskStatus='In Progress').exists():
			status = "In Progress"
			milestonestatus.append(status)
		if m.task_set.filter(taskStatus='Completed').count() == m.task_set.all().count():
			print(m.task_set.all().count())
			status = "Completed"
			milestonestatus.append(status)

	zipped_data = zip(milestone, milestonestatus)

	array = []

	for m in Task.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
		id = Task.objects.get(id=m.id).id
		milestone = Task.objects.get(id=m.id).milestone.milestoneName
		name = Task.objects.get(id=m.id).taskName
		resource = Task.objects.get(id=m.id).assignedTo
		startdate = Task.objects.get(id=m.id).taskstartDate
		enddate = Task.objects.get(id=m.id).taskendDate

		if "Not Started" in m.taskStatus:
			status = 0
		elif "In Progress" in m.taskStatus:
			status = 50
		elif "Completed" in m.taskStatus:
			status = 100

		array1 = [milestone, name, resource, startdate.isoformat(), enddate.isoformat(), status]
		array.append(array1)

	milestone_list = []
	for mile in Milestone.objects.filter(project=project):

		if mile.get_finished_task() < 100 and mile.milestoneendDate < datetime.date.today():
			milestone_list.append(mile)

	budgetcategory = BudgetCategory.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)).values('category', 'title').annotate(sum=Sum('allocatedAmount'))
	totalexpense = ProjectExpense.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), status='Approved').exclude(expenseReceipt__isnull=True).values('category', 'category__title').annotate(sum=Sum('expenseTotal'))
	print(totalexpense)
	context = {'id': json.dumps(id), 'name': json.dumps(name), 'resource': json.dumps(resource), 'startdate': startdate,
			   'enddate': enddate, 'array': array, 'notifications': get_notifications(request), 'project': project,
			   'milestone': milestone, 'zipped_data': zipped_data, 'task': task, 'currentdate': currentdate, 'totalexpense': totalexpense,
			   'in_progress_task': in_progress_task,
			   'not_started_task': not_started_task, 'milestone_list': milestone_list, 'users': users, 'delayed_task': delayed_task, 'finished_task': finished_task, 'budgetcategory': budgetcategory}

	return render(request, 'sdrc/progressreport.html', context)


def ShowNotifBase(request):
	currentdate = datetime.date.today()
	milestones = Milestone.objects.all().filter(milestoneStatus=True)
	projects = Project.objects.all().filter(endDate__lte=currentdate)
	milestone_count = Milestone.objects.all().filter(milestoneStatus=True).count()
	project_count = Project.objects.all().filter(endDate__lte=currentdate).count()
	notif_count = milestone_count + project_count

	context = {
		'milestones': milestones,
		'projects': projects,
		'notif_count': notif_count, 'notifications': get_notifications(request)
	}

	return render(request, 'sdrc/base.html', context)


def incident_report_post(request):
	current_user = request.user

	if request.method == 'GET':
		incidentInfo = IncidentReport()

	if request.method == 'POST':
		milestone = request.POST['milestone']
		milestoneInfo = Milestone.objects.get(id=milestone)
		issueEncountered = request.POST['issueEncountered']
		issueDescription = request.POST['issueDescription']
		dateEncountered = request.POST['dateEncountered']

		incidentInfo = IncidentReport(issueEncountered=issueEncountered, issueDescription=issueDescription,
									  dateEncountered=dateEncountered, nowDate=datetime.date.today())
		incidentInfo.milestone = milestoneInfo
		incidentInfo.save()

	all_projects = Project.objects.get(principalInvestigator=current_user.id, dateFinished__isnull=True)
	milestone = Milestone.objects.filter(project=all_projects)
	incident = ()

	context = {'notifications': get_notifications(request), 'milestone': milestone, 'incident': incident}
	return render(request, 'sdrc/createincidentreport.html', context)


def GanttChartView(request):
	template_name = 'sdrc/ganttchart.html'
	context_object_name = 'ganttchart'

	array = []

	for m in Task.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
		id = Task.objects.get(id=m.id).id
		milestone = Task.objects.get(id=m.id).milestone.milestoneName
		name = Task.objects.get(id=m.id).taskName
		resource = Task.objects.get(id=m.id).assignedTo
		startdate = Task.objects.get(id=m.id).taskstartDate
		enddate = Task.objects.get(id=m.id).taskendDate

		if "Not Started" in m.taskStatus:
			status = 0
		elif "In Progress" in m.taskStatus:
			status = 50
		elif "Completed" in m.taskStatus:
			status = 100

		array1 = [milestone, name, resource, startdate.isoformat(), enddate.isoformat(), status]
		array.append(array1)
		print(array1)

	context = {'id': json.dumps(id), 'name': json.dumps(name), 'resource': json.dumps(resource), 'startdate': startdate,
			   'enddate': enddate, 'array': array, 'notifications': get_notifications(request)}

	return render(request, template_name, context)

def SampleGanttView(request):
	template_name = 'sdrc/samplegantt.html'
	context_object_name = 'ganttchart'

	notstarted_array = []
	inprogress_array = []
	completed_array = []
	array_1 = []

	for m in Milestone.objects.filter(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True).projectTitle
		milestone = Milestone.objects.get(id=m.id).milestoneName
		milestonestartDate = Milestone.objects.get(id=m.id).milestonestartDate
		milestoneendDate = Milestone.objects.get(id=m.id).milestoneendDate
		nowday = datetime.date.today()

		array1 = [milestone, (milestonestartDate - nowday).days, (milestoneendDate - nowday).days, project]
		array_1.append(array1)

	for m in Task.objects.filter(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)):
		id = Task.objects.get(id=m.id).id
		milestone = Task.objects.get(id=m.id).milestone.milestoneName
		milestonestartDate = Task.objects.get(id=m.id).milestone.milestonestartDate
		milestoneendDate = Task.objects.get(id=m.id).milestone.milestoneendDate
		name = Task.objects.get(id=m.id).taskName
		resource = Task.objects.get(id=m.id).assignedTo
		nowday = datetime.date.today()
		startdate = Task.objects.get(id=m.id).taskstartDate
		enddate = Task.objects.get(id=m.id).taskendDate
		status = 0
		if "Not Started" in m.taskStatus:
			status = 0
			array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
			notstarted_array.append(array1)
		elif "In Progress" in m.taskStatus:
			status = 50
			array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
			inprogress_array.append(array1)
		elif "Completed" in m.taskStatus:
			status = 100
			array1 = [milestone, name, resource, (startdate - nowday).days, (enddate - nowday).days, status]
			completed_array.append(array1)

	context = {'notstarted_array': notstarted_array, 'inprogress_array': inprogress_array, 'completed_array': completed_array, 'array_1': array_1, 'notifications': get_notifications(request)}

	return render(request, template_name, context)


class ExpenseListView(TemplateView):
	template_name = 'sdrc/expenselist.html'
	context_object_name = 'expenselist'


def ExpenseTracking(request):
	if request.user.profile.principal_investigator and request.user.profile.active_project:
		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)

		allmilestones = []
		allcategories = []
		allmembers = []
		allexpense = []
		totalexpense = []
		allprojectmembers = []

		categories = BudgetCategory.objects.filter(project=project)
		members = ProjectExpense.objects.filter(project=project)
		expense = ProjectExpense.objects.filter(project=project)
		milestone = Milestone.objects.filter(project=project)
		projectmembers = ProjectExpense.objects.filter(project=project).values('category', 'expenseName').annotate(
			sum=Sum('expenseQuantity'))
		total = ProjectExpense.objects.filter(project=project).values('project', 'category', 'status',
																	  'milestone').annotate(
			sum=Sum('expenseTotal')).order_by('category', 'status')

		for c in categories:
			allcategories.append(c)

		for m in members:
			allmembers.append(m)

		for e in expense:
			if e.expenseReceipt:
				allexpense.append(e)

		for te in total:
			totalexpense.append(te)

		for pm in projectmembers:
			allprojectmembers.append(pm)

		for mil in milestone:
			allmilestones.append(mil)

		if request.is_ajax():
			print("ajax success")
			category_request = request.POST.get("category_requested")
			category_reallocate = request.POST.get("category_reallocated")
			amount_requested = request.POST.get("requested_amount")

			reallocation = Reallocation(
				project=project,
				category_selected_for_reallocation=category_reallocate,
				category_requested=category_request,
				amountReallocated=amount_requested
			)
			reallocation.save()
	elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					project = p

					allmilestones = []
					allcategories = []
					allmembers = []
					allexpense = []
					totalexpense = []
					allprojectmembers = []

					categories = BudgetCategory.objects.filter(project=project)
					members = ProjectExpense.objects.filter(project=project)
					milestone = Milestone.objects.filter(project=project)
					expense = ProjectExpense.objects.filter(project=project)
					projectmembers = ProjectExpense.objects.filter(project=project).values('category',
																						   'expenseName').annotate(
						sum=Sum('expenseQuantity'))
					total = ProjectExpense.objects.filter(project=project).values('project', 'category',
																				  'status').annotate(
						sum=Sum('expenseTotal')).order_by('category', 'status')

					for mil in milestone:
						allmilestones.append(mil)

					for c in categories:
						allcategories.append(c)

					for m in members:
						allmembers.append(m)

					for e in expense:
						if e.expenseReceipt:
							allexpense.append(e)

					for te in total:
						totalexpense.append(te)

					for pm in projectmembers:
						allprojectmembers.append(pm)

					if request.is_ajax():
						print("ajax success")
						category_request = request.POST.get("category_requested")
						category_reallocate = request.POST.get("category_reallocated")
						amount_requested = request.POST.get("requested_amount")

						reallocation = Reallocation(
							project=project,
							category_selected_for_reallocation=category_reallocate,
							category_requested=category_request,
							amountReallocated=amount_requested
						)
						reallocation.save()

					totalallocated = BudgetCategory.objects.filter(project=project).values('project', 'category').annotate(
						sum=Sum('allocatedAmount'))
					totalprojected = BudgetCategory.objects.filter(project=project).values('project').aggregate(
						sum=Sum('allocatedAmount'))

	context = {
		'projectmembers': allprojectmembers,
		'projects': project,
		'categories': allcategories,
		'members': allmembers,
		'expenses': allexpense,
		'totalexpense': totalexpense,
		'notifications': get_notifications(request),
		'milestones': allmilestones
	}

	return render(request,'sdrc/expensetracking.html',context)

class UploadProjectInformationView(TemplateView):
	template_name = 'sdrc/uploadprojectinformation.html'
	context_object_name = 'uploadprojectinformation'


def MilestoneStatusView(request):
	template_name = 'sdrc/milestonestatus.html'

	if request.user.profile.principal_investigator and request.user.profile.active_project:
		milestone = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
		taskform = TaskFinishedForm()
		incidentform = IncidentForm()
		incident = []

		if request.method == 'POST':
			form = TaskFinishedForm(request.POST)
			if form.is_valid():
				taskID = request.POST.get('taskID')

				task_object = Task.objects.get(id=taskID)
				taskStatus = request.POST.get('taskStatus')
				dateFinished = request.POST.get('taskFinished')
				receipt = request.FILES.get('receipt')
				if taskStatus:
					task_object.taskStatus = taskStatus
					task_object.save(update_fields=['taskStatus'])
				if dateFinished:
					task_object.taskFinished = dateFinished
					task_object.taskFile = receipt
					task_object.nowDate = datetime.date.today()
					task_object.save(update_fields=['taskFinished', 'taskFile', 'nowDate'])

			issueEncountered = request.POST.get('issueEncountered')
			if issueEncountered:
				project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
				taskid = request.POST.get('taskID')
				milestoneid = request.POST.get('milestoneID')
				task = Task.objects.get(id=taskid)
				milestone = Milestone.objects.get(task=task)
				issueDescription = request.POST.get('issueDescription')
				dateEncountered = request.POST.get('dateEncountered')
				issuePriority = request.POST.get('issuePriority')
				issueCategory = request.POST.get('issueCategory')
				new_incident = IncidentReport(project=project, milestone=milestone, task=task, category=issueCategory,
											  issueEncountered=issueEncountered,
											  issueDescription=issueDescription, issuePriority=issuePriority,
											  dateEncountered=dateEncountered, nowDate=datetime.date.today())
				new_incident.save()
				return redirect('incidentreport')

		currentdate = datetime.date.today()

		# for notif
		milestone_count = Milestone.objects.all().filter(milestoneStatus=True).count()
		project_count = Project.objects.all().filter(endDate__lte=currentdate).count()
		notif_count = milestone_count + project_count
		# for notif

		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
		completed_task = Task.objects.filter(taskStatus='Completed', project=project).count()



		context = {'milestones': milestone, 'currentdate': currentdate, 'taskform': taskform, 'project': project,
				   'completed_task': completed_task, 'incidentform': incidentform,
				   'notif_count': notif_count, 'incident': incident, 'notifications': get_notifications(request)}
		return render(request, template_name, context)
	elif not request.user.profile.principal_investigator and request.user.profile.active_project:
		project = []
		for pm in ProjectMember.objects.all():
			if pm.member == request.user:
				for p in Project.objects.all():
					if pm.project == p and not p.dateFinished:
						project.append(p)

		if project:
			for p in project:
				milestone = Milestone.objects.filter(
					project=p)
				taskform = TaskFinishedForm()
				incidentform = IncidentForm()
				incident = []
				name = request.user.first_name + " " + request.user.last_name

				if request.method == 'POST':
					form = TaskFinishedForm(request.POST)
					if form.is_valid():
						taskID = request.POST.get('taskID')

						task_object = Task.objects.get(id=taskID)
						taskStatus = request.POST.get('taskStatus')
						dateFinished = request.POST.get('taskFinished')
						receipt = request.FILES.get('receipt')
						if taskStatus:
							task_object.taskStatus = taskStatus
							task_object.save(update_fields=['taskStatus'])
						if dateFinished:
							task_object.taskFinished = dateFinished
							task_object.taskFile = receipt
							task_object.save(update_fields=['taskFinished', 'taskFile'])

					issueEncountered = request.POST.get('issueEncountered')
					if issueEncountered:
						project = p
						taskid = request.POST.get('taskID')
						milestoneid = request.POST.get('milestoneID')
						task = Task.objects.get(id=taskid)
						milestone = Milestone.objects.get(task=task)
						issueDescription = request.POST.get('issueDescription')
						dateEncountered = request.POST.get('dateEncountered')
						issuePriority = request.POST.get('issuePriority')
						issueCategory = request.POST.get('issueCategory')
						new_incident = IncidentReport(project=project, milestone=milestone, task=task, category=issueCategory,
													  issueEncountered=issueEncountered,
													  issueDescription=issueDescription, issuePriority=issuePriority,
													  dateEncountered=dateEncountered, nowDate=datetime.date.today())
						new_incident.save()
						return redirect('incidentreport')

				currentdate = datetime.date.today()

				# for notif
				milestone_count = Milestone.objects.all().filter(milestoneStatus=True).count()
				project_count = Project.objects.all().filter(endDate__lte=currentdate).count()
				notif_count = milestone_count + project_count
				# for notif

				project = p
				completed_task = Task.objects.filter(taskStatus='Completed', project=project).count()

				context = {'milestones': milestone, 'currentdate': currentdate, 'taskform': taskform,
						   'project': project,
						   'completed_task': completed_task, 'incidentform': incidentform,
						   'notif_count': notif_count, 'incident': incident,
						   'notifications': get_notifications(request), 'name': name}
				return render(request, template_name, context)



class FinancialReportView(TemplateView):
	template_name = 'sdrc/financialreport.html'
	context_object_name = 'financialreport'


class ProjectStatusView(TemplateView):
	template_name = 'sdrc/viewprojectstatus.html'
	context_object_name = 'projectstatus'


def create_expense(request):
	template_name = 'sdrc/createexpense.html'


	# expenses = ProjectExpense.objects.filter(budget=Budget.objects.get(project=Project.objects.get(principalInvestigator=request.user.id).id).id)
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
	# context = {'form': form, 'budget': budget, 'project': project, 'expenses': expenses}
	# return render(request, template_name, context)


class ProjectBudgetView(TemplateView):
	template_name = 'sdrc/projectbudget.html'
	context_object_name = 'projectbudget'


def signup(request):
	form = SignUpForm()
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			# username = form.cleaned_data.get('username')
			# raw_password = User.objects.make_random_password(length=15, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789')
			user.is_active = False
			# Save the User object
			user.save()
			profile = Profile.objects.get(user=user)
			profile.active_project = False
			profile.save()
			# get current site
			current_site = get_current_site(request)
			subject = '[SDRC] Activate Your Account'
			# create Message
			message = render_to_string('registration/password_reset_subject.txt', {
				'user': user,
				'domain': current_site.domain,
				'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode("utf-8"),
				'token': account_activation_token.make_token(user),
			})
			html_message = render_to_string('registration/signup_email.html', {
				'user': user,
				'domain': current_site.domain,
				'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode("utf-8"),
				'token': account_activation_token.make_token(user),
			})
			# send activation link to the user
			user.email_user(subject=subject, message=message, html_message=html_message)
			if request.user.is_staff:
				return redirect('/create-project-account/')
			else:
				return redirect('/signup/')
			# user = authenticate(username=username, password=raw_password)
			# return redirect('create-account')
	else:
		form = SignUpForm()
	return render(request, 'sdrc/signup.html', {'form': form})

def activate(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None

	if user is not None and account_activation_token.check_token(user, token):
		user.backend = 'django.contrib.auth.backends.ModelBackend'
		user.is_active = True
		user.save()
		login(request, user)
		return redirect('/change_password/')
	else:
		return render(request, 'sdrc/signup.html')

def cashadvance(request):
	if request.user.profile.principal_investigator and request.user.profile.active_project:
		itemType = request.POST.get('itemType')
		hotelname = request.POST.get('hotelname')
		hotelpax = request.POST.get('hotelpax')
		hotelplace = request.POST.get('hotelplace')
		hotelestimatedamount = request.POST.get('hotelestimatedamount')
		noofnights = request.POST.get('noofnights')
		hoteldescription = request.POST.get('hoteldescription')
		hotelcheckin = request.POST.get('hotelcheckin')

		flightlocation = request.POST.get('flightlocation')
		destinationname = request.POST.get('destinationname')
		flightpax = request.POST.get('flightpax')
		nooftimes = request.POST.get('nooftimes')
		flightestimatedamount = request.POST.get('flightestimatedamount')
		dateofflight = request.POST.get('dateofflight')
		flightdescription = request.POST.get('flightdescription')
		#
		#OTHERS
		nameofservice = request.POST.get('nameofservice')
		servicequantity = request.POST.get('servicequantity')
		labserviceestimatedamount = request.POST.get('labserviceestimatedamount')
		servicedescription = request.POST.get('servicedescription')
		#
		#OTHERS
		nameofsoftware = request.POST.get('nameofsoftware')
		softwarequantity = request.POST.get('softwarequantity')
		softwareestimatedamount = request.POST.get('softwareestimatedamount')
		softwaredescription = request.POST.get('softwaredescription')
		#
		#OTHERS
		nameofliterature = request.POST.get('nameofliterature')
		literaturequantity = request.POST.get('literaturequantity')
		literatureestimatedamount = request.POST.get('literatureestimatedamount')
		literaturedescription = request.POST.get('literaturedescription')
		#
		#OTHERS
		typeofdissemination = request.POST.get('typeofdissemination')
		disseminationquantity = request.POST.get('disseminationquantity')
		disseminationestimatedamount = request.POST.get('disseminationestimatedamount')
		disseminationdescription = request.POST.get('disseminationdescription')
		#
		#FIELDWORK
		typeoffieldexpense = request.POST.get('typeoffieldexpense')
		fieldexpensequantity = request.POST.get('fieldexpensequantity')
		fieldexpenseestimatedamount = request.POST.get('fieldexpenseestimatedamount')
		fieldexpensedescription = request.POST.get('hoteldescription')
		#
		#FIELDWORK
		typeofrepair = request.POST.get('typeofrepair')
		repairquantity = request.POST.get('repairquantity')
		repairestimatedamount = request.POST.get('repairestimatedamount')
		repairdescription = request.POST.get('repairdescription')
		#
		#OTHERS
		typeofequipment = request.POST.get('typeofequipment')
		equipmentquantity = request.POST.get('equipmentquantity')
		equipmentestimatedamount = request.POST.get('equipmentestimatedamount')
		equipmentdescription = request.POST.get('equipmentdescription')

		budgetcategory = request.POST.get('category')
		amount = request.POST.get('amount')
		expense = request.POST.get('expense')
		description = request.POST.get('description')
		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
		category = BudgetCategory.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))

		milestone = Milestone.objects.filter(project=project).order_by('milestoneendDate')
		milestone_list = []

		all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
		not_complete_milestone = []

		complete_milestone_with_tranche = 0
		for m in all_milestones:
			if m.get_finished_task() == 100:
				if m.trancheAmount:
					if m.trancheAmount != 0:
						complete_milestone_with_tranche += m.trancheAmount

						complet_tranche = Milestone.objects.get(id=m.id)
						complet_tranche.trancheAmount = 0
						complet_tranche.save(update_fields=['trancheAmount'])

			else:
				not_complete_milestone.append(m)
				milestones = not_complete_milestone[0]
		if milestones.trancheAmount:
			milestones.trancheAmount += complete_milestone_with_tranche
			milestones.save(update_fields=['trancheAmount'])
		# complete_milestone_with_tranche = 0

		for m in milestone:
			if m.get_finished_task():
				if m.get_finished_task() < 100 and m.milestoneendDate < datetime.date.today():
					milestone_list.append(m)

		if budgetcategory:
			request.session['category'] = budgetcategory
			request.session['amount'] = amount
			request.session['expense'] = expense
			request.session['description'] = description
			return HttpResponseRedirect('/budgetextensionform/')
		else:
			if itemType == "Hotel Booking":
				for c in category:
					if c.title == 'Accomodations':
						hotelexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
													  expenseType="Cash Advance",
													  expenseName=hotelname,
													  expenseLocation=hotelplace,
													  expenseQuantity=hotelpax,
													  amountRequested=hotelestimatedamount,
													  expenseDescription=hoteldescription,
													  fromDate=hotelcheckin,
													  days=noofnights,
													  status="For Review", nowDate=datetime.date.today())
						hotelexpense.save()

			elif itemType == "Flight Tickets":
				for c in category:
					if c.title == 'Transportation':
						flightexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
													   expenseType = "Cash Advance",
													   expenseName = destinationname,
													   expenseLocation = flightlocation,
													   expenseQuantity = flightpax,
													   amountRequested = flightestimatedamount,
													   expenseDescription=flightdescription,
													   fromDate = dateofflight,
													   status="For Review", nowDate=datetime.date.today())
						flightexpense.save()


			elif itemType == "Field Expense (No Official Receipt)":
				for c in category:
					if c.title == 'Other Expense':
						fieldexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
													  expenseType = "Cash Advance",
													  expenseName = typeoffieldexpense,
													  expenseQuantity = fieldexpensequantity,
													  amountRequested = fieldexpenseestimatedamount,
													  expenseDescription=fieldexpensedescription,
													  status="For Review", nowDate=datetime.date.today())
						fieldexpense.save()

			elif itemType == "Field Expense (Repair and Maintenance of Equipment)":
				for c in category:
					if c.title == 'Other Expense':
						repairexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
													   expenseType = "Cash Advance",
													   expenseName = typeofrepair,
													   expenseQuantity = repairquantity,
													   amountRequested = repairestimatedamount,
													   expenseDescription=repairdescription,
													   status="For Review", nowDate=datetime.date.today())
						repairexpense.save()


			elif itemType == "Specialized Scientific/Laboratory Services":
				for c in category:
					if c.title == 'Equipment':
						serviceexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
														expenseType = "Cash Advance",
														expenseName = nameofservice,
														expenseQuantity = servicequantity,
														amountRequested = labserviceestimatedamount,
														expenseDescription=servicedescription,
														status="For Review", nowDate=datetime.date.today())
						serviceexpense.save()

			elif itemType == "Scientific Software and Databases":
				for c in category:
					if c.title == 'Supplies and Materials':
						softwareexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
														 expenseType = "Cash Advance",
														 expenseName = nameofsoftware,
														 expenseQuantity = softwarequantity,
														 amountRequested = softwareestimatedamount,
														 expenseDescription=softwaredescription,
														 status="For Review", nowDate=datetime.date.today())
						softwareexpense.save()

			elif itemType == "Scientific Literature":
				for c in category:
					if c.title == 'Supplies and Materials':
						literatureexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
														   expenseType = "Cash Advance",
														   expenseName = nameofliterature,
														   expenseQuantity = literaturequantity,
														   amountRequested = literatureestimatedamount,
														   expenseDescription=literaturedescription,
														   status="For Review", nowDate=datetime.date.today())
						literatureexpense.save()

			elif itemType == "Research Dissemination Expenses":
				for c in category:
					if c.title == 'Training':
						disseminationexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
															  expenseType = "Cash Advance",
															  expenseName = typeofdissemination,
															  expenseQuantity = disseminationquantity,
															  amountRequested = disseminationestimatedamount,
															  expenseDescription=disseminationdescription,
															  status="For Review", nowDate=datetime.date.today())
						disseminationexpense.save()

			elif itemType == "Scientific Equipment and Supplies":
				for c in category:
					if c.title == 'Equipment':
						equipmentexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
														  expenseType = "Cash Advance",
														  expenseName = typeofequipment,
														  expenseQuantity = equipmentquantity,
														  amountRequested = equipmentestimatedamount,
														  expenseDescription=equipmentdescription,
														  status="For Review", nowDate=datetime.date.today())
						equipmentexpense.save()

		accomodations = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
												   title='Accomodations')
		transportation = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
													title='Transportation')
		others = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
											title='Other Expense')
		equipment = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
											   title='Equipment')
		supplies = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
											  title='Supplies and Materials')
		training = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
											  title='Training')
		if milestone_list:
			context = {'accomodations': accomodations, 'transportation': transportation, 'others': others, 'equipment': equipment,
				   'supplies': supplies, 'training': training, "project" : project,
				   "category" : category, 'milestones': milestone_list[0], 'milestone':milestones}
		else:
			context = {'accomodations': accomodations, 'transportation': transportation, 'others': others,
					   'equipment': equipment,
					   'supplies': supplies, 'training': training, "project": project,
					   "category": category, 'milestone':milestones}
		return render(request, "sdrc/cashadvance.html", context)
	elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					itemType = request.POST.get('itemType')
					hotelname = request.POST.get('hotelname')
					hotelpax = request.POST.get('hotelpax')
					hotelplace = request.POST.get('hotelplace')
					hotelestimatedamount = request.POST.get('hotelestimatedamount')
					noofnights = request.POST.get('noofnights')
					hoteldescription = request.POST.get('hoteldescription')
					hotelcheckin = request.POST.get('hotelcheckin')

					flightlocation = request.POST.get('flightlocation')
					destinationname = request.POST.get('destinationname')
					flightpax = request.POST.get('flightpax')
					nooftimes = request.POST.get('nooftimes')
					flightestimatedamount = request.POST.get('flightestimatedamount')
					dateofflight = request.POST.get('dateofflight')
					flightdescription = request.POST.get('flightdescription')
					#
					# OTHERS
					nameofservice = request.POST.get('nameofservice')
					servicequantity = request.POST.get('servicequantity')
					labserviceestimatedamount = request.POST.get('labserviceestimatedamount')
					servicedescription = request.POST.get('servicedescription')
					#
					# OTHERS
					nameofsoftware = request.POST.get('nameofsoftware')
					softwarequantity = request.POST.get('softwarequantity')
					softwareestimatedamount = request.POST.get('softwareestimatedamount')
					softwaredescription = request.POST.get('softwaredescription')
					#
					# OTHERS
					nameofliterature = request.POST.get('nameofliterature')
					literaturequantity = request.POST.get('literaturequantity')
					literatureestimatedamount = request.POST.get('literatureestimatedamount')
					literaturedescription = request.POST.get('literaturedescription')
					#
					# OTHERS
					typeofdissemination = request.POST.get('typeofdissemination')
					disseminationquantity = request.POST.get('disseminationquantity')
					disseminationestimatedamount = request.POST.get('disseminationestimatedamount')
					disseminationdescription = request.POST.get('disseminationdescription')
					#
					# FIELDWORK
					typeoffieldexpense = request.POST.get('typeoffieldexpense')
					fieldexpensequantity = request.POST.get('fieldexpensequantity')
					fieldexpenseestimatedamount = request.POST.get('fieldexpenseestimatedamount')
					fieldexpensedescription = request.POST.get('hoteldescription')
					#
					# FIELDWORK
					typeofrepair = request.POST.get('typeofrepair')
					repairquantity = request.POST.get('repairquantity')
					repairestimatedamount = request.POST.get('repairestimatedamount')
					repairdescription = request.POST.get('repairdescription')
					#
					# OTHERS
					typeofequipment = request.POST.get('typeofequipment')
					equipmentquantity = request.POST.get('equipmentquantity')
					equipmentestimatedamount = request.POST.get('equipmentestimatedamount')
					equipmentdescription = request.POST.get('equipmentdescription')

					budgetcategory = request.POST.get('category')
					amount = request.POST.get('amount')
					expense = request.POST.get('expense')
					description = request.POST.get('description')
					project = p
					category = BudgetCategory.objects.filter(
						project=project)

					all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
					not_complete_milestone = []

					complete_milestone_with_tranche = 0
					for m in all_milestones:
						if m.get_finished_task() == 100:
							if m.trancheAmount:
								if m.trancheAmount != 0:
									complete_milestone_with_tranche += m.trancheAmount

									complet_tranche = Milestone.objects.get(id=m.id)
									complet_tranche.trancheAmount = 0
									complet_tranche.save(update_fields=['trancheAmount'])

						else:
							not_complete_milestone.append(m)
							milestones = not_complete_milestone[0]
					if milestones.trancheAmount:
						milestones.trancheAmount += complete_milestone_with_tranche
						milestones.save(update_fields=['trancheAmount'])
					# complete_milestone_with_tranche = 0

					milestone = Milestone.objects.filter(project=project).order_by('milestoneendDate')
					milestone_list = []

					for m in milestone:
						if m.get_finished_task():
							if m.get_finished_task() < 100 and m.milestoneendDate < datetime.date.today():
								milestone_list.append(m)

					if budgetcategory:
						request.session['category'] = budgetcategory
						request.session['amount'] = amount
						request.session['expense'] = expense
						request.session['description'] = description
						return HttpResponseRedirect('/budgetextensionform/')
					else:
						if itemType == "Hotel Booking":
							for c in category:
								if c.title == 'Accomodations':
									hotelexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																  expenseType="Cash Advance",
																  expenseName=hotelname,
																  expenseLocation=hotelplace,
																  expenseQuantity=hotelpax,
																  amountRequested=hotelestimatedamount,
																  expenseDescription=hoteldescription,
																  fromDate=hotelcheckin,
																  days=noofnights,
																  status="For Review", nowDate=datetime.date.today())
									hotelexpense.save()

						elif itemType == "Flight Tickets":
							for c in category:
								if c.title == 'Transportation':
									flightexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																   expenseType="Cash Advance",
																   expenseName=destinationname,
																   expenseLocation=flightlocation,
																   expenseQuantity=flightpax,
																   amountRequested=flightestimatedamount,
																   expenseDescription=flightdescription,
																   fromDate=dateofflight,
																   status="For Review", nowDate=datetime.date.today())
									flightexpense.save()


						elif itemType == "Field Expense (No Official Receipt)":
							for c in category:
								if c.title == 'Other Expense':
									fieldexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																  expenseType="Cash Advance",
																  expenseName=typeoffieldexpense,
																  expenseQuantity=fieldexpensequantity,
																  amountRequested=fieldexpenseestimatedamount,
																  expenseDescription=fieldexpensedescription,
																  status="For Review", nowDate=datetime.date.today())
									fieldexpense.save()

						elif itemType == "Field Expense (Repair and Maintenance of Equipment)":
							for c in category:
								if c.title == 'Other Expense':
									repairexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																   expenseType="Cash Advance",
																   expenseName=typeofrepair,
																   expenseQuantity=repairquantity,
																   amountRequested=repairestimatedamount,
																   expenseDescription=repairdescription,
																   status="For Review", nowDate=datetime.date.today())
									repairexpense.save()


						elif itemType == "Specialized Scientific/Laboratory Services":
							for c in category:
								if c.title == 'Equipment':
									serviceexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																	expenseType="Cash Advance",
																	expenseName=nameofservice,
																	expenseQuantity=servicequantity,
																	amountRequested=labserviceestimatedamount,
																	expenseDescription=servicedescription,
																	status="For Review", nowDate=datetime.date.today())
									serviceexpense.save()

						elif itemType == "Scientific Software and Databases":
							for c in category:
								if c.title == 'Supplies and Materials':
									softwareexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																	 expenseType="Cash Advance",
																	 expenseName=nameofsoftware,
																	 expenseQuantity=softwarequantity,
																	 amountRequested=softwareestimatedamount,
																	 expenseDescription=softwaredescription,
																	 status="For Review", nowDate=datetime.date.today())
									softwareexpense.save()

						elif itemType == "Scientific Literature":
							for c in category:
								if c.title == 'Supplies and Materials':
									literatureexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																	   expenseType="Cash Advance",
																	   expenseName=nameofliterature,
																	   expenseQuantity=literaturequantity,
																	   amountRequested=literatureestimatedamount,
																	   expenseDescription=literaturedescription,
																	   status="For Review",
																	   nowDate=datetime.date.today())
									literatureexpense.save()

						elif itemType == "Research Dissemination Expenses":
							for c in category:
								if c.title == 'Training':
									disseminationexpense = ProjectExpense(project=project, milestone=milestones, category=c,
																		  itemType=itemType,
																		  expenseType="Cash Advance",
																		  expenseName=typeofdissemination,
																		  expenseQuantity=disseminationquantity,
																		  amountRequested=disseminationestimatedamount,
																		  expenseDescription=disseminationdescription,
																		  status="For Review",
																		  nowDate=datetime.date.today())
									disseminationexpense.save()

						elif itemType == "Scientific Equipment and Supplies":
							for c in category:
								if c.title == 'Equipment':
									equipmentexpense = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType,
																	  expenseType="Cash Advance",
																	  expenseName=typeofequipment,
																	  expenseQuantity=equipmentquantity,
																	  amountRequested=equipmentestimatedamount,
																	  expenseDescription=equipmentdescription,
																	  status="For Review",
																	  nowDate=datetime.date.today())
									equipmentexpense.save()

					accomodations = BudgetCategory.objects.get(
						project=project,
						title='Accomodations')
					transportation = BudgetCategory.objects.get(
						project=project,
						title='Transportation')
					others = BudgetCategory.objects.get(
						project=project,
						title='Other Expense')
					equipment = BudgetCategory.objects.get(
						project=project,
						title='Equipment')
					supplies = BudgetCategory.objects.get(
						project=project,
						title='Supplies and Materials')
					training = BudgetCategory.objects.get(
						project=project,
						title='Training')
					if milestone_list:
						context = {'accomodations': accomodations, 'transportation': transportation, 'others': others,
							   'equipment': equipment,
							   'supplies': supplies, 'training': training, "project": project,
							   "category": category, 'milestones': milestone_list[0], 'milestone': milestones, 'notifications': get_notifications(request)}
					else:
						context = {'accomodations': accomodations, 'transportation': transportation, 'others': others,
								   'equipment': equipment,
								   'supplies': supplies, 'training': training, "project": project,
								   "category": category, 'milestone': milestones,  'notifications': get_notifications(request)}
					return render(request, "sdrc/cashadvance.html", context)


def cashadvance_admin(request):
	template_name = 'sdrc/cashadvance_admin.html'
	user = ()

	if request.user.is_staff:
		budget_extension = Project.objects.all()

		if request.method == 'POST':
			status = request.POST.get('status')
			if status == 'Approved':
				budgetID = request.POST.get('budgetID')
				projectID = request.POST.get('projectID')
				approvedAmount = request.POST.get('approvedAmount')
				remarks = request.POST.get('remarks')

				expense = ProjectExpense.objects.get(id=budgetID)
				expense.expenseAmount = approvedAmount
				expense.status = status
				expense.remarks = remarks
				expense.save()


			else:
				budgetID = request.POST.get('budgetID')
				projectID = request.POST.get('projectID')
				remarks = request.POST.get('remarks')

				expense = ProjectExpense.objects.get(id=budgetID)
				expense.status = status
				expense.remarks = remarks
				expense.save()

		context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
		return render(request, template_name, context)

	else:
		if request.user.profile.principal_investigator and request.user.profile.active_project:
			budget_extension = ProjectExpense.objects.filter(expenseType='Cash Advance', project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))

			if request.method == 'POST':
				projectID = request.POST.get('projectID')
				expenseID = request.POST.get('expenseID')
				expenseReceipt = request.FILES.get('expenseReceipt')
				expenseDate = request.POST.get('date')
				totalallocated = request.POST.get('totalallocated')
				budgetalloc = request.POST.get('allocatedleft')
				totalcost = request.POST.get('budgetspent')
				budget = request.POST.get('budgetremaining')
				expenseTotal = request.POST.get('expenseTotal')

				expense = ProjectExpense.objects.get(id=expenseID)
				expense.expenseTotal = expenseTotal
				expense.expenseReceipt = expenseReceipt
				expense.expenseDate = expenseDate
				expense.save(update_fields=['expenseTotal', 'expenseReceipt', 'expenseDate'])
				project = Project.objects.get(principalInvestigator=request.user.id)
				if project.hasTranche == True:
					milestone = Milestone.objects.get(id=expense.milestone.id)
					milestoneTranche = expense.milestone.trancheAmount - Decimal(expenseTotal)
					milestone.trancheAmount = milestoneTranche
					milestone.save(update_fields=['trancheAmount'])

				if expense.itemType == 'Hotel Booking':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Accomodations')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Flight Tickets':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Transportation')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Field Expense (No Official Receipt)':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Other Expense')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Field Expense (Repair and Maintenance of Equipment)':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Scientific Equipment and Supplies':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Specialized Scientific/Laboratory Services':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Scientific Software and Databases':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Supplies and Materials')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Scientific Literature':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Supplies and Materials')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if expense.itemType == 'Research Dissemination Expenses':
					category = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), title='Training')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])


			context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
			return render(request, template_name, context)

		elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			budget_extension = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					budget_extension = ProjectExpense.objects.filter(expenseType='Cash Advance', project=p)

					if request.method == 'POST':
						projectID = request.POST.get('projectID')
						expenseID = request.POST.get('expenseID')
						expenseReceipt = request.FILES.get('expenseReceipt')
						expenseDate = request.POST.get('date')
						totalallocated = request.POST.get('totalallocated')
						budgetalloc = request.POST.get('allocatedleft')
						totalcost = request.POST.get('budgetspent')
						budget = request.POST.get('budgetremaining')
						expenseTotal = request.POST.get('expenseTotal')

						expense = ProjectExpense.objects.get(id=expenseID)
						expense.expenseTotal = expenseTotal
						expense.expenseReceipt = expenseReceipt
						expense.expenseDate = expenseDate
						expense.save(update_fields=['expenseTotal', 'expenseReceipt', 'expenseDate'])
						project = p
						if project.hasTranche == True:
							milestone = Milestone.objects.get(id=expense.milestone.id)
							milestoneTranche = expense.milestone.trancheAmount - Decimal(expenseTotal)
							milestone.trancheAmount = milestoneTranche
							milestone.save(update_fields=['trancheAmount'])

						if expense.itemType == 'Hotel Booking':
							category = BudgetCategory.objects.get(
								project=p,
								title='Accomodations')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Flight Tickets':
							category = BudgetCategory.objects.get(
								project=p,
								title='Transportation')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Field Expense (No Official Receipt)':
							category = BudgetCategory.objects.get(
								project=p,
								title='Other Expense')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Field Expense (Repair and Maintenance of Equipment)':
							category = BudgetCategory.objects.get(
								project=p,
								title='Equipment')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Scientific Equipment and Supplies':
							category = BudgetCategory.objects.get(
								project=p,
								title='Equipment')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Specialized Scientific/Laboratory Services':
							category = BudgetCategory.objects.get(
								project=p,
								title='Equipment')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Scientific Software and Databases':
							category = BudgetCategory.objects.get(
								project=p,
								title='Supplies and Materials')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Scientific Literature':
							category = BudgetCategory.objects.get(
								project=p,
								title='Supplies and Materials')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = Project.objects.get(principalInvestigator=request.user.id)
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])
						if expense.itemType == 'Research Dissemination Expenses':
							category = BudgetCategory.objects.get(
								project=p,
								title='Training')
							category.subtotal = totalallocated
							category.save(update_fields=['subtotal'])
							project = p
							project.budgetSpent = totalcost
							project.budgetRemaining = budget
							project.save(update_fields=['budgetSpent', 'budgetRemaining'])

			context = {'budgetextension': budget_extension, 'notifications': get_notifications(request)}
			return render(request, template_name, context)


def request_reimbursement(request):
	template_name = 'sdrc/request_reimbursement.html'

	if request.user.profile.principal_investigator and request.user.profile.active_project:
		project= Project.objects.get(principalInvestigator=request.user.id)
		all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
		milestone = Milestone.objects.filter(project=project).order_by('milestoneendDate')
		milestone_list = []
		all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
		not_complete_milestone = []

		complete_milestone_with_tranche = 0
		for m in all_milestones:
			if m.get_finished_task() == 100:
				if m.trancheAmount:
					if m.trancheAmount != 0:
						complete_milestone_with_tranche += m.trancheAmount

						complet_tranche = Milestone.objects.get(id=m.id)
						complet_tranche.trancheAmount = 0
						complet_tranche.save(update_fields=['trancheAmount'])

			else:
				not_complete_milestone.append(m)
				milestones = not_complete_milestone[0]
		if milestones.trancheAmount:
			milestones.trancheAmount += complete_milestone_with_tranche
			milestones.save(update_fields=['trancheAmount'])
		# complete_milestone_with_tranche = 0

	elif not request.user.profile.principal_investigator and request.user.profile.active_project:
		project = []
		for pm in ProjectMember.objects.all():
			if pm.member == request.user:
				for p in Project.objects.all():
					if pm.project == p and not p.dateFinished:
						project.append(p)

		if project:
			for p in project:

				all_milestones = Milestone.objects.filter(project=p).order_by('milestonestartDate')
				milestone = Milestone.objects.filter(project=p).order_by('milestoneendDate')
				milestone_list = []
				all_milestones = Milestone.objects.filter(project=p).order_by('milestonestartDate')
				not_complete_milestone = []

				for am in all_milestones:
					print("ALL MILESTONE")
					print(am)
					if am.get_finished_task() == 100:
						print("ALL DONE")
						print(am)
					else:
						not_complete_milestone.append(am)
						milestones = not_complete_milestone[0]
						print("ALL NOT FINISIH TASK")
						print(milestones)

	if request.user.profile.principal_investigator and request.user.profile.active_project:
		category = BudgetCategory.objects.filter(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
		accomodations = BudgetCategory.objects.get(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
			title='Accomodations')
		transportation = BudgetCategory.objects.get(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
			title='Transportation')
		others = BudgetCategory.objects.get(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
			title='Other Expense')
		equipment = BudgetCategory.objects.get(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
			title='Equipment')
		supplies = BudgetCategory.objects.get(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
			title='Supplies and Materials')
		training = BudgetCategory.objects.get(
			project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
			title='Training')
		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)

		milestone = Milestone.objects.filter(project=project).order_by('milestoneendDate')
		milestone_list = []
		all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
		not_complete_milestone = []

		complete_milestone_with_tranche = 0
		for m in all_milestones:
			if m.get_finished_task() == 100:
				if m.trancheAmount:
					if m.trancheAmount != 0:
						complete_milestone_with_tranche += m.trancheAmount

						complet_tranche = Milestone.objects.get(id=m.id)
						complet_tranche.trancheAmount = 0
						complet_tranche.save(update_fields=['trancheAmount'])

			else:
				not_complete_milestone.append(m)
				milestones = not_complete_milestone[0]
		if milestones.trancheAmount:
			milestones.trancheAmount += complete_milestone_with_tranche
			milestones.save(update_fields=['trancheAmount'])
		# complete_milestone_with_tranche = 0

		for m in milestone:
			if m.get_finished_task():
				if m.get_finished_task() < 100 and m.milestoneendDate < datetime.date.today():
					milestone_list.append(m)


			if request.method == 'POST':
				if request.is_ajax():
					itemType = request.POST.get('itemType')
					project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)

					if itemType == 'Hotel Booking':
						for c in category:
							if c.title == 'Accomodations':
								expenseTotal = request.POST.get('hotelamount')
								expenseLocation = request.POST.get('hotellocation')
								days = request.POST.get('hoteldays')

								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType, currency=request.POST.get('currency'), expenseName=itemType,
														 expenseLocation=expenseLocation,
														 expenseQuantity=request.POST.get('hotelpax'),
														 expenseDescription=request.POST.get('hoteldescription'),
														 amountRequested=expenseTotal,
														 fromDate=request.POST.get('hotelcheckin'),
														 toDate=request.POST.get('hotelcheckout'),
														 expenseReceipt=request.POST.get('hotelreceipt'),
														 days=days, venue=request.POST.get('hotel'),
														 status='For Review', nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Flight Tickets':
						for c in category:
							if c.title == 'Transportation':
								expenseLocation = request.POST.get('location')
								expenseTotal = request.POST.get('amount')
								expenseQuantity = request.POST.get('pax')
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType, currency=request.POST.get('currency'),expenseName=itemType,
														 expenseLocation=expenseLocation,
														 expenseQuantity=expenseQuantity,
														 expenseAmount=request.POST.get('price'),
														 amountRequested=expenseTotal, fromDate=request.POST.get('departure'),
														 toDate=request.POST.get('arrival'),
														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'),
														 destination=request.POST.get('destination'),
														 times=request.POST.get('times'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Field Expense (No Official Receipt)':
						for c in category:
							if c.title == 'Other Expense':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType, currency=request.POST.get('currency'), expenseName=request.POST.get('expensename'),
														 amountRequested=request.POST.get('total'),
														 expenseDate=request.POST.get('date'),
														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Field Expense (Repair and Maintenance of Equipment)':
						for c in category:
							if c.title == 'Other Expense':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType, currency=request.POST.get('currency'), expenseName=request.POST.get('expensename'),
														 amountRequested=request.POST.get('total'),
														 expenseDate=request.POST.get('date'),
														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Scientific Equipment and Supplies':
						for c in category:
							if c.title == 'Equipment':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType,
														 currency=request.POST.get('currency'),
														 expenseName=request.POST.get('expenseName'),
														 expenseLocation=request.POST.get('location'),
														 expenseQuantity=request.POST.get('quantity'),
														 expenseAmount=request.POST.get('price'),
														 amountRequested=request.POST.get('amount'),
														 expenseDate=request.POST.get('date'),

														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Specialized Scientific/Laboratory Services':
						for c in category:
							if c.title == 'Equipment':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType,
														 currency=request.POST.get('currency'),
														 expenseName=request.POST.get('expenseName'),
														 expenseLocation=request.POST.get('location'),
														 expenseQuantity=request.POST.get('quantity'),
														 expenseAmount=request.POST.get('price'),
														 amountRequested=request.POST.get('amount'),
														 expenseDate=request.POST.get('date'),

														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Scientific Software and Databases':
						for c in category:
							if c.title == 'Supplies and Materials':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType,
														 currency=request.POST.get('currency'),
														 expenseName=request.POST.get('expenseName'),
														 expenseLocation=request.POST.get('location'),
														 expenseQuantity=request.POST.get('quantity'),
														 expenseAmount=request.POST.get('price'),
														 amountRequested=request.POST.get('amount'),
														 expenseDate=request.POST.get('date'),

														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Scientific Literature':
						for c in category:
							if c.title == 'Supplies and Materials':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType,
														 currency=request.POST.get('currency'),
														 expenseName=request.POST.get('expenseName'),
														 expenseLocation=request.POST.get('location'),
														 expenseQuantity=request.POST.get('quantity'),
														 expenseAmount=request.POST.get('price'),
														 expenseDescription=request.POST.get('description'),
														 amountRequested=request.POST.get('amount'),
														 expenseDate=request.POST.get('date'),

														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
					elif itemType == 'Research Dissemination Expenses':
						for c in category:
							if c.title == 'Training':
								expense = ProjectExpense(project=project, category=c, milestone=milestones, expenseType='Reimbursement',
														 itemType=itemType,
														 currency=request.POST.get('currency'),
														 expenseName=request.POST.get('expenseName'),
														 expenseLocation=request.POST.get('location'),
														 expenseQuantity=request.POST.get('quantity'),
														 expenseAmount=request.POST.get('price'),
														 amountRequested=request.POST.get('amount'),
														 expenseDate=request.POST.get('date'),

														 expenseDescription=request.POST.get('description'),
														 expenseReceipt=request.POST.get('receipt'), status='For Review',
														 nowDate=datetime.date.today())
								expense.save()
				else:
					budgetcategory = request.POST.get('category')
					amount = request.POST.get('amount')
					expense = request.POST.get('expense')
					description = request.POST.get('description')
					request.session['category'] = budgetcategory
					request.session['amount'] = amount
					request.session['expense'] = expense
					request.session['description'] = description
					return HttpResponseRedirect('/budgetextensionform/')

			if milestone_list:
				return render(request, template_name,
							  context={'category': category, 'accomodations': accomodations, 'transportation': transportation,
									   'others': others,
									   'equipment': equipment, 'supplies': supplies, 'training': training, 'project': project,
									   'notifications': get_notifications(request), 'milestone': milestone_list[0], 'milestones': milestones})
			else:
				return render(request, template_name, context={'category': category, 'accomodations': accomodations,
															   'transportation': transportation, 'others': others,
															   'equipment': equipment, 'supplies': supplies,
															   'training': training, 'project': project,
															   'notifications': get_notifications(request), 'milestones': milestones})

	elif not request.user.profile.principal_investigator and request.user.profile.active_project:
		project = []
		for pm in ProjectMember.objects.all():
			if pm.member == request.user:
				for p in Project.objects.all():
					if pm.project == p and not p.dateFinished:
						project.append(p)

		if project:
			for p in project:
				category = BudgetCategory.objects.filter(project=p)
				accomodations = BudgetCategory.objects.get(project=p, title='Accomodations')
				transportation = BudgetCategory.objects.get(project=p, title='Transportation')
				others = BudgetCategory.objects.get(project=p,
													title='Other Expense')
				equipment = BudgetCategory.objects.get(project=p,
													   title='Equipment')
				supplies = BudgetCategory.objects.get(project=p,
													  title='Supplies and Materials')
				training = BudgetCategory.objects.get(project=p,
													  title='Training')
				project = p
				milestone = Milestone.objects.filter(project=p).order_by('milestoneendDate')
				milestone_list = []
				print(project)

				for m in milestone:
					if m.get_finished_task():
						if m.get_finished_task() < 100 and m.milestoneendDate < datetime.date.today():
							milestone_list.append(m)

				all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
				not_complete_milestone = []

				for m in all_milestones:
					if m.get_finished_task() == 100:
						print("ALL FINISIH TASK")
						print(m.milestoneName)
					else:
						not_complete_milestone.append(m)
						milestones = not_complete_milestone[0]

				print(milestone_list)

				if request.method == 'POST':
					if request.is_ajax():
						itemType = request.POST.get('itemType')
						project = p

						if itemType == 'Hotel Booking':
							for c in category:
								if c.title == 'Accomodations':
									expenseTotal = request.POST.get('hotelamount')
									expenseLocation = request.POST.get('hotellocation')
									days = request.POST.get('hoteldays')

									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=itemType,
															 expenseLocation=expenseLocation,
															 expenseQuantity=request.POST.get('hotelpax'),
															 expenseDescription=request.POST.get('hoteldescription'),
															 amountRequested=expenseTotal,
															 currency=request.POST.get('currency'),
															 fromDate=request.POST.get('hotelcheckin'),
															 toDate=request.POST.get('hotelcheckout'),
															 expenseReceipt=request.POST.get('hotelreceipt'),
															 days=days, venue=request.POST.get('hotel'),
															 status='For Review', nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Flight Tickets':
							for c in category:
								if c.title == 'Transportation':
									expenseLocation = request.POST.get('location')
									expenseTotal = request.POST.get('amount')
									expenseQuantity = request.POST.get('pax')
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=itemType,
															 expenseLocation=expenseLocation,
															 expenseQuantity=expenseQuantity,
															 expenseAmount=request.POST.get('price'),
															 amountRequested=expenseTotal,
															 currency=request.POST.get('currency'),
															 fromDate=request.POST.get('departure'),
															 toDate=request.POST.get('arrival'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'),
															 destination=request.POST.get('destination'),
															 times=request.POST.get('times'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Field Expense (No Official Receipt)':
							for c in category:
								if c.title == 'Other Expense':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expensename'),
															 amountRequested=request.POST.get('total'),
															 expenseDate=request.POST.get('date'),
															 currency=request.POST.get('currency'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Field Expense (Repair and Maintenance of Equipment)':
							for c in category:
								if c.title == 'Other Expense':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expensename'),
															 amountRequested=request.POST.get('total'),
															 expenseDate=request.POST.get('date'),
															 currency=request.POST.get('currency'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Scientific Equipment and Supplies':
							for c in category:
								if c.title == 'Equipment':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expenseName'),
															 expenseLocation=request.POST.get('location'),
															 expenseQuantity=request.POST.get('quantity'),
															 expenseAmount=request.POST.get('price'),
															 currency=request.POST.get('currency'),
															 amountRequested=request.POST.get('amount'),
															 expenseDate=request.POST.get('date'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Specialized Scientific/Laboratory Services':
							for c in category:
								if c.title == 'Equipment':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expenseName'),
															 expenseLocation=request.POST.get('location'),
															 expenseQuantity=request.POST.get('quantity'),
															 expenseAmount=request.POST.get('price'),
															 amountRequested=request.POST.get('amount'),
															 expenseDate=request.POST.get('date'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Scientific Software and Databases':
							for c in category:
								if c.title == 'Supplies and Materials':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expenseName'),
															 expenseLocation=request.POST.get('location'),
															 expenseQuantity=request.POST.get('quantity'),
															 currency=request.POST.get('currency'),
															 expenseAmount=request.POST.get('price'),
															 amountRequested=request.POST.get('amount'),
															 expenseDate=request.POST.get('date'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Scientific Literature':
							for c in category:
								if c.title == 'Supplies and Materials':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expenseName'),
															 expenseLocation=request.POST.get('location'),
															 expenseQuantity=request.POST.get('quantity'),
															 expenseAmount=request.POST.get('price'),
															 currency=request.POST.get('currency'),
															 expenseDescription=request.POST.get('description'),
															 amountRequested=request.POST.get('amount'),
															 expenseDate=request.POST.get('date'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
						elif itemType == 'Research Dissemination Expenses':
							for c in category:
								if c.title == 'Training':
									expense = ProjectExpense(project=project, category=c, expenseType='Reimbursement',
															 itemType=itemType, expenseName=request.POST.get('expenseName'),
															 expenseLocation=request.POST.get('location'),
															 expenseQuantity=request.POST.get('quantity'),
															 expenseAmount=request.POST.get('price'),
															 amountRequested=request.POST.get('amount'),
															 expenseDate=request.POST.get('date'),
															 currency=request.POST.get('currency'),
															 expenseDescription=request.POST.get('description'),
															 expenseReceipt=request.POST.get('receipt'), status='For Review',
															 nowDate=datetime.date.today())
									expense.save()
					else:
						budgetcategory = request.POST.get('category')
						amount = request.POST.get('amount')
						expense = request.POST.get('expense')
						description = request.POST.get('description')
						request.session['category'] = budgetcategory
						request.session['amount'] = amount
						request.session['expense'] = expense
						request.session['description'] = description
						return HttpResponseRedirect('/budgetextensionform/')
				if milestone_list:
					return render(request, template_name,
								  context={'category': category, 'accomodations': accomodations, 'transportation': transportation,
										   'others': others,
										   'equipment': equipment, 'supplies': supplies, 'training': training, 'project': project,
										   'notifications': get_notifications(request),
										   'milestone': milestone_list[0], 'notifications': get_notifications(request), 'milestones': milestones})
				else:
					return render(request, template_name,
								  context={'category': category, 'accomodations': accomodations, 'transportation': transportation,
										   'others': others,
										   'equipment': equipment, 'supplies': supplies, 'training': training, 'project': project,
										   'notifications': get_notifications(request), 'milestones': milestones
										   })


def budget_plan_create(request):
	project = Project.objects.all()
	budget = []
	projectbudget = []

	for p in project:
		category = BudgetCategory.objects.filter(project=p).values('project', 'category').annotate(sum=Sum('allocatedAmount')).order_by('category')
		for c in category:
			budget.append(c)

	for p in project:
		projected = BudgetCategory.objects.filter(project=p).values('project').annotate(
			sum=Sum('allocatedAmount'))
		for pr in projected:
			projectbudget.append(pr)
	print(budget)

	if BudgetCategory:
		category = BudgetCategory.objects.all()
		zipped_data = zip(project, category)



	if request.method == 'POST':
		pid = request.POST.get("projectID")
		request.session['pid'] = pid
		return HttpResponseRedirect("/create-budget-plan/")

	context = {
		'projects': project,
		'budget': budget,
		'zipped_data': zipped_data,
		'categories':category,
		'projectbudget': projectbudget
	}


	return render(request, 'sdrc/view_budget_plan.html', context)

# PI REQUEST PROCUREMENT
def requestprocurement(request):
	if request.user.profile.principal_investigator and request.user.profile.active_project:
		itemType = request.POST.get("itemType")
		country = request.POST.get("hotelcountry")
		city = request.POST.get("hotelcity")
		if itemType == 'Hotel Booking':
			country = request.POST.get("hotelcountry")
			city = request.POST.get("hotelcity")
		elif itemType == 'Flight Ticket':
			country = request.POST.get("flightcountry")
			city = request.POST.get("flightcity")
		location = country
		if country and city:
			location = city + ", " + country
		fromDate = request.POST.get("fromDate")
		toDate = request.POST.get("toDate")
		hotelNights = request.POST.get("hotelNights")
		hotelPax = request.POST.get("hotelPax")
		hotelBudget = request.POST.get("hotelBudget")
		hotelTotal = request.POST.get("hotelTotal")
		hotelDescription = request.POST.get("hotelDescription")
		flightDeparture = request.POST.get("flightDeparture")
		flightArrival = request.POST.get("flightArrival")
		flightPax = request.POST.get("flightPax")
		flightBudget = request.POST.get("flightBudget")
		flightDescription = request.POST.get("flightDescription")
		serviceName = request.POST.get("serviceName")
		serviceDate = request.POST.get("serviceDate")
		serviceBudget = request.POST.get("serviceBudget")
		serviceDescription = request.POST.get("serviceDescription")
		equipmentName = request.POST.get("equipmentName")
		equipmentQty = request.POST.get("equipmentQty")
		equipmentBudget = request.POST.get("equipmentBudget")
		equipmentDate = request.POST.get("equipmentDate")
		equipTotal = request.POST.get("equipTotal")
		equipDescription = request.POST.get("equipDescription")

		project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
		milestone = Milestone.objects.filter(project=project).order_by('milestoneendDate')
		milestone_list = []

		for m in milestone:
			if m.get_finished_task():
				if m.get_finished_task() < 100 and m.milestoneendDate < datetime.date.today():
					milestone_list.append(m)

		category = BudgetCategory.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
		accomodations = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
												   title='Accomodations')
		transportation = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
													title='Transportation')
		equipment = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
											   title='Equipment')
		supplies = BudgetCategory.objects.get(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
											   title='Supplies and Materials')

		all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
		not_complete_milestone = []


		complete_milestone_with_tranche = 0
		for m in all_milestones:
			if m.get_finished_task() == 100:
				if m.trancheAmount:
					if m.trancheAmount != 0:
						complete_milestone_with_tranche += m.trancheAmount

						complet_tranche = Milestone.objects.get(id=m.id)
						complet_tranche.trancheAmount = 0
						complet_tranche.save(update_fields=['trancheAmount'])

			else:
				not_complete_milestone.append(m)
				milestones = not_complete_milestone[0]
		if milestones.trancheAmount:
			milestones.trancheAmount += complete_milestone_with_tranche
			milestones.save(update_fields=['trancheAmount'])
		# complete_milestone_with_tranche = 0

		if itemType == "Hotel Booking":
			for c in category:
				if c.title == 'Accomodations':
					request_hotel = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType, expenseName=itemType, expenseType='Procurement', expenseLocation=location, fromDate=fromDate, toDate=toDate, days=hotelNights, expenseQuantity=hotelPax, expenseAmount=hotelBudget, expenseDescription=hotelDescription, amountRequested=hotelTotal, status="For Review", nowDate=datetime.date.today())
					request_hotel.save()

		if itemType == "Flight Ticket":
			for c in category:
				if c.title == 'Transportation':
					request_flight = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType, expenseName=itemType, expenseType='Procurement', expenseLocation=location, fromDate=flightDeparture, toDate=flightArrival, expenseQuantity=flightPax, amountRequested=flightBudget, expenseDescription=flightDescription, status="For Review", nowDate=datetime.date.today())
					request_flight.save()

		if itemType == "Specialized Scientific/Laboratory Services":
			for c in category:
				if c.title == 'Equipment':
					request_service = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType, expenseName=serviceName, expenseType='Procurement',  fromDate=serviceDate, amountRequested=serviceBudget, expenseDescription=serviceDescription, status="For Review", nowDate=datetime.date.today())
					request_service.save()

		if itemType == "Equipment and Supplies":
			for c in category:
				if c.title == 'Equipment':
					request_equipment = ProjectExpense(project=project, milestone=milestones, category=c, itemType=itemType, expenseName=equipmentName, expenseType='Procurement', expenseLocation=location, fromDate=equipmentDate, expenseQuantity=equipmentQty, expenseAmount=equipmentBudget, amountRequested=equipTotal, expenseDescription=equipDescription, status="For Review", nowDate=datetime.date.today())
					request_equipment.save()
		if milestone_list:
			context = {
				"project": project,
				"accomodations": accomodations,
				"transportation": transportation,
				"equipment": equipment,
				"supplies": supplies,
				"milestone": milestone_list[0]
			}
		else:
			context = {
				"project": project,
				"accomodations": accomodations,
				"transportation": transportation,
				"equipment": equipment,
				"supplies": supplies,
				"milestones": milestones
			}
		return render(request, 'sdrc/requestprocurement.html', context)

	elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					itemType = request.POST.get("itemType")
					country = request.POST.get("hotelcountry")
					city = request.POST.get("hotelcity")
					if itemType == 'Hotel Booking':
						country = request.POST.get("hotelcountry")
						city = request.POST.get("hotelcity")
					elif itemType == 'Flight Ticket':
						country = request.POST.get("flightcountry")
						city = request.POST.get("flightcity")
					location = country
					if country and city:
						location = city + ", " + country
					fromDate = request.POST.get("fromDate")
					toDate = request.POST.get("toDate")
					hotelNights = request.POST.get("hotelNights")
					hotelPax = request.POST.get("hotelPax")
					hotelBudget = request.POST.get("hotelBudget")
					hotelTotal = request.POST.get("hotelTotal")
					hotelDescription = request.POST.get("hotelDescription")
					flightDeparture = request.POST.get("flightDeparture")
					flightArrival = request.POST.get("flightArrival")
					flightPax = request.POST.get("flightPax")
					flightBudget = request.POST.get("flightBudget")
					flightDescription = request.POST.get("flightDescription")
					serviceName = request.POST.get("serviceName")
					serviceDate = request.POST.get("serviceDate")
					serviceBudget = request.POST.get("serviceBudget")
					serviceDescription = request.POST.get("serviceDescription")
					equipmentName = request.POST.get("equipmentName")
					equipmentQty = request.POST.get("equipmentQty")
					equipmentBudget = request.POST.get("equipmentBudget")
					equipmentDate = request.POST.get("equipmentDate")
					equipTotal = request.POST.get("equipTotal")
					equipDescription = request.POST.get("equipDescription")

					project = p
					milestone = Milestone.objects.filter(project=project).order_by('milestoneendDate')
					milestone_list = []

					for m in milestone:
						if m.get_finished_task():
							if m.get_finished_task() < 100 and m.milestoneendDate < datetime.date.today():
								milestone_list.append(m)
					all_milestones = Milestone.objects.filter(project=project).order_by('milestonestartDate')
					not_complete_milestone = []

					complete_milestone_with_tranche = 0
					for m in all_milestones:
						if m.get_finished_task() == 100:
							if m.trancheAmount:
								if m.trancheAmount != 0:
									complete_milestone_with_tranche += m.trancheAmount

									complet_tranche = Milestone.objects.get(id=m.id)
									complet_tranche.trancheAmount = 0
									complet_tranche.save(update_fields=['trancheAmount'])

						else:
							not_complete_milestone.append(m)
							milestones = not_complete_milestone[0]
					if milestones.trancheAmount:
						milestones.trancheAmount += complete_milestone_with_tranche
						milestones.save(update_fields=['trancheAmount'])
					# complete_milestone_with_tranche = 0

					category = BudgetCategory.objects.filter(
						project=project)
					accomodations = BudgetCategory.objects.get(
						project=project,
						title='Accomodations')
					transportation = BudgetCategory.objects.get(
						project=project,
						title='Transportation')
					equipment = BudgetCategory.objects.get(
						project=project,
						title='Equipment')
					supplies = BudgetCategory.objects.get(
						project=project,
						title='Supplies and Materials')

					if itemType == "Hotel Booking":
						for c in category:
							if c.title == 'Accomodations':
								request_hotel = ProjectExpense(project=project, category=c, itemType=itemType, milestone=milestones,
															   expenseName=itemType, expenseType='Procurement',
															   expenseLocation=location, fromDate=fromDate,
															   toDate=toDate, days=hotelNights,
															   expenseQuantity=hotelPax, expenseAmount=hotelBudget,
															   expenseDescription=hotelDescription,
															   amountRequested=hotelTotal, status="For Review",
															   nowDate=datetime.date.today())
								request_hotel.save()

					if itemType == "Flight Ticket":
						for c in category:
							if c.title == 'Transportation':
								request_flight = ProjectExpense(project=project, category=c, itemType=itemType, milestone=milestones,
																expenseName=itemType, expenseType='Procurement',
																expenseLocation=location, fromDate=flightDeparture,
																toDate=flightArrival, expenseQuantity=flightPax,
																amountRequested=flightBudget,
																expenseDescription=flightDescription,
																status="For Review", nowDate=datetime.date.today())
								request_flight.save()

					if itemType == "Specialized Scientific/Laboratory Services":
						for c in category:
							if c.title == 'Equipment':
								request_service = ProjectExpense(project=project, category=c, itemType=itemType, milestone=milestones,
																 expenseName=serviceName, expenseType='Procurement',
																 fromDate=serviceDate, amountRequested=serviceBudget,
																 expenseDescription=serviceDescription,
																 status="For Review", nowDate=datetime.date.today())
								request_service.save()

					if itemType == "Equipment and Supplies":
						for c in category:
							if c.title == 'Equipment':
								request_equipment = ProjectExpense(project=project, category=c, itemType=itemType, milestone=milestones,
																   expenseName=equipmentName, expenseType='Procurement',
																   expenseLocation=location, fromDate=equipmentDate,
																   expenseQuantity=equipmentQty,
																   expenseAmount=equipmentBudget,
																   amountRequested=equipTotal,
																   expenseDescription=equipDescription,
																   status="For Review", nowDate=datetime.date.today())
								request_equipment.save()
					if milestone_list:
						context = {
							"project": project,
							"accomodations": accomodations,
							"transportation": transportation,
							"equipment": equipment,
							"supplies": supplies,
							'milestone': milestone_list[0],
							'milestones': milestones
						}
					else:
						context = {
							"project": project,
							"accomodations": accomodations,
							"transportation": transportation,
							"equipment": equipment,
							"supplies": supplies,
							'notifications': get_notifications(request),
							'milestones': milestones
						}
					return render(request, 'sdrc/requestprocurement.html', context)

# ADMIN PROCUREMENT REQUESTS
def requestprocurement_admin(request):
	if request.user.is_staff:
		projects = Project.objects.all()
		requests = ProjectExpense.objects.filter(expenseType='Procurement')
		if request.method == 'POST':
			status = request.POST.get('status')
			if status == 'Approved':
				budgetID = request.POST.get('budgetID')
				projectID = request.POST.get('projectID')
				approvedAmount = request.POST.get('approvedAmount')
				totalallocated = request.POST.get('totalallocated')
				remarks = request.POST.get('remarks')
				date = request.POST.get('date')
				itemType = request.POST.get('itemType')
				receipt = request.FILES.get('receipt')
				budgetalloc = request.POST.get('allocatedleft')
				totalcost = request.POST.get('budgetspent')
				budget = request.POST.get('budgetremaining')

				if itemType == 'Hotel Booking':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()

					project=Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])

					category = BudgetCategory.objects.get(project=projectID, title='Accomodations')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost

					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Flight Tickets':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					category = BudgetCategory.objects.get(project=projectID, title='Transportation')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Field Expense (No Official Receipt)':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					category = BudgetCategory.objects.get(project=projectID, title='Other Expense')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Field Expense (Repair and Maintenance of Equipment)':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])

					category = BudgetCategory.objects.get(project=projectID, title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Equipment and Supplies':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					expense.save()
					category = BudgetCategory.objects.get(project=projectID, title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Specialized Scientific/Laboratory Services':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					category = BudgetCategory.objects.get(project=projectID, title='Equipment')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Scientific Software and Databases':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					category = BudgetCategory.objects.get(project=projectID, title='Supplies and Materials')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Scientific Literature':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					category = BudgetCategory.objects.get(project=projectID, title='Supplies and Materials')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
				if itemType == 'Research Dissemination Expenses':
					expense = ProjectExpense.objects.get(id=budgetID)
					expense.expenseTotal = approvedAmount
					expense.status = status
					expense.remarks = remarks
					expense.expenseDate = date
					expense.expenseReceipt = receipt
					expense.save()
					project = Project.objects.get(id=projectID)
					if project.hasTranche == True:
						milestone = Milestone.objects.get(id=expense.milestone.id)
						milestoneTranche = expense.milestone.trancheAmount - Decimal(approvedAmount)
						milestone.trancheAmount = milestoneTranche
						milestone.save(update_fields=['trancheAmount'])
					category = BudgetCategory.objects.get(project=projectID, title='Training')
					category.subtotal = totalallocated
					category.save(update_fields=['subtotal'])
					project = Project.objects.get(id=projectID)
					project.budgetSpent = totalcost
					project.budgetRemaining = budget
					project.save(update_fields=['budgetSpent', 'budgetRemaining'])
			else:
				budgetID = request.POST.get('budgetID')
				projectID = request.POST.get('projectID')
				remarks = request.POST.get('remarks')

				expense = ProjectExpense.objects.get(id=budgetID)
				expense.status = status
				expense.remarks = remarks
				expense.save()
		context = {
			'projects': projects,
			'requests': requests,
			'notifications': get_notifications(request)
		}

		return render(request, 'sdrc/requestprocurement_admin.html', context)
	else:
		if request.user.profile.principal_investigator and request.user.profile.active_project:
			procurement = ProjectExpense.objects.filter(expenseType='Procurement',
													project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
		elif not request.user.profile.principal_investigator and request.user.profile.active_project:
			project = []
			for pm in ProjectMember.objects.all():
				if pm.member == request.user:
					for p in Project.objects.all():
						if pm.project == p and not p.dateFinished:
							project.append(p)

			if project:
				for p in project:
					procurement = ProjectExpense.objects.filter(expenseType='Procurement',
																project=p)


		context = {
			'procurement': procurement,
			'notifications': get_notifications(request)
		}

		return render(request, 'sdrc/requestprocurement_admin.html', context)

def request_budget_extension(request):
    template_name = 'sdrc/request_budget_extension.html'
    project= Project.objects.get(principalInvestigator=request.user.id)
    if request.method == "POST":
        amount = request.POST.get("amount")
        reason = request.POST.get("reason")
        BudgetExtension(project=project,amountRequested=amount,reason=reason, nowDate=datetime.date.today()).save()
    return render(request,template_name)

def view_budget_status(request):

	project = Project.objects.all()
	allcategories = []
	allmembers =[]
	allprocurement=[]
	allreimburse=[]
	allexpense=[]
	totalexpense=[]


	for p in project:
		categories = BudgetCategory.objects.filter(project=p)
		members = ProjectMember.objects.filter(project=p)
		expense = ProjectExpense.objects.filter(project=p)
		total = ProjectExpense.objects.filter(project=p).values('project','category','status').annotate(sum=Sum('expenseTotal')).order_by('category','status')


		for c in categories:
			allcategories.append(c)


		for m in members:
			allmembers.append(m)

		for e in expense:
			if e.expenseReceipt:
				allexpense.append(e)

		for te in total:
			totalexpense.append(te)
			print("ito mga expense: ")
			print(totalexpense)





	context={
		'projects':project,
		'categories':allcategories,
		'members':allmembers,
		'expenses':allexpense,
		'totalexpense':totalexpense
	}

	return render(request, 'sdrc/budgetstatus.html', context)

def create_budget(request):

	pid = request.session['pid']
	project = Project.objects.get(principalInvestigator=pid, dateFinished__isnull=True)
	category = BudgetCategory.objects.filter(project=project)


	if request.is_ajax():
		personnel_category= request.POST.get("personnel_id")
		travel_category = request.POST.get("travel_id")
		operating_category = request.POST.get("operating_id")

		if personnel_category == 'Personnel':
			personnel_titles = json.loads(request.POST['personnel_title'])
			personnel_quantities = json.loads(request.POST['personnel_quatity'])
			personnel_amounts = json.loads(request.POST['personnel_amount'])
			personnel_subtotals = json.loads(request.POST['personnel_subtotal'])
			personnel_allocated = request.POST.get("personnel_totalallocated")

			for pt in personnel_titles:
				pTitle = pt

			for pq in personnel_quantities:
				pQuantity = pq

			for pa in personnel_amounts:
				pAmount= pa

			for ps in personnel_subtotals:
				pSubtotal = ps

			budgetcategory=BudgetCategory(
				project=project,
				category=personnel_category,
				title=pTitle,
				quantity=pQuantity,
				amount=pAmount,
				subtotal=pSubtotal,
				allocatedAmount=pSubtotal,
			)
			budgetcategory.save()


		if travel_category == 'Travel and Survey Cost':
			travel_titles = json.loads(request.POST['travel_title'])
			travel_quantities = json.loads(request.POST['travel_quatity'])
			travel_amounts = json.loads(request.POST['travel_amount'])
			travel_subtotals = json.loads(request.POST['travel_subtotal'])
			travel_allocated = request.POST.get("travel_totalallocated")

			for tt in travel_titles:
				tTitle = tt

			for tq in travel_quantities:
				tQuantity = tq

			for ta in travel_amounts:
				tAmount= ta

			for ts in travel_subtotals:
				tSubtotal = ts

			budgetcategory=BudgetCategory(
				project=project,
				category=travel_category,
				title=tTitle,
				quantity=tQuantity,
				amount=tAmount,
				subtotal=tSubtotal,
				allocatedAmount=tSubtotal
			)
			budgetcategory.save()
			print(travel_titles)

		if operating_category == 'Operating Expense':
			operating_titles = json.loads(request.POST['operating_title'])
			operating_quantities = json.loads(request.POST['operating_quatity'])
			operating_amounts = json.loads(request.POST['operating_amount'])
			operating_subtotals = json.loads(request.POST['operating_subtotal'])
			operating_allocated = request.POST.get("operating_totalallocated")
			for ot in operating_titles:
				oTitle = ot

			for oq in operating_quantities:
				oQuantity = oq

			for oa in operating_amounts:
				oAmount= oa

			for os in operating_subtotals:
				oSubtotal = os

			budgetcategory=BudgetCategory(
				project=project,
				category=operating_category,
				title=oTitle,
				quantity=oQuantity,
				amount=oAmount,
				subtotal=oSubtotal,
				allocatedAmount=oSubtotal
			)
			budgetcategory.save()
			print(operating_titles)


	if category:
		dontload = request.POST.get('dontload')
		if dontload:
			projectID = request.POST.get('projectID')
			request.session['projectID'] = projectID
			return HttpResponseRedirect('/createmilestone/')



	total = BudgetCategory.objects.filter(project=project).values('project', 'category').annotate(
		sum=Sum('allocatedAmount'))
	totalprojected =  BudgetCategory.objects.filter(project=project).values('project').aggregate(
		sum=Sum('allocatedAmount'))

	context = {
		"projects": project,
		"categories": category,
		"total": total,
		"totalprojected": totalprojected,
		"pid": pid

	}

	return render(request, 'sdrc/budgetplan.html', context)

def change_password(request):
	template_name = 'sdrc/change_password.html'

	form = ChangePasswordForm()

	if request.method == 'POST':
		form = ChangePasswordForm(request.POST)
		if form.is_valid():
			password1 = form.cleaned_data.get('password1')
			password2 = form.cleaned_data.get('password2')

			if password1 == password2:
				user = User.objects.get(id=request.user.id)
				user.set_password(password1)
				user.save()
				messages.success(request, 'Password successfully changed!')
				return redirect('/login/')
			else:
				messages.warning(request, 'Passwords do not match!')
				return redirect('/change_password/')
		else:
			return render(request, 'sdrc/change_password.html')

	return render(request, template_name, context={'form': form})


class NotificationItem:
    LOW_BUDGET = "Budget is below 20%"
    PROJECT_NEARING_DEADLINE = "Projects Nearing Deadline"
    INCIDENT_REPORT = "Incident Report"
    RESOLVED_INCIDENT_REPORT = "Resolved Incident Report"
    ACCOMPLISHED_MILESTONE = "Accomplished Milestone"
    BUDGET_EXTENSION = "Budget Extension"
    NEW_BUDGET_EXTENSION = "New Budget Extension"
    COMPLETED_PROJECT = "Project Completed"
    NEW_PROJECT = "New Project"
    MILESTONE_NEARING_DEADLINE = "Milestone Nearing Deadline"
    TASK_NEARING_DEADLINE = "Task Nearing Deadline"
    MILESTONE_DELAYED = "Milestone Delayed"
    TASK_DELAYED = "Task Delayed"
    UPDATED_BUDGET_EXTENSION = "Budget Extension Update"
    REQUEST = "Request"
    REALLOCATION = "Reallocation"
    PROJECT_EXTENSION = "Project Extension"
    UNRESOLVED = "Unresolved Incident"

    def __init__(self, notification_type, date, highlight, message, url):
        self.notification_type = notification_type
        self.date = date
        self.highlight = highlight
        self.message = message
        self.url = url

    @property
    def css_class(self):
        return {
            self.LOW_BUDGET:"text-danger",
            self.NEW_PROJECT: "text-info",
            self.COMPLETED_PROJECT: "text-success",
            self.PROJECT_NEARING_DEADLINE: "text-warning",
            self.INCIDENT_REPORT: "text-warning",
            self.RESOLVED_INCIDENT_REPORT: "text-success",
            self.ACCOMPLISHED_MILESTONE: "text-success",
            self.BUDGET_EXTENSION: "text-primary",
            self.NEW_BUDGET_EXTENSION: "text-info",
            self.UPDATED_BUDGET_EXTENSION: "text-info",
            self.MILESTONE_NEARING_DEADLINE: "text-warning",
            self.TASK_NEARING_DEADLINE: "text-warning",
            self.MILESTONE_DELAYED: "text-danger",
            self.TASK_DELAYED: "text-danger",
            self.REQUEST: "text-primary",
            self.REALLOCATION: "text-primary",
            self.PROJECT_EXTENSION: "text-primary",
            self.UNRESOLVED: "text-danger"
        }[self.notification_type]


def get_notifications(request):
    notifications = []

    if request.user.is_staff:
        # Projects 30 days before deadline or pass the deadline
        projects_near_deadline = Project.objects.filter(
            endDate__lte=datetime.date.today() + datetime.timedelta(days=30)
        ).order_by('nowDate')
        projects = Project.objects.all()

        # Completed Project
        for project in projects:
            if project.task_set.all():
                if project.task_set.filter(taskStatus='Completed').count() == project.task_set.all().count():
                    message = f"project is completed"

                    notifications.append(NotificationItem(
                        notification_type=NotificationItem.COMPLETED_PROJECT,
                        date=project.nowDate,
                        highlight=project.projectTitle,
                        message=message,
                        url=""
                    ))
        reallocation = Reallocation.objects.all()

        for realloc in reallocation:
            notifications.append(NotificationItem(
                    notification_type=NotificationItem.REALLOCATION,
                    date=realloc.dateRequested,
                    highlight=project.projectTitle,
                    message='has a new request for reallocation',
                    url="/view_reallocation"
                ))

        for project in projects:
            if project.finalReport:
                message = f"project uploaded their final report"

                notifications.append(NotificationItem(
                    notification_type=NotificationItem.COMPLETED_PROJECT,
                    date=project.nowDate,
                    highlight=project.projectTitle,
                    message=message,
                    url=""
                ))

        for project in projects_near_deadline:
            if project.get_daysLeft() < 0:
                message = f"project is {abs(project.get_daysLeft())} days past the deadline"
            else:
                if project.get_daysLeft() <= 30:
                    message = f"project is {project.get_daysLeft()} days until the deadline"

            notifications.append(NotificationItem(
                notification_type=NotificationItem.PROJECT_NEARING_DEADLINE,
                date=project.nowDate,
                highlight=project.projectTitle,
                message=message,
                url="/view-projects/"
            ))

        # Incident Report
        for incident in IncidentReport.objects.filter(issueStatus=False).order_by("nowDate"):
            notifications.append(NotificationItem(
                notification_type=NotificationItem.INCIDENT_REPORT,
                date=incident.nowDate,
                highlight=incident.project,
                message="has an incident report",
                url="/incidentreport/"
            ))

        # Resolved Incident Report
        for resolved_incident in IncidentReport.objects.filter(issueStatus=True).order_by("nowDate"):
            notifications.append(NotificationItem(
                notification_type=NotificationItem.RESOLVED_INCIDENT_REPORT,
                date=resolved_incident.nowDate,
                highlight=resolved_incident.project,
                message="has resolved an incident",
                url="/incidentreport/"
            ))

        # Accomplished Milestones
        for milestone in Milestone.objects.filter(milestoneStatus=True).order_by('nowDate'):
            notifications.append(NotificationItem(
                notification_type=NotificationItem.ACCOMPLISHED_MILESTONE,
                date=milestone.nowDate,
                highlight=milestone.project,
                message="has finished a milestone",
                url=""
            ))

        budget_extensions = BudgetExtension.objects.all()

        if budget_extensions:
            # New Budget Extension
            for new_budget_extension in budget_extensions.filter(nowDate=datetime.date.today()).order_by('nowDate'):
                notifications.append(NotificationItem(
                    notification_type=NotificationItem.NEW_BUDGET_EXTENSION,
                    date=new_budget_extension.nowDate,
                    highlight=new_budget_extension.project,
                    message="has a new budget extension request",
                    url="/budgetextension/"
                ))

        project_extension = ProjectExtension.objects.all()

        if project_extension:
            for new_budget_extension in project_extension.filter(nowDate=datetime.date.today()).order_by('nowDate'):
                notifications.append(NotificationItem(
                    notification_type=NotificationItem.PROJECT_EXTENSION,
                    date=new_budget_extension.nowDate,
                    highlight=new_budget_extension.project,
                    message="has a new project extension request",
                    url="/view_projectextension/"
                ))

        #New Request for Reimbursement
        reimbursement = ProjectExpense.objects.all()

        for request in reimbursement.filter(expenseType='Reimbursement'):
            notifications.append(NotificationItem(
                notification_type=NotificationItem.REQUEST,
                date=request.nowDate,
                highlight=request.project,
                message="has a new request for reimbursement",
                url="/view_reimbursements/"
            ))

        for request in reimbursement.filter(expenseType='Cash Advance'):
            notifications.append(NotificationItem(
                notification_type=NotificationItem.REQUEST,
                date=request.nowDate,
                highlight=request.project,
                message="has a new request for cash advance",
                url="/view_cashadvance/"
            ))
        for request in reimbursement.filter(expenseType='Procurement'):
            notifications.append(NotificationItem(
                notification_type=NotificationItem.REQUEST,
                date=request.nowDate,
                highlight=request.project,
                message="has a new request for procurement",
                url="/view_procurement/"
            ))


        notifications.sort(key=lambda n: n.date, reverse=True)
        return notifications

    else:
        if request.user.profile.principal_investigator and request.user.profile.active_project:
            projects = Project.objects.filter(principalInvestigator=request.user.id, dateFinished__isnull=True)
            # Completed Project
            for project in projects:
                remaining = float(project.projectCost)*0.20
                if project.budgetRemaining <= remaining:
                    notifications.append(NotificationItem(
                        notification_type=NotificationItem.LOW_BUDGET,
                        date=project.nowDate,
                        highlight= "Remaining Budget of this project is "+ str(project.budgetRemaining) + ".",
                        message="You might want to request for budget extension",
                        url="/requestbudgetextension/"
                    ))
                if project.task_set.all():
                    if project.get_percentage_completed() == 100:
                        message = f"project is completed"

                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.COMPLETED_PROJECT,
                            date=project.nowDate,
                            highlight=project.projectTitle,
                            message=f"project is completed",
                            url="/milestonestatus/"
                        ))

                    reallocation = Reallocation.objects.filter(project=project)

                    for realloc in reallocation:
                        if realloc.status != 'Approve':
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.REALLOCATION,
                                date=realloc.dateRequested,
                                highlight='',
                                message=f"Your budget reallocation's status has been changed to: '" + realloc.status + "' with remarks of '" + realloc.remarks +'.',
                                url="/expensetracking/"
                            ))
                        elif realloc.status == 'Approve':
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.REALLOCATION,
                                date=realloc.dateRequested,
                                highlight=f"Your budget reallocation's status has been approved with the approved amount of: ",
                                message= realloc.amountReallocated,
                                url="/expensetracking/"
                            ))
                    budget_extensions = BudgetExtension.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
                    # Approved Budget Extension
                    if budget_extensions:
                        for approved_budget_extension in budget_extensions.filter(status="Approved").order_by('nowDate'):
                            print(approved_budget_extension)
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.NEW_BUDGET_EXTENSION,
                                date=approved_budget_extension.nowDate,
                                highlight="Your budget extension has been approved amounting to P ",
                                message= approved_budget_extension.approvedAmount,
                                url="/budgetextension/"
                            ))
                        for budget_extension in budget_extensions.filter(status="For Revisions").order_by('nowDate'):
                            if budget_extension.remarks:
                                notifications.append(NotificationItem(
                                    notification_type=NotificationItem.UPDATED_BUDGET_EXTENSION,
                                    date=budget_extension.nowDate,
                                    highlight="Remarks:",
                                    message=budget_extension.remarks,
                                    url="/budgetextension/"
                                ))
                        for budget_extension in budget_extensions.filter(status="Disapproved").order_by('nowDate'):
                            if budget_extension.remarks:
                                notifications.append(NotificationItem(
                                    notification_type=NotificationItem.UPDATED_BUDGET_EXTENSION,
                                    date=budget_extension.nowDate,
                                    highlight="Status: ",
                                    message=budget_extension.status + " Remarks: " + budget_extension.remarks,
                                    url="/budgetextension/"
                                ))


                tasks = Task.objects.filter(project=project)
                for task in tasks:
                    incidents = IncidentReport.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), nowDate__gte=Task.objects.get(id=task.id).taskendDate - datetime.timedelta(days=7), issueStatus=False)
                    for incident in incidents:
                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.UNRESOLVED,
                            date=incident.nowDate,
                            highlight=incident.issueEncountered,
                            message="still remains unresolved",
                            url="/incidentreport/"
                        ))

            milestones = Milestone.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
            for m in milestones:

                if m.get_daysLeft() <= 0:
                    notifications.append(NotificationItem(
                        notification_type=NotificationItem.MILESTONE_DELAYED,
                        date=m.nowDate,
                        highlight=m.milestoneName,
                        message=f"is {abs(m.get_daysLeft())} days past the deadline",
                        url=""
                    ))
                else:
                    if m.get_daysLeft() <= 7:
                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.MILESTONE_NEARING_DEADLINE,
                            date=m.nowDate,
                            highlight=m.milestoneName,
                            message=f"has only {abs(m.get_daysLeft())} days left before the deadline",
                            url=""
                        ))

            tasks = Task.objects.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)).order_by('nowDate')
            for t in tasks:

                if t.get_daysLeft() <= 0:
                    notifications.append(NotificationItem(
                        notification_type=NotificationItem.MILESTONE_DELAYED,
                        date=t.nowDate,
                        highlight=t.taskName,
                        message=f"is {abs(t.get_daysLeft())} days past the deadline",
                        url=""


                    ))
                else:
                    if t.get_daysLeft() <= 7:
                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.MILESTONE_NEARING_DEADLINE,
                            date=t.nowDate,
                            highlight=t.taskName,
                            message=f"has only {abs(t.get_daysLeft())} days left before the deadline",
                            url=""
                        ))

            project = Project.objects.filter(principalInvestigator=request.user.id, dateFinished__isnull=True)
            # New Project
            for p in project:
                if not p.milestone_set.all():
                    notifications.append(NotificationItem(
                        notification_type=NotificationItem.NEW_PROJECT,
                        date=p.nowDate,
                        highlight=p.projectTitle,
                        message=f"project has been assigned to you!",
                        url="/piindex/"
                    ))

            budget_extensions = BudgetExtension.objects.filter(
                project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True))
            for approved_budget_extension in budget_extensions.filter(status=True).order_by('nowDate'):
                print(approved_budget_extension)
                notifications.append(NotificationItem(
                    notification_type=NotificationItem.NEW_BUDGET_EXTENSION,
                    date=approved_budget_extension.nowDate,
                    highlight="test",
                    message="milestone has an approved budget extension request",
                    url=""

                ))

            projects_near_deadline = Project.objects.filter(principalInvestigator=request.user.id,
                                                            endDate__lte=datetime.date.today() + datetime.timedelta(days=30)
                                                            ).order_by('nowDate')

            for project in projects_near_deadline:
                if project.get_daysLeft() <= 0:
                    message = f"project is {abs(project.get_daysLeft())} days past the deadline"
                else:
                    if project.get_daysLeft() <= 30:
                        message = f"project has {project.get_daysLeft()} days left before the deadline"

                notifications.append(NotificationItem(
                    notification_type=NotificationItem.PROJECT_NEARING_DEADLINE,
                    date=project.nowDate,
                    highlight=project.projectTitle,
                    message=message,
                    url=""
                ))

            requests = ProjectExpense.objects.all()
            for req in requests.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True), expenseType='Reimbursement', status='Approved'):

                notifications.append(NotificationItem(
                    notification_type=NotificationItem.BUDGET_EXTENSION,
                    date=req.nowDate,
                    highlight="",
                    message='Your request for reimbursement has been approved',
                    url="/view_reimbursements/"
                ))

            for req in requests.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
                                       expenseType='Cash Advance', status='Approved'):
                notifications.append(NotificationItem(
                    notification_type=NotificationItem.BUDGET_EXTENSION,
                    date=req.nowDate,
                    highlight="",
                    message='Your request for cash advance has been approved',
                    url="/view_cashadvance/"
                ))

            for req in requests.filter(project=Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True),
                                       expenseType='Procurement', status='Approved'):
                notifications.append(NotificationItem(
                    notification_type=NotificationItem.BUDGET_EXTENSION,
                    date=req.nowDate,
                    highlight="",
                    message='Your request for procurement has been approved',
                    url="/view_procurement/"
                ))

            notifications.sort(key=lambda n: n.date, reverse=True)

            return notifications
        elif not request.user.profile.principal_investigator and request.user.profile.active_project:
            project_list = []
            for pm in ProjectMember.objects.all():
                if pm.member == request.user:
                    for p in Project.objects.all():
                        if pm.project == p and not p.dateFinished:
                            project_list.append(p)

            if project_list:
                for p in project_list:
                    projects = Project.objects.filter(id=p.id)
                    # Completed Project
                    for project in projects:
                        if project.task_set.all():
                            if project.get_percentage_completed() == 100:
                                message = f"project is completed"

                                notifications.append(NotificationItem(
                                    notification_type=NotificationItem.COMPLETED_PROJECT,
                                    date=project.nowDate,
                                    highlight=project.projectTitle,
                                    message=f"project is completed",
                                    url="/milestonestatus/"
                                ))

                            reallocation = Reallocation.objects.filter(project=project)

                            for realloc in reallocation:
                                if realloc.status != 'Approve':
                                    notifications.append(NotificationItem(
                                        notification_type=NotificationItem.REALLOCATION,
                                        date=realloc.dateRequested,
                                        highlight='',
                                        message=f"Your budget reallocation's status has been changed to: '" + realloc.status + "' with remarks of '" + realloc.remarks + '.',
                                        url="/expensetracking/"
                                    ))
                                elif realloc.status == 'Approve':
                                    notifications.append(NotificationItem(
                                        notification_type=NotificationItem.REALLOCATION,
                                        date=realloc.dateRequested,
                                        highlight=f"Your budget reallocation's status has been approved with the approved amount of: ",
                                        message=realloc.amountReallocated,
                                        url="/expensetracking/"
                                    ))
                            budget_extensions = BudgetExtension.objects.filter(
                                project=project)
                            # Approved Budget Extension
                            if budget_extensions:
                                for approved_budget_extension in budget_extensions.filter(status="Approved").order_by(
                                        'nowDate'):
                                    print(approved_budget_extension)
                                    notifications.append(NotificationItem(
                                        notification_type=NotificationItem.NEW_BUDGET_EXTENSION,
                                        date=approved_budget_extension.nowDate,
                                        highlight="Your budget extension has been approved amounting to P ",
                                        message=approved_budget_extension.approvedAmount,
                                        url="/budgetextension/"
                                    ))
                                for budget_extension in budget_extensions.filter(status="For Revisions").order_by(
                                        'nowDate'):
                                    if budget_extension.remarks:
                                        notifications.append(NotificationItem(
                                            notification_type=NotificationItem.UPDATED_BUDGET_EXTENSION,
                                            date=budget_extension.nowDate,
                                            highlight="Remarks:",
                                            message=budget_extension.remarks,
                                            url="/budgetextension/"
                                        ))
                                for budget_extension in budget_extensions.filter(status="Disapproved").order_by(
                                        'nowDate'):
                                    if budget_extension.remarks:
                                        notifications.append(NotificationItem(
                                            notification_type=NotificationItem.UPDATED_BUDGET_EXTENSION,
                                            date=budget_extension.nowDate,
                                            highlight="Status: ",
                                            message=budget_extension.status + " Remarks: " + budget_extension.remarks,
                                            url="/budgetextension/"
                                        ))

                        tasks = Task.objects.filter(project=project)
                        for task in tasks:
                            incidents = IncidentReport.objects.filter(
                                project=project,
                                nowDate__gte=Task.objects.get(id=task.id).taskendDate - datetime.timedelta(days=7),
                                issueStatus=False)
                            for incident in incidents:
                                notifications.append(NotificationItem(
                                    notification_type=NotificationItem.UNRESOLVED,
                                    date=incident.nowDate,
                                    highlight=incident.issueEncountered,
                                    message="still remains unresolved",
                                    url="/incidentreport/"
                                ))

                    milestones = Milestone.objects.filter(
                        project=project)
                    for m in milestones:

                        if m.get_daysLeft() <= 0:
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.MILESTONE_DELAYED,
                                date=m.nowDate,
                                highlight=m.milestoneName,
                                message=f"is {abs(m.get_daysLeft())} days past the deadline",
                                url=""
                            ))
                        else:
                            if m.get_daysLeft() <= 7:
                                notifications.append(NotificationItem(
                                    notification_type=NotificationItem.MILESTONE_NEARING_DEADLINE,
                                    date=m.nowDate,
                                    highlight=m.milestoneName,
                                    message=f"has only {abs(m.get_daysLeft())} days left before the deadline",
                                    url=""
                                ))

                    tasks = Task.objects.filter(project=project).order_by(
                        'nowDate')
                    for t in tasks:

                        if t.get_daysLeft() <= 0:
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.MILESTONE_DELAYED,
                                date=t.nowDate,
                                highlight=t.taskName,
                                message=f"is {abs(t.get_daysLeft())} days past the deadline",
                                url=""

                            ))
                        else:
                            if t.get_daysLeft() <= 7:
                                notifications.append(NotificationItem(
                                    notification_type=NotificationItem.MILESTONE_NEARING_DEADLINE,
                                    date=t.nowDate,
                                    highlight=t.taskName,
                                    message=f"has only {abs(t.get_daysLeft())} days left before the deadline",
                                    url=""
                                ))

                    project = Project.objects.filter(id=project.id)
                    # New Project
                    for p in project:
                        if not p.milestone_set.all():
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.NEW_PROJECT,
                                date=p.nowDate,
                                highlight=p.projectTitle,
                                message=f"project has been assigned to you!",
                                url="/piindex/"
                            ))

                        budget_extensions = BudgetExtension.objects.filter(
                            project=Project.objects.get(id=p.id), status=True).order_by('nowDate')
                        for approved_budget_extension in budget_extensions:
                            print(approved_budget_extension)
                            notifications.append(NotificationItem(
                                notification_type=NotificationItem.NEW_BUDGET_EXTENSION,
                                date=approved_budget_extension.nowDate,
                                highlight="test",
                                message="milestone has an approved budget extension request",
                                url=""

                            ))

                        projects_near_deadline = Project.objects.filter(id=p.id,
                                                                        endDate__lte=datetime.date.today() + datetime.timedelta(
                                                                            days=30)
                                                                        ).order_by('nowDate')

                    for project in projects_near_deadline:
                        if project.get_daysLeft() <= 0:
                            message = f"project is {abs(project.get_daysLeft())} days past the deadline"
                        else:
                            if project.get_daysLeft() <= 30:
                                message = f"project has {project.get_daysLeft()} days left before the deadline"

                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.PROJECT_NEARING_DEADLINE,
                            date=project.nowDate,
                            highlight=project.projectTitle,
                            message=message,
                            url=""
                        ))

                    requests = ProjectExpense.objects.all()
                    for req in requests.filter(project=p,
                                               expenseType='Reimbursement', status='Approved'):
                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.BUDGET_EXTENSION,
                            date=req.nowDate,
                            highlight="",
                            message='Your request for reimbursement has been approved',
                            url="/view_reimbursements/"
                        ))

                    for req in requests.filter(project=p,
                                               expenseType='Cash Advance', status='Approved'):
                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.BUDGET_EXTENSION,
                            date=req.nowDate,
                            highlight="",
                            message='Your request for cash advance has been approved',
                            url="/view_cashadvance/"
                        ))

                    for req in requests.filter(project=p,
                                               expenseType='Procurement', status='Approved'):
                        notifications.append(NotificationItem(
                            notification_type=NotificationItem.BUDGET_EXTENSION,
                            date=req.nowDate,
                            highlight="",
                            message='Your request for procurement has been approved',
                            url="/view_procurement/"
                        ))

                    notifications.sort(key=lambda n: n.date, reverse=True)

                    return notifications


def create_budget_plan(request):
	template_name = 'sdrc/create_budget_plan.html'
	project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
	personnelForm = PersonnelForm()
	fieldForm = FieldForm()
	travelForm = TravelForm()
	operatingForm = OperatingForm()
	otherForm = OthersForm()

	if request.method == 'POST':
		personnelForm = PersonnelForm(request.POST)
		if personnelForm.is_valid():
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
			title = request.POST.get("Expense_Title")
			budgetAllocated = request.POST.get("Personnel_Budget")
			budgetcategory = BudgetCategory(project=project, title=title, budgetAllocated=budgetAllocated)
			budgetcategory.save()


	if request.method == 'POST':
		fieldForm = FieldForm(request.POST)
		if fieldForm.is_valid():
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
			title = request.POST.get("Expense_Category")
			budgetAllocated = request.POST.get("Fieldwork_Budget")
			budgetcategory = BudgetCategory(project=project, title=title, budgetAllocated=budgetAllocated)
			budgetcategory.save()


	if request.method == 'POST':
		travelForm = TravelForm(request.POST)
		if travelForm.is_valid():
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
			title = request.POST.get("Category")
			budgetAllocated = request.POST.get("Travel_Budget")
			budgetcategory = BudgetCategory(project=project, title=title, budgetAllocated=budgetAllocated)
			budgetcategory.save()

	if request.method == 'POST':
		operatingForm = OperatingForm(request.POST)
		if operatingForm.is_valid():
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
			title = request.POST.get("Category_Title")
			budgetAllocated = request.POST.get("Operating_Budget")
			budgetcategory = BudgetCategory(project=project, title=title, budgetAllocated=budgetAllocated)
			budgetcategory.save()


	if request.method == 'POST':
		otherForm= OthersForm(request.POST)
		if otherForm.is_valid():
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
			title = request.POST.get("Category_Name")
			budgetAllocated = request.POST.get("Other_Budget")
			budgetcategory = BudgetCategory(project=project, title=title, budgetAllocated=budgetAllocated)
			budgetcategory.save()


		return HttpResponseRedirect('/create-expense-tracker/')

	context = {
		'pform':personnelForm,
		'fform':fieldForm,
		'tform':travelForm,
		'oform':operatingForm,
		'otherform':otherForm,
		'project':project
	}


	return render(request, template_name, context)

def create_expense_tracker(request):

	user = request.user.id
	project = Project.objects.get(principalInvestigator=user, dateFinished__isnull=True)
	category = BudgetCategory.objects.filter(project=project)
	expensePersonnels = ProjectExpense.objects.filter(project=Project.objects.get(principalInvestigator=user, dateFinished__isnull=True))

	if request.method == 'POST':
		budgetRemainingDiv = request.POST.get('budgetRemaining')
		totalExpense = request.POST.get('totalExpense')
		projectbudget = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)
		personnelAllocated = request.POST.get('personnelAlloc')
		fieldAllocated = request.POST.get('fieldAlloc')
		travelAllocated = request.POST.get('travelAlloc')
		operatingAllocated = request.POST.get('operatingAlloc')
		otherAllocated = request.POST.get('otherAlloc')

		personnelExpense = request.POST.get('personnelExpenseID')
		fieldExpense = request.POST.get('fieldExpenseID')
		travelExpense = request.POST.get('travelExpenseID')
		operatingExpense = request.POST.get('operatingExpenseID')
		otherExpense = request.POST.get('otherExpenseID')
		budgetAllocated = BudgetCategory.objects.filter(project=project)

		if budgetRemainingDiv:
			projectbudget.budgetRemaining = budgetRemainingDiv
			projectbudget.totalExpense = totalExpense
			projectbudget.save(update_fields=['budgetRemaining','totalExpense'])

		if personnelAllocated:
			for b in budgetAllocated:
				if (b.title == 'Personnel'):
					expenseName = request.POST.get('personnelSelect')
					if expenseName:
						b.budgetAllocated = personnelAllocated
						b.totalPersonnelExpense = personnelExpense
						b.save(update_fields=['budgetAllocated','totalPersonnelExpense'])
						print(expenseName)

		if fieldAllocated:
			for b in budgetAllocated:
				if (b.title == 'Fieldwork'):
					expenseName = request.POST.get('fieldSelect')
					if expenseName:
						b.budgetAllocated = fieldAllocated
						b.totalFieldExpense = fieldExpense
						b.save(update_fields=['budgetAllocated','totalFieldExpense'])
						print(expenseName)

		if travelAllocated:
			for b in budgetAllocated:
				if (b.title == 'Travel'):
					expenseName = request.POST.get('travelSelect')
					if expenseName:
						b.budgetAllocated = travelAllocated
						b.totalTravelExpense = travelExpense
						b.save(update_fields=['budgetAllocated', 'totalTravelExpense'])
						print(expenseName)

		if operatingAllocated:
			for b in budgetAllocated:
				if (b.title == 'Operating'):
					expenseName = request.POST.get('operatingSelect')
					if expenseName:
						b.budgetAllocated = operatingAllocated
						b.totalOperatingExpense = operatingExpense
						b.save(update_fields=['budgetAllocated', 'totalOperatingExpense'])
						print(expenseName)

		if otherAllocated:
			for b in budgetAllocated:
				if (b.title == 'Others'):
					expenseName = request.POST.get('otherNames')
					if expenseName:
						b.budgetAllocated = otherAllocated
						b.totalOtherExpense = otherExpense
						b.save(update_fields=['budgetAllocated', 'totalOtherExpense'])
						print(expenseName)


	for c in category:

		if (c.title == 'Personnel'):
			expenseName = request.POST.get('personnelSelect')
			personnelBudget = c.budgetAllocated
			pExpense = c.totalPersonnelExpense
			if expenseName:


				if request.is_ajax():

					expensePersonnel = ProjectExpense(
						project=project,
						category=c,
						expenseName=request.POST.get('personnelSelect'),
						expenseQuantity=request.POST.get('personnelQuantity'),
						expenseAmount=request.POST.get('personnelAmount'),
						expenseTotal=request.POST.get('personnelSubtotal'),
						expenseDate=request.POST.get('personnelDate'),
						expenseReceipt=request.POST.get('personnelReceipt'),


					)
					expensePersonnel.save()

		elif (c.title == 'Fieldwork'):
			expenseName = request.POST.get('fieldSelect')
			fieldBudget = c.budgetAllocated
			fExpense = c.totalFieldExpense
			if expenseName:
				if request.is_ajax():
					expenseField = ProjectExpense(
						project=project,
						category=c,
						expenseName=request.POST.get('fieldSelect'),
						expenseQuantity=request.POST.get('fieldQuantity'),
						expenseAmount=request.POST.get('fieldAmount'),
						expenseTotal=request.POST.get('fieldSubtotal'),
						expenseDate=request.POST.get('fieldDate'),
						expenseReceipt=request.POST.get('fieldReceipt'),

					)
					expenseField.save()

		elif (c.title == 'Travel'):
			expenseName = request.POST.get('travelSelect')
			travelBudget = c.budgetAllocated
			tExpense = c.totalTravelExpense
			if expenseName:
				if request.is_ajax():
					expenseTravel = ProjectExpense(
						project=project,
						category=c,
						expenseName=request.POST.get('travelSelect'),
						expenseQuantity=request.POST.get('travelQuantity'),
						expenseAmount=request.POST.get('travelAmount'),
						expenseTotal=request.POST.get('travelSubtotal'),
						expenseDate=request.POST.get('travelDate'),
						expenseReceipt=request.POST.get('travelReceipt'),
						destination = request.POST.get('traveldestination'),
						mode=request.POST.get('travelmode'),
						times=request.POST.get('traveltimes'),

						days = request.POST.get('travelDays'),
						venue=request.POST.get('travelVenue'),
					)
					expenseTravel.save()

		elif (c.title == 'Operating'):
			expenseName = request.POST.get('operatingSelect')
			operatingBudget = c.budgetAllocated
			oExpense = c.totalOperatingExpense
			if expenseName:
				if request.is_ajax():
					expenseOperating = ProjectExpense(
						project=project,
						category=c,
						expenseName=request.POST.get('operatingSelect'),
						expenseQuantity=request.POST.get('operatingQuantity'),
						expenseAmount=request.POST.get('operatingAmount'),
						expenseTotal=request.POST.get('operatingSubtotal'),
						expenseDate=request.POST.get('operatingDate'),
						expenseReceipt=request.POST.get('operatingReceipt'),


					)
					expenseOperating.save()

		elif (c.title == 'Others'):
			expenseName = request.POST.get('otherSelect')
			otherBudget = c.budgetAllocated
			otherExpense = c.totalOtherExpense
			if expenseName:
				if request.is_ajax():
					expenseOther = ProjectExpense(
						project=project,
						category=c,
						expenseName=request.POST.get('otherSelect'),
						expenseQuantity=request.POST.get('otherQuantity'),
						expenseAmount=request.POST.get('otherAmount'),
						expenseTotal=request.POST.get('otherSubtotal'),
						expenseDate=request.POST.get('otherDate'),
						expenseReceipt=request.POST.get('otherReceipt'),


					)
					expenseOther.save()

	form = BudgetExtensionForm()
	if request.method == 'POST':
		form = BudgetExtensionForm(request.POST)
		if form.is_valid():
			amountRequested = request.POST.get('amountRequested')
			reason = request.POST.get('reason')
			project = Project.objects.get(principalInvestigator=request.user.id, dateFinished__isnull=True)

			new_budget_extension = BudgetExtension(project=project, amountRequested=amountRequested, reason=reason, nowDate=datetime.date.today())
			new_budget_extension.save()
	context = {
		'project': project,
		'personnel': expensePersonnels,
		'category': category,
		'pBudget':personnelBudget,
		'fBudget':fieldBudget,
		'tBudget': travelBudget,
		'oBudget': operatingBudget,
		'otherBudget': otherBudget,
		'pExpense':pExpense,
		'fExpense': fExpense,
		'tExpense':tExpense,
		'oExpense':oExpense,
		'otherExpense': otherExpense,
		'form': form

	}

	template_name = 'sdrc/create_expense_tracker.html'

	return render(request, template_name,context)
