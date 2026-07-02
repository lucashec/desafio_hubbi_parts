from django.urls import path
from .views import ConsultorView, ConsultorHistoricoView

urlpatterns = [
    path("consultor/", ConsultorView.as_view(), name="consultor"),
    path("consultor/historico/", ConsultorHistoricoView.as_view(), name="consultor-historico"),
]
