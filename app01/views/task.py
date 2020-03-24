from django.shortcuts import HttpResponse,render,redirect,reverse
from app01 import models
from app01.myforms.task import TaskModelForm
from django.http import JsonResponse

def task_list(request,project_id):
    # 根据项目id查询出所有的任务纪录
    taskList = models.DeployTask.objects.filter(project_id=project_id)
    project_obj = models.Project.objects.filter(pk=project_id).first()
    return render(request,'task_list.html',locals())


def task_add(request,project_id):
    form_obj = TaskModelForm(project_id)
    project_obj = models.Project.objects.filter(pk=project_id).first()
    if request.method == 'POST':
        form_obj = TaskModelForm(data=request.POST,project_obj=project_obj)
        if form_obj.is_valid():
            # 初步处理 自己手动加uid和project_id
            # print(form_obj.instance)  # 当前数据对象
            # form_obj.instance.uid = 'dsdjsdasdn'
            # form_obj.instance.project_id = project_id
            form_obj.save()
            _url = reverse('task_list',args=(project_id,))
            return redirect(_url)
    return render(request,'task_form.html',locals())


def hook_template(request,hook_id):
    hook_obj = models.HookTemplate.objects.filter(pk=hook_id).first()
    back_dic = {'status':1000,'content':''}
    back_dic['content'] = hook_obj.content
    return JsonResponse(back_dic)