from django.forms import ModelForm
from territori.models import Territorio

class PaginaComuneAdminForm(ModelForm):

    """
    Overrides Form init to set only Comune in the territorio field
    """

    def __init__(self, *args, **kwargs):
        super(PaginaComuneAdminForm, self).__init__(*args, **kwargs)
        self.fields['territorio'].queryset = Territorio.objects.filter(territorio="C")
