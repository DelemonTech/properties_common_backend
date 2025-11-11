from rest_framework.routers import DefaultRouter
from django.urls import path, include
from api.views.agent_details_username import AgentDetailByUsernameView
from api.views.property_filter import FilterPropertiesView
from api.views.properties_list import PropertyListView, PropertyList50View
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
from api.views import AgentListView
from api.views.contact_enquiry import ContactEnquiryView
from api.views.reserve_now import ReserveNowView
from api.views.blogs import BlogPostDetail, BlogPostList
from api.views.agent_list_frontend import AgentListFrontendView


# router = DefaultRouter()
# router.register(r'admin/agents', AdminAgentDetailViewSet, basename='admin-agents')

urlpatterns = [
    # path('', include(router.urls)),
    path('agent/<str:username>/', AgentDetailByUsernameView.as_view(), name='agent-detail-by-username'),
    path("agents/frontend/", AgentListFrontendView.as_view(), name="agent-list-frontend"),
    path("properties/filter/", FilterPropertiesView.as_view(), name="property-filter"),
    path("properties/", PropertyListView.as_view(), name="property-list"),
    path("properties/large/", PropertyList50View.as_view(), name="property-list-50"),
    path("property/<int:id>/", PropertyDetailView.as_view(), name="property-detail"),
    path("cities/", CityListView.as_view(), name="city-list"),
    path('register/', AgentRegisterView.as_view(), name='register-agent'),
    path('agent/update/<int:id>/', AgentUpdateView.as_view(), name='agent-update'),
    path('agent/delete/<int:id>/', AgentDeleteView.as_view(), name='agent-delete'),
    path('agents/list/', AgentListView.as_view(), name='agent-list'),
    path('properties/status-counts/', PropertyStatusCountView.as_view(), name='property-status-counts'),
    path('properties/city/count/', PropertyByStatusView.as_view(), name='property-city-wise-count'),
    path('consultation', ConsultationView.as_view(), name='consultation_details'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('developers/', DeveloperListView.as_view(), name='developer-list'),
    path('contact/', ContactEnquiryView.as_view(), name='contact-enquiry'),
    path('reserve-now/<int:id>/',ReserveNowView.as_view(),name='reserve-now'),
    path('api/blogs/', BlogPostList.as_view()),
    path('api/blogs/<slug:slug>/', BlogPostDetail.as_view()),
]
