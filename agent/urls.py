from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.Home,name="home" ),
    path('query',views.Query,name='agent'),
    path('user',views.warehouse_query_view,name='user')
]