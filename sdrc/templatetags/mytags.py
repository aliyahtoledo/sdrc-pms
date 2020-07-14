from sdrc.models import Task, Project

from django import template

register = template.Library()

@register.filter
def get_task_name(id):
    tasks = Task.objects.get(milestone=id) # get the object with given id, the id is passed from template.html through custom template tag
    return tasks.taskName # return the object's name

@register.filter
def get_task_assigned_to(id):
    tasks = Task.objects.get(milestone=id) # get the object with given id, the id is passed from template.html through custom template tag
    return tasks.assignedTo # return the object's name

@register.filter
def get_task_start_date(id):
    tasks = Task.objects.get(milestone=id) # get the object with given id, the id is passed from template.html through custom template tag
    return tasks.taskstartDate # return the object's name

@register.filter
def get_task_end_date(id):
    tasks = Task.objects.get(milestone=id) # get the object with given id, the id is passed from template.html through custom template tag
    return tasks.taskendDate # return the object's name

@register.filter(name='times')
def times(number):
    return range(number)

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg

@register.filter(name='abs')
def abs_filter(value):
    return abs(value)

@register.filter(name='divide')
def divide(value, arg):
    return value/arg * 100