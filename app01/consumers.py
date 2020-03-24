from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
import json
from asgiref.sync import async_to_sync
from app01 import models
import time
import threading
import subprocess
from app01.utils.ab_git import GitRepository
from app01.utils.ab_paramiko import SSHProxy
import shutil


def create_node(task_obj,task_id):
    # 判断当前任务是否已经创建过了图表数据
    node_object_list = models.Node.objects.filter(task_id=task_id)
    if node_object_list:
        return node_object_list
    if not node_object_list:
        node_object_list = []
        # 1 先创建节点
        start_node = models.Node.objects.create(text='开始', task_id=task_id)
        node_object_list.append(start_node)

        # 判断用户是否填写了下载前钩子
        if task_obj.before_download_script:
            # 有 则需要创建节点  利用变量名指向  将start_node由开始节点指向下载前钩子节点
            start_node = models.Node.objects.create(text='下载前', task_id=task_id, parent=start_node)
            node_object_list.append(start_node)

        download_node = models.Node.objects.create(text='下载', task_id=task_id, parent=start_node)
        node_object_list.append(download_node)

        # 同理 下载后节点创建也是如此
        # 判断用户是否填写了下载前钩子
        if task_obj.after_download_script:
            # 有 则需要创建节点  利用变量名指向  将start_node由开始节点指向下载前钩子节点
            download_node = models.Node.objects.create(text='下载后', task_id=task_id, parent=download_node)
            node_object_list.append(download_node)

        upload_node = models.Node.objects.create(text='上传', task_id=task_id, parent=download_node)
        node_object_list.append(upload_node)

        # 服务器节点需要考虑服务器的个数
        task_obj = models.DeployTask.objects.filter(pk=task_id).first()
        for server_obj in task_obj.project.servers.all():
            server_node = models.Node.objects.create(text=server_obj.hostname,
                                                     task_id=task_id,
                                                     parent=upload_node,
                                                     servers=server_obj
                                                     )
            node_object_list.append(server_node)

            # 判断发布前是否有钩子脚本
            if task_obj.before_deploy_script:
                server_node = models.Node.objects.create(text='发布前',
                                                         task_id=task_id,
                                                         parent=server_node,
                                                         servers=server_obj

                                                         )
                node_object_list.append(server_node)

            # 额外的再添加一个节点 发布节点
            deploy_node = models.Node.objects.create(text='发布',
                                                     task_id=task_id,
                                                     parent=server_node,
                                                     servers=server_obj
                                                     )
            node_object_list.append(deploy_node)

            # 同理
            if task_obj.after_deploy_script:
                after_deploy_node = models.Node.objects.create(text='发布后',
                                                               task_id=task_id,
                                                               parent=deploy_node,
                                                               servers=server_obj

                                                               )
                node_object_list.append(after_deploy_node)
        return node_object_list


def convert_object_to_js(node_object_list):
    # 构造gojs需要的节点数据
    node_list = []
    for node_object in node_object_list:
        temp = {
            'key': str(node_object.pk),
            'text': node_object.text,
            'color': node_object.status
        }
        # 判断当前节点对象是否有副节点 如果有则需要再添加一株简直对 parent
        if node_object.parent:
            temp['parent'] = str(node_object.parent_id)
        # 添加到列表中
        node_list.append(temp)  # [{},{},{}]
    return node_list


class PublishConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        self.accept()
        # 获取url中携带的无名或有名分组参数
        # self.scope看成一个大字典  这个字典里面有前端所有的信息 cookie session ...
        task_id = self.scope['url_route']['kwargs'].get('task_id')
        # task_id = self.scope['url_route']['args'].get('task_id')

        # 1 将当前用户加入群聊中
        async_to_sync(self.channel_layer.group_add)(task_id,self.channel_name)
        """
        括号内第一个参数是群号 必须是字符串格式
        第二个参数是用户的唯一标识
        """

        # 查询当前任务是否已经初始化节点数据 如果有直接返回给前端展示
        node_queryset = models.Node.objects.filter(task_id=task_id)

        if node_queryset:
            node_list = convert_object_to_js(node_queryset)
            # 发送数据给前端  这里是群发还是单独发送
            # 单发
            self.send(text_data=json.dumps({'code':'init','data':node_list}))

    def deploy(self,task_obj,task_id):
        # 执行流程
        # 1 开始 直接修改数据库中的节点数据并发送给前端
        start_node = models.Node.objects.filter(text='开始', task_id=task_id).first()
        start_node.status = 'green'
        start_node.save()
        # 立刻将数据返回给前端
        # 群发
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send',
                                                               'message': {'code': 'deploy', 'node_id': start_node.pk,
                                                                           'color': 'green'}})


        # 先通过代码的方式创建出所有的文件夹
        import os
        from django.conf import settings
        # 项目名
        project_name = task_obj.project.title
        # 唯一标示
        uid = task_obj.uid

        # 创建代码文件夹
        project_folder = os.path.join(settings.DEPLOY_CODE_PATH,project_name,uid,project_name)
        # 创建脚本文件夹
        script_folder= os.path.join(settings.DEPLOY_CODE_PATH,project_name,uid,'scripts')

        # 压缩文件存储路径
        package_folder = os.path.join(settings.PACKAGE_PATH,project_name,uid,project_name)

        # 判断上述文件夹是否存在 不存在应该动态创建
        if not os.path.exists(project_folder):
            # mkdir 该方法无法创建多层目录  makedirs可以
            os.makedirs(project_folder)

        if not os.path.exists(script_folder):
            os.makedirs(script_folder)


        if not os.path.exists(package_folder):
            os.makedirs(package_folder)

        # 2 下载前钩子脚本
        if task_obj.before_download_script:
            # TODO:执行钩子脚本内容
            """
            在发布机上执行钩子脚本内容
                1 先将用户填写的钩子脚本内容下载到本地
                2 执行 如果成功则绿色 否则红色
            """
            script_name = 'before_download_script.py'
            script_path = os.path.join(script_folder,script_name)
            # 写脚本文件
            with open(script_path,'w',encoding='utf-8') as f:
                f.write(task_obj.before_download_script)

            status = 'green'
            try:
                # 执行脚本文件
                """cmd:python /data/temp/a.py"""
                subprocess.check_output("python {0}".format(script_path),shell=True,cwd=script_folder)
                """
                先切换到cwd指定的目录下
                之后再执行前面的命令
                """
            except Exception as e:
                """一旦出现错误 后续所有的操作 都无需再进行了"""
                status = 'red'

            before_download_node = models.Node.objects.filter(text='下载前', task_id=task_id).first()
            before_download_node.status = status
            before_download_node.save()
            async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                                  'node_id': before_download_node.pk,
                                                                                                  'color': status}})
            if status == 'red':
                return

        # 3 下载
        # TODO:利用gitpython操作远程仓库
        # 模拟网络延迟
        # time.sleep(2)
        status = 'green'
        try:
            # gitpython相关代码
            GitRepository(project_folder,task_obj.project.repo,task_obj.tag)
        except Exception as e:
            status = 'red'
        download_node = models.Node.objects.filter(text='下载', task_id=task_id).first()
        download_node.status = status
        download_node.save()
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                              'node_id': download_node.pk,
                                                                                              'color': status}})
        if status == 'red':
            return


        # 4 下载后钩子脚本
        if task_obj.after_download_script:
            # TODO:执行钩子脚本内容
            script_name = 'after_download_script.py'
            script_path = os.path.join(script_folder, script_name)
            # 写脚本文件
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(task_obj.after_download_script)

            status = 'green'
            try:
                # 执行脚本文件
                """cmd:python /data/temp/a.py"""
                subprocess.check_output("python {0}".format(script_path), shell=True, cwd=script_folder)
                """
                先切换到cwd指定的目录下
                之后再执行前面的命令
                """
            except Exception as e:
                """一旦出现错误 后续所有的操作 都无需再进行了"""
                status = 'red'


            if status == 'red':
                return



            after_download_node = models.Node.objects.filter(text='下载后', task_id=task_id).first()
            after_download_node.status = 'green'
            after_download_node.save()
            async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                                  'node_id': after_download_node.pk,
                                                                                                  'color': 'green'}})

        # 5 上传
        upload_node = models.Node.objects.filter(text='上传', task_id=task_id).first()
        upload_node.status = 'green'
        upload_node.save()
        async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                              'node_id': upload_node.pk,
                                                                                              'color': 'green'}})

        # 6 链接服务器
        # TODO:paramiko模块
        for server_obj in task_obj.project.servers.all():
            # 6.1 上传代码
            # TODO:paramiko模块
            # 模拟延迟
            # time.sleep(2)
            status = 'green'
            try:
                """将代码文件和脚本文件压缩之后上传"""
                upload_folder_path = os.path.join(settings.DEPLOY_CODE_PATH,project_name,uid)
                # zip包压缩
                packag_path = shutil.make_archive(
                    base_name=os.path.join(package_folder,uid+'.zip'),
                    format='zip',  # zip tar
                    root_dir=upload_folder_path
                )
                # TODO:将文件发送到远程服务器 paramiko

            except Exception as e:
                status = 'red'

            server_node = models.Node.objects.filter(text=server_obj.hostname, task_id=task_id,
                                                     servers=server_obj).first()
            server_node.status = status
            server_node.save()
            async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                                  'node_id': server_node.pk,
                                                                                                  'color': status}})

            # 6.2 发布前钩子脚本
            # TODO:远程服务器上执行钩子脚本
            if task_obj.before_deploy_script:
                # TODO:执行钩子脚本内容
                """
                将脚本文件下载到本地  打包上蹿到服务器上 执行脚本文件
                /data/temp/
                """
                before_deploy_node = models.Node.objects.filter(text='发布前', task_id=task_id, servers=server_obj).first()
                before_deploy_node.status = 'green'
                before_deploy_node.save()
                async_to_sync(self.channel_layer.group_send)(task_id,
                                                             {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                             'node_id': before_deploy_node.pk,
                                                                                             'color': 'green'}})

            # 6.3  发布
            deploy_node = models.Node.objects.filter(text='发布', task_id=task_id,
                                                     servers=server_obj).first()
            deploy_node.status = 'green'
            deploy_node.save()
            async_to_sync(self.channel_layer.group_send)(task_id, {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                                  'node_id': deploy_node.pk,
                                                                                                  'color': 'green'}})

            # 6.4 发布后钩子脚本
            if task_obj.before_deploy_script:
                # TODO:执行钩子脚本内容
                """
                将脚本文件下载到本地  打包上蹿到服务器上 执行脚本文件

                
                """
                after_deploy_node = models.Node.objects.filter(text='发布后', task_id=task_id, servers=server_obj).first()
                after_deploy_node.status = 'green'
                after_deploy_node.save()
                async_to_sync(self.channel_layer.group_send)(task_id,
                                                             {'type': 'my.send', 'message': {'code': 'deploy',
                                                                                             'node_id': after_deploy_node.pk,
                                                                                             'color': 'green'}})


    def websocket_receive(self, message):
        text = message.get('text')
        task_id = self.scope['url_route']['kwargs'].get('task_id')
        task_obj = models.DeployTask.objects.filter(pk=task_id).first()

        # 初始化数据
        if text == 'init':
            # node_list = [
            #     {"key": "start", "text": '开始', "figure": 'Ellipse', "color": "lightgreen"},
            #     {"key": "download", "parent": 'start', "text": '下载代码', "color": "lightgreen", "link_text": '执行中...'},
            #     {"key": "compile", "parent": 'download', "text": '本地编译', "color": "lightgreen"},
            #     {"key": "compile", "parent": 'download', "text": '本地编译', "color": "lightgreen"},
            #     {"key": "compile", "parent": 'download', "text": '本地编译', "color": "lightgreen"},
            #
            # ]

            # 动态创建节点信息
            """
            1.先做基本的节点 不考虑钩子节点
            开始 下载 打包上传 服务器
            """
            # 1 调用create_node创建节点
            node_object_list = create_node(task_obj,task_id)

            # 2 调用convert...获取gojs所需数据
            node_list = convert_object_to_js(node_object_list)

            # 单独给当前链接对象发送数据
            # self.send(text_data=json.dumps({"code":'init','data':node_list}))
            # 给特定群号里面的用户发送数据
            async_to_sync(self.channel_layer.group_send)(task_id,{'type':'my.send','message':{"code":'init','data':node_list}})
            """
            type参数后指定的是发送数据的方法
            my.send     》》》  自定义一个my_send方法
            xxx.ooo     》》》  自定义一个xxx_ooo方法
            
            message参数后指定的是发送的数据
            
            将message后面的数据交给type指定的方法发送给用户
            """

        if text == 'deploy':
            # 调用执行  内部是单线程
            # self.deploy(task_obj,task_id)

            # 通用的解决方式  开设线程
            thread = threading.Thread(target=self.deploy,args=(task_obj,task_id))
            thread.start()




    def my_send(self,event):
        """发送数据功能
        async_to_sync会循环调用该方法 给群聊里面的每一个用户发送数据
        for obj in [obj1,obj2,obj3...]:
            obj.send()
        """
        # 获取message后面的数据
        message = event.get('message')
        self.send(json.dumps(message))



    def websocket_disconnect(self, message):
        # 当用户断开链接之后 应该剔除群聊
        task_id = self.scope['url_route']['kwargs'].get('task_id')
        # 去群里面将用户剔除
        async_to_sync(self.channel_layer.group_disacad)(task_id,self.channel_name)
        raise StopConsumer