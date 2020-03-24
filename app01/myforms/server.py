from app01 import models
from app01.myforms.base import BaseModelForm


class ServerModelForm(BaseModelForm):
    class Meta:
        model = models.Server
        fields = "__all__"
