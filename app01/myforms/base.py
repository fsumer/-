from django.forms import ModelForm


class BaseModelForm(ModelForm):
    # 将是否添加样式 做成可配置的
    exclude_bootstrap = []


    # 重写init方法  当你不知道一个方法是否有参数或者有几个参数的时候 建议你写*args,**kwargs
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 额外的操作
        # print(self.fields)  # 有序字典 OrderedDict([('hostname', <django.forms.fields.CharField object at 0x1092abf60>)])
        # 给所有的字段添加样式form-control
        for k, field in self.fields.items():
            # 判断当前字段是否需要加
            if k in self.exclude_bootstrap:
                # 直接跳过
                continue
            field.widget.attrs['class'] = 'form-control'