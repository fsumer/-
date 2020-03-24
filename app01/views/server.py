# 服务器相关所有业务逻辑
from django.shortcuts import HttpResponse,render,redirect,reverse
from app01 import models
from django.http import JsonResponse
from app01.myforms.server import ServerModelForm




def server_list(request):
    # 将当前所有的服务器展示到前端页面
    serverList = models.Server.objects.all()
    # return render(request,'server_list.html',{'serverList':serverList})
    return render(request,'server_list.html',locals())


def server_add(request):
    # 先产生一个空的modelform对象
    form_obj = ServerModelForm()
    if request.method == 'POST':
        # 获取数据并校验
        form_obj = ServerModelForm(data=request.POST)
        # 判断数据是否合法
        if form_obj.is_valid():
            # 通过校验 操作数据库
            form_obj.save()  # 保存数据
            # 跳转到展示页
            return redirect('server_list')
            # redirect括号内可以直接写url 其实也可以写反向解析的别名 但是如果带有名无名分组的情况 则必须使用reverse
    # 将该对象传递给form页面
    return render(request,'form.html',locals())



def server_edit(request,edit_id):
    # 获取编辑对象 展示到页面给用户看 之后用户再编辑 提交
    edit_obj = models.Server.objects.filter(pk=edit_id).first()
    """
    其实编辑页面和添加页面是一样的 不同的在于是否需要渲染默认数据
    所以我们直接使用用一个页面
    """
    form_obj = ServerModelForm(instance=edit_obj)
    if request.method == 'POST':
        form_obj = ServerModelForm(data=request.POST,instance=edit_obj)
        if form_obj.is_valid():
            form_obj.save()  # 编辑
            # 新增和编辑都是save方法 区分就依据与instance参数
            return redirect('server_list')
    return render(request,'form.html',locals())


def server_delete(request,delete_id):
    models.Server.objects.filter(pk=delete_id).delete()
    return JsonResponse({'status':True})