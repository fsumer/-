# 项目相关所有业务逻辑
from django.shortcuts import HttpResponse,render,redirect,reverse
from app01 import models
from django.http import JsonResponse
from app01.myforms.project import ProjectModelForm




def project_list(request):
    # 将当前所有的服务器展示到前端页面
    projectList = models.Project.objects.all()
    # return render(request,'server_list.html',{'serverList':serverList})
    return render(request,'project_list.html',locals())


def project_add(request):
    # 先产生一个空的modelform对象
    form_obj = ProjectModelForm()
    if request.method == 'POST':
        # 获取数据并校验
        form_obj = ProjectModelForm(data=request.POST)
        # 判断数据是否合法
        if form_obj.is_valid():
            # 通过校验 操作数据库
            form_obj.save()  # 保存数据
            # 跳转到展示页
            return redirect('project_list')
            # redirect括号内可以直接写url 其实也可以写反向解析的别名 但是如果带有名无名分组的情况 则必须使用reverse
    # 将该对象传递给form页面
    return render(request,'form.html',locals())



def project_edit(request,edit_id):
    # 获取编辑对象 展示到页面给用户看 之后用户再编辑 提交
    edit_obj = models.Project.objects.filter(pk=edit_id).first()
    """
    其实编辑页面和添加页面是一样的 不同的在于是否需要渲染默认数据
    所以我们直接使用用一个页面
    """
    form_obj = ProjectModelForm(instance=edit_obj)
    if request.method == 'POST':
        form_obj = ProjectModelForm(data=request.POST,instance=edit_obj)
        if form_obj.is_valid():
            form_obj.save()  # 编辑
            # 新增和编辑都是save方法 区分就依据与instance参数
            return redirect('project_list')
    return render(request,'form.html',locals())


def project_delete(request,delete_id):
    models.Project.objects.filter(pk=delete_id).delete()
    return JsonResponse({'status':True})