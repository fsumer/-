from app01 import models
from app01.myforms.base import BaseModelForm


class ProjectModelForm(BaseModelForm):
    class Meta:
        model = models.Project
        fields = "__all__"
