from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GoalViewSet, DailyProgressViewSet, TrialViewSet  # include TrialViewSet

router = DefaultRouter()
router.register(r'goals', GoalViewSet)
router.register(r'progress', DailyProgressViewSet)
router.register(r'trials', TrialViewSet)  # register the trial route

urlpatterns = [
    path('', include(router.urls)),
]
