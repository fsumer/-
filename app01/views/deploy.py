from django.shortcuts import HttpResponse,render,redirect
from app01 import models



def deploy_task(request,task_id):
    task_obj = models.DeployTask.objects.filter(pk=task_id).first()
    return render(request,'deploy.html',locals())
