from django.views.generic import TemplateView, ListView
from django.db.models.aggregates import Count
import json
from json.encoder import JSONEncoder
from django.db.models.query import QuerySet
from django.core.serializers import serialize
from django.utils.functional import curry

from bilanci_project.territori.models import Territorio

class HomeView(TemplateView):
    template_name = "home.html"


class TerritorioListView(ListView):
    model = Territorio

    def get_queryset(self):
        territori = Territorio.objects.filter(tipo_territorio = "C",cod_comune__in=settings.COMUNI_CRATERE).\
            annotate(c = Count("progetto")).filter(c__gt=0).order_by("-cod_provincia").values_list('cod_comune',flat=True)
        if 'qterm' in self.request.GET:
            qterm = self.request.GET['qterm']
            return Territorio.objects.filter(denominazione__icontains=qterm,cod_comune__in=territori)[0:50]
        else:
            return  None


class DjangoJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            # `default` must return a python serializable
            # structure, the easiest way is to load the JSON
            # string produced by `serialize` and return it
            return json.loads(serialize('json', obj))
        return JSONEncoder.default(self,obj)
dumps = curry(json.dumps, cls=DjangoJSONEncoder)

class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(content,
            content_type='application/json',
            **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return dumps(context)


class TerritoriJSONListView(JSONResponseMixin, TerritorioListView):
    def convert_context_to_json(self, context):
        return dumps(context['territorio_list'])


