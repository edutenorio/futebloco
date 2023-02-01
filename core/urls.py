from django.urls import path

from .views import IndexView, GroupsView, SingleGroupView, SingleResultView, FixturesView, TeamsView, SingleTeamView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('groups/', GroupsView.as_view(), name='groups'),
    path('single-group/', SingleGroupView.as_view(), name='single-group'),
    path('single-reuslt/', SingleResultView.as_view(), name='single-result'),
    path('fixtures/', FixturesView.as_view(), name='fixtures'),
    path('teams/', TeamsView.as_view(), name='teams'),
    path('single-team', SingleTeamView.as_view(), name='single-team'),
]
