from django.urls import path

from .views import IndexView, SetSeasonView, GroupsView, SingleGroupView, SingleResultView, FixturesView, TeamsView, \
    SingleTeamView, CustomLoginView, CustomLogoutView, CustomSignupView, PersonDataView, CustomPasswordResetView, \
    CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView, SinglePlayerView, \
    MatchInputView, MatchEventAddView, MatchEventListVew, MatchEventUpdateView, MatchEventDeleteView, PlayersView, \
    ContactView, FixturesInputView, AwardsView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('set_season/', SetSeasonView.as_view(), name='set_season'),
    path('groups/', GroupsView.as_view(), name='groups'),
    path('single-group/', SingleGroupView.as_view(), name='single-group'),
    path('single-reuslt/', SingleResultView.as_view(), name='single-result'),
    path('fixtures/', FixturesView.as_view(), name='fixtures'),
    path('fixtures-input/', FixturesInputView.as_view(), name='fixtures-input'),
    path('teams/', TeamsView.as_view(), name='teams'),
    path('single-team/', SingleTeamView.as_view(), name='single-team'),
    path('players/', PlayersView.as_view(), name='players'),
    path('single-player/', SinglePlayerView.as_view(), name='single-player'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', CustomSignupView.as_view(), name='signup'),
    path('person-data/', PersonDataView.as_view(), name='person-data'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('match-input/', MatchInputView.as_view(), name='match-input'),
    path('match-event/', MatchEventListVew.as_view(), name='match-event'),
    path('match-event/<int:pk>/edit', MatchEventUpdateView.as_view(), name='match-event-update'),
    path('match-event/<int:pk>/delete', MatchEventDeleteView.as_view(), name='match-event-delete'),
    path('awards/', AwardsView.as_view(), name='awards'),
    path('contact/', ContactView.as_view(), name='contact'),
]
