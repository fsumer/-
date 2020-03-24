from app01.myforms.base import BaseModelForm
from app01 import models
import datetime
from django import forms

class TaskModelForm(BaseModelForm):

    # checkbox无需添加样式
    exclude_bootstrap = [
        'before_download_template',
        'after_download_template',
        'before_deploy_template',
        'after_deploy_template'

    ]
    # 自己定义新的字段
    # 下拉框 checkbox 文本框
    before_download_select = forms.ChoiceField(required=False, label='下载前')
    before_download_title = forms.CharField(required=False, label='模板名称')
    before_download_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label='是否保存为模板')

    after_download_select = forms.ChoiceField(required=False, label='下载后')
    after_download_title = forms.CharField(required=False, label='模板名称')
    after_download_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label='是否保存为模板')

    before_deploy_select = forms.ChoiceField(required=False, label='发布前')
    before_deploy_title = forms.CharField(required=False, label='模板名称')
    before_deploy_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label='是否保存为模板')

    after_deploy_select = forms.ChoiceField(required=False, label='下载后')
    after_deploy_title = forms.CharField(required=False, label='模板名称')
    after_deploy_template = forms.BooleanField(required=False, widget=forms.CheckboxInput, label='是否保存为模板')



    class Meta:
        model = models.DeployTask
        fields = '__all__'
        # 项目唯一标识 应该是自动生成的无需用户填写
        # 项目由于已经带了主键值了 所以也无需用户填写
        # 创建的任务单默认状态就是待发布 所以也无需展示
        exclude = ['uid','project','status']


    def __init__(self,project_obj,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.project_obj = project_obj
        # 初始化选择框内容
        self.init_hook()

    def init_hook(self):
        # 给所有的下拉框先添加一个 请选择选项
        # <option value="0">请选择</option>  (0,'请选择')

        before_download = [(0,'请选择')]
        # 还应该去数据库中查询是否有对应的模版名称
        extra_list = models.HookTemplate.objects.filter(hook_type=2).values_list('pk','title')
        before_download.extend(extra_list)
        self.fields['before_download_select'].choices = before_download

        after_download = [(0,'请选择')]
        extra_list = models.HookTemplate.objects.filter(hook_type=4).values_list('pk', 'title')
        after_download.extend(extra_list)
        self.fields['after_download_select'].choices = after_download

        before_deploy = [(0,'请选择')]
        extra_list = models.HookTemplate.objects.filter(hook_type=6).values_list('pk', 'title')
        before_deploy.extend(extra_list)
        self.fields['before_deploy_select'].choices = before_deploy

        after_deploy = [(0,'请选择')]
        extra_list = models.HookTemplate.objects.filter(hook_type=8).values_list('pk', 'title')
        after_deploy.extend(extra_list)
        self.fields['after_deploy_select'].choices = after_deploy

    def create_uid(self):
        # luffycity-test-v1-20201111111
        title = self.project_obj.title
        env = self.project_obj.env
        # 版本号 需要获取用户输入
        tag = self.cleaned_data.get('tag')
        date_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        return '{0}-{1}-{2}-{3}'.format(title,env,tag,date_time)

    def save(self, commit=True):
        # 添加数据
        self.instance.uid = self.create_uid()
        self.instance.project_id = self.project_obj.pk
        # 调用父类的save方法保存数据
        super().save(commit=True)

        # 判断用户是否点击checkbox
        if self.cleaned_data.get("before_download_template"):
            # 获取模版名称
            title = self.cleaned_data.get("before_download_title")
            # 获取脚本内容
            content = self.cleaned_data.get("before_download_script")
            # 保存到表中
            models.HookTemplate.objects.create(
                title=title,
                content=content,
                hook_type=2
            )

        if self.cleaned_data.get("after_download_template"):
            # 获取模版名称
            title = self.cleaned_data.get("after_download_title")
            # 获取脚本内容
            content = self.cleaned_data.get("after_download_script")
            # 保存到表中
            models.HookTemplate.objects.create(
                title=title,
                content=content,
                hook_type=4
            )

        if self.cleaned_data.get("before_deploy_template"):
            # 获取模版名称
            title = self.cleaned_data.get("before_deploy_title")
            # 获取脚本内容
            content = self.cleaned_data.get("before_deploy_script")
            # 保存到表中
            models.HookTemplate.objects.create(
                title=title,
                content=content,
                hook_type=6
            )

        if self.cleaned_data.get("after_deploy_template"):
            # 获取模版名称
            title = self.cleaned_data.get("after_deploy_title")
            # 获取脚本内容
            content = self.cleaned_data.get("after_deploy_script")
            # 保存到表中
            models.HookTemplate.objects.create(
                title=title,
                content=content,
                hook_type=8
            )

    # 全局钩子校验用户是否点击checkbox
    def clean(self):
        if self.cleaned_data.get('before_download_template'):
            # 获取用户输入的模版名称 判断是否有值
            title = self.cleaned_data.get("before_download_title")
            if not title:
                # 展示提示信息
                self.add_error('before_download_title','请输入模版名称')

        if self.cleaned_data.get('after_download_template'):
            # 获取用户输入的模版名称 判断是否有值
            title = self.cleaned_data.get("after_download_title")
            if not title:
                # 展示提示信息
                self.add_error('after_download_title','请输入模版名称')

        if self.cleaned_data.get('before_deploy_template'):
            # 获取用户输入的模版名称 判断是否有值
            title = self.cleaned_data.get("before_deploy_title")
            if not title:
                # 展示提示信息
                self.add_error('before_deploy_title','请输入模版名称')

        if self.cleaned_data.get('after_deploy_template'):
            # 获取用户输入的模版名称 判断是否有值
            title = self.cleaned_data.get("after_deploy_title")
            if not title:
                # 展示提示信息
                self.add_error('after_deploy_title','请输入模版名称')