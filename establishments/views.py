from django.http import HttpResponse
from django.views.generic import ListView
from establishments.models import City, Establishment
from django.shortcuts import render


class EstablishmentsList(ListView):
    model = City
    template_name = 'establishments/establishments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city_id = self.kwargs.get('city_id')
        if city_id is not None:
            default_city = City.objects.filter(id=city_id)[0] or City.objects.first()
        else:
            default_city = City.objects.first()
        context['default_city'] = default_city
        context['establishment_list'] = Establishment.objects.filter(city=default_city)
        return context


def delete_expired_session_data(request):
    """Очищает истекшие ключи сессии"""
    if request.is_ajax():
        # TODO очищать только, когда пользователь заходит первый раз в сессию на эту страницу
        request.session.flush()
        message = 'ok'
    else:
        message = 'error'
    return HttpResponse(message)


def about_page_view(request):
    return render(
        request,
        'establishments/about.html',
        {

        }
    )
