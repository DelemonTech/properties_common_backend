"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from api.views import AgentListView
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views.agent_details_username import AgentDetailByUsernameView
from django.http import HttpResponse
from api.views.property_filter import FilterPropertiesView
from api.views.properties_list import PropertyListView
from api.views.property_details import PropertyDetailView
from api.views.cities_list import CityListView
from api.views.agent_register import AgentRegisterView
from api.views.agent_update import AgentUpdateView
from api.views.agent_delete import AgentDeleteView
from api.views.property_status_counts import PropertyStatusCountView
from api.views.property_city_count import PropertyByStatusView
from api.views.consultation import ConsultationView
from api.views.subscription import SubscribeView
from api.views.developers_list import DeveloperListView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from api.views.meta_view import agent_meta_view

schema_view = get_schema_view(
   openapi.Info(
      title="Offplan Agent API",
      default_version='v1',
      description="API documentation for agent listing and admin operations",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
   authentication_classes=[],
)

urlpatterns = [
    path('', lambda request: HttpResponse("🚀 Offplan Backend is running!")),
    # path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # path('agents/', AgentListView.as_view(), name='agent-list'),
    re_path(r'^(?P<username>[\w-]+)/$', agent_meta_view),

    # Swagger routes
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # path('agent/<str:username>/', AgentDetailByUsernameView.as_view(), name='agent-detail-by-username'),
    # path('', lambda request: HttpResponse("🚀 Offplan Backend is running!")),
    # path("properties/filter/", FilterPropertiesView.as_view(), name="property-filter"),
    # path("properties/", PropertyListView.as_view(), name="property-list"),
    # path("property/<int:id>/", PropertyDetailView.as_view(), name="property-detail"),
    # path("cities/", CityListView.as_view(), name="city-list"),
    # path('register/', AgentRegisterView.as_view(), name='register-agent'),
    # path('agent/update/<int:id>/', AgentUpdateView.as_view(), name='agent-update'),
    # path('agent/delete/<int:id>/', AgentDeleteView.as_view(), name='agent-delete'),
    # path('agents/list/', AgentListView.as_view(), name='agent-list'),
    # path('properties/status-counts/', PropertyStatusCountView.as_view(), name='property-status-counts'),
    # path('properties/city/count/', PropertyByStatusView.as_view(), name='property-city-wise-count'),
    # path('consultation',ConsultationView.as_view(),name='consultation_details'),
    # path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    # path('developers/', DeveloperListView.as_view(), name='developer-list'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)