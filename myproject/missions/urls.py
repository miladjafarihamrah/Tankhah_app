"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import update_balance
from .views import update_profile
from .views import update_mission_factory
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('add_mission/', views.add_mission, name='add_mission'),
    path('delete_mission/<int:mission_id>/', views.delete_mission, name='delete_mission'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('generate_report/', views.generate_report, name='generate_report'),
    path('generate_pdf_report/', views.generate_pdf_report, name='generate_pdf_report'),
    path('delete_mission/', views.delete_mission, name='delete_mission'),
    path('edit_expense/', views.edit_expense, name='edit_expense'),
    path('delete_expense/', views.delete_expense, name='delete_expense'),
    path('edit_mission/', views.edit_mission, name='edit_mission'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('update-balance/', update_balance, name='update_balance'),
    path('update-profile/', update_profile, name='update_profile'),
    path('update_mission_factory/<int:mission_id>/', update_mission_factory, name='update_mission_factory'),
    path('edit_expense_details/', views.edit_expense_details, name='edit_expense_details'),
    path('hazineh_khodro/', views.hazineh_khodro, name='hazineh_khodro'),
    path('edit_khodro/', views.edit_khodro, name='edit_khodro'),
    path('delete_khodro/', views.delete_khodro, name='delete_khodro'),
    path('edit_khodro_details/', views.edit_khodro_details, name='edit_khodro_details'),
    path('tools/', views.tools, name='tools'),
    path('gold_price/', views.gold_price, name='gold_price'),
    path('select_software/', views.select_software, name='select_software'),
    path('device_manual/', views.device_manual, name='device_manual'),
]
