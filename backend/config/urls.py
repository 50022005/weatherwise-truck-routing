from django.urls import path,re_path
from routing.views import plan_view,health,index
urlpatterns=[path('api/plan/',plan_view),path('api/health/',health),re_path(r'^(?!api/).*$',index)]
