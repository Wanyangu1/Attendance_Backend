from django.urls import path
from .views import CheckInView, CheckOutView, TimeHistoryView, TodayStatusView, PauseView, ResumeView

urlpatterns = [
    path('checkin/', CheckInView.as_view(), name='checkin'),
    path('checkout/', CheckOutView.as_view(), name='checkout'),
    path('pause/', PauseView.as_view(), name='pause'),
    path('resume/', ResumeView.as_view(), name='resume'),
    path('history/', TimeHistoryView.as_view(), name='time-history'),
    path('today/', TodayStatusView.as_view(), name='today-status'),
]
