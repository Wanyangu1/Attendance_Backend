from django.urls import path
from .views import UserSettingsDetail, UserSettingsCreate

urlpatterns = [
    path('settings/', UserSettingsDetail.as_view(), name='user-settings'),
    path('settings/create/', UserSettingsCreate.as_view(), name='create-settings'),
]
