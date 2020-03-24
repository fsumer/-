from django.db import models

# Create your models here.


class Server(models.Model):
    """服务器表"""
    hostname = models.CharField(verbose_name='主机名',max_length=32)


    def __str__(self):
        return self.hostname


class Project(models.Model):
    """项目表"""
    # luffycity  cmdb crm ...
    title = models.CharField(verbose_name='项目名',max_length=32)

    # https://www.github.com/xxx.git/
    repo = models.CharField(verbose_name='仓库地址',max_length=64)

    env_choices = (
        ('prod','正式'),
        ('test','测试'),
    )
    env = models.CharField(verbose_name='环境',max_length=16,choices=env_choices,default='test')

    # /data/temp/...
    path = models.CharField(verbose_name='线上项目地址',max_length=32)
    # 项目跑在服务器上  那么项目和服务器应该是有关系的

    """
    一个项目可以是否可以跑在多台服务器上   可以!
    一台服务器上是否可以跑多个项目呢      当资金不是很充足的时候 服务器是可以混用的 可以！
    """
    servers = models.ManyToManyField(verbose_name='关联服务器',to='Server')

    def __str__(self):
        return '%s-%s'%(self.title,self.get_env_display())


class DeployTask(models.Model):
    """发布任务单
    项目主键            项目版本
    1                      v1
    1                      v2
    1                      v3
    2                      v1
    """
    # luffycity-test-v1-20201111111
    """项目名-环境-版本-日期"""
    uid = models.CharField(verbose_name='标识',max_length=32)

    # 任务与项目是一对多的关系  并且任务是多 项目是一
    project = models.ForeignKey(verbose_name='项目',to='Project')

    tag = models.CharField(verbose_name='版本',max_length=32)

    status_choices = (
        (1,'待发布'),
        (2,'发布中'),
        (3,'成功'),
        (4,'失败'),
    )
    status = models.IntegerField(verbose_name='状态',choices=status_choices,default=1)

    """预留了一些钩子功能"""
    before_download_script = models.TextField(verbose_name='下载前脚本', null=True, blank=True)
    after_download_script = models.TextField(verbose_name='下载后脚本', null=True, blank=True)
    before_deploy_script = models.TextField(verbose_name='发布前脚本', null=True, blank=True)
    after_deploy_script = models.TextField(verbose_name='发布后脚本', null=True, blank=True)


class HookTemplate(models.Model):
    """保存钩子脚本"""
    title = models.CharField(verbose_name='标题',max_length=32)
    content = models.TextField(verbose_name='脚本内容')
    # 我想实现钩子与钩子之间模版互不影响
    hook_type_choices = (
        (2,'下载前'),
        (4,'下载后'),
        (6,'发布前'),
        (8,'发布后')
    )
    hook_type = models.IntegerField(verbose_name='钩子类型',choices=hook_type_choices)


class Node(models.Model):
    # 一个任务单有多个节点
    task = models.ForeignKey(verbose_name='发布任务单',to='DeployTask')

    text = models.CharField(verbose_name='节点文字',max_length=32)

    # 节点颜色 初始化颜色 成功之后的颜色  失败之后的颜色
    status_choices = [
        ('lightgray','待发布'),
        ('green','成功'),
        ('red','失败'),
    ]
    status = models.CharField(verbose_name='状态',max_length=32,choices=status_choices,default='lightgray')

    # 自关联  根节点 子节点
    parent = models.ForeignKey(verbose_name='父节点',to='self',null=True,blank=True)

    # 节点与服务器 一对多
    servers = models.ForeignKey(to='Server',verbose_name='服务器',null=True,blank=True)



