from datetime import datetime, timezone

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group as UserGroup
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, \
    PasswordResetConfirmView, PasswordResetCompleteView
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.http import JsonResponse, QueryDict
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import activate, get_language
from django.views.generic import FormView, ListView, UpdateView, DeleteView
from django.views.generic.base import TemplateView, View
from django.utils.translation import gettext as _

from futebloco.settings import LANGUAGE_CODE, TIME_ZONE
from .forms import PersonForm, CustomUserCreationForm, CustomPasswordResetForm, CustomSetPasswordForm, MatchEventForm, \
    ContactForm
from .models import Tournament, Group, Match, Season, MatchEvent, Team, TeamTournamentRegistration, \
    PlayerTournamentRegistration, Person, MatchEventType, Genre
from .gmaplink import gmaplink
import pytz
from icecream import ic


def try_int(x):
    try:
        return int(x)
    except ValueError:
        return 1000000


class SetSeasonView(View):
    @staticmethod
    def get(request):
        season_id = request.GET.get('season')
        if season_id:
            request.session['season'] = season_id
        return redirect(to='index')


def user_belongs_to_group(user, group_name):
    try:
        group = UserGroup.objects.get(name=group_name)
        return user.groups.filter(name=group_name).exists()
    except UserGroup.DoesNotExist:
        return False


def get_common_info(request):
    # Season info
    all_seasons = Season.objects.all()
    season_id = request.session['season'] if 'season' in request.session else Season.objects.last().id
    season = Season.objects.get(id=season_id)
    all_tournaments_season = Tournament.objects.filter(season=season)
    # User info
    is_referee = user_belongs_to_group(request.user, 'referee')
    return {'all_seasons': all_seasons, 'season_id': season_id, 'season': season,
            'all_tournaments_season': all_tournaments_season, 'is_referee': is_referee}


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        return render(request, self.template_name, self.get_context_data(**common_info))


class GroupsView(TemplateView):
    template_name = 'groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs['tournament_id'] != 0:
            tournaments = Tournament.objects.filter(id=kwargs['tournament_id'])
        else:
            tournaments = Tournament.objects.filter(season=context['season'])
        groups_by_tournament = [Group.objects.filter(gamestage__id=1, tournament=t) for t in tournaments]
        context['tournaments'] = tournaments
        context['groups_by_tournament'] = groups_by_tournament
        # context['groups'] = groups
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, tournament_id=tournament_id))


class SingleGroupView(TemplateView):
    template_name = 'single-group.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = Group.objects.get(id=kwargs['group_id'])
        matches = Match.objects.filter(group=group).order_by('matchno')
        context['group'] = group
        context['group_results'] = group.get_results()
        context['matches'] = matches
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        group_id = int(request.GET['group']) if 'group' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, group_id=group_id))


class SingleResultView(TemplateView):
    template_name = 'single-result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = Match.objects.get(id=kwargs['match_id'])
        matchevents = MatchEvent.objects.filter(match=match)
        team_tables = [
            [
                [
                    (p.shirtno, ),
                    (p.person.short, ),
                    (p.get_goal_count_at_match(context['match']), p.id, t.id, 'goal'),
                    (p.get_foul_count_at_match(context['match']), p.id, t.id, 'foul'),
                    (p.get_yellowcard_count_at_match(context['match']), p.id, t.id, 'yellow card'),
                    (p.get_redcard_count_at_match(context['match']), p.id, t.id, 'red card'),
                    (p.get_owngoal_count_at_match(context['match']), p.id, t.id, 'own goal'),
                    (p.get_tiebreakgoal_count_at_match(context['match']), p.id, t.id, 'tie-break penalty goal'),
                ]
                for p in PlayerTournamentRegistration.objects.filter(teamreg=t)
            ]
            for t in [context['match'].hometeamreg, context['match'].awayteamreg]
        ]
        team_tables[0].sort(key=lambda x: try_int(x[0][0]))
        team_tables[1].sort(key=lambda x: try_int(x[0][0]))
        context['match'] = match
        context['matchevents'] = matchevents
        context['team_tables'] = team_tables
        context['gmaplink'] = gmaplink(context['match'].venue.address)
        context['input_permission'] = False
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        match_id = int(request.GET['match']) if 'match' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, match_id=match_id))


class FixturesView(TemplateView):
    template_name = 'fixtures.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs['tournament_id'] != 0:
            tournament = Tournament.objects.get(id=kwargs['tournament_id'])
            matches = Match.objects.filter(group__tournament=tournament).order_by('datetime')
            context['tournament'] = tournament
            context['matches'] = matches
        else:
            matches = Match.objects.filter(group__tournament__season=kwargs['season']).order_by('datetime')
            context['matches'] = matches
            context['show_tournament'] = True
        context['show_group'] = True
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, tournament_id=tournament_id))


class FixturesInputView(FixturesView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['to_input'] = True
        return context


class TeamsView(TemplateView):
    template_name = 'teams.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs['tournament_id'] != 0:
            tournaments = Tournament.objects.filter(id=kwargs['tournament_id'])
            teamregs = TeamTournamentRegistration.objects.filter(tournament=tournaments[0]).order_by('team__name')
            groups = [Group.objects.get(tournament=tournaments[0], teams=tr, gamestage__id=1) for tr in teamregs]
            group_filter = Group.objects.filter(teams__in=teamregs, gamestage_id=1).order_by('name').distinct()
        else:
            tournaments = Tournament.objects.filter(season=kwargs['season'])
            teamregs = TeamTournamentRegistration.objects.filter(tournament__in=tournaments).order_by('team__name')
            groups = [Group.objects.get(tournament__in=tournaments, teams=tr, gamestage__id=1) for tr in teamregs]
            group_filter = Group.objects.filter(teams__in=teamregs, gamestage_id=1).order_by('tournament__id',
                                                                                             'name').distinct()
        context['tournaments'] = tournaments
        context['teamregs_groups'] = zip(teamregs, groups)
        context['group_filter'] = group_filter
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, tournament_id=tournament_id))


class SingleTeamView(TemplateView):
    template_name = 'single-team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = Team.objects.get(id=kwargs['team_id'])
        teamreg = TeamTournamentRegistration.objects.filter(team=team, tournament__season=kwargs['season']).last()
        players = PlayerTournamentRegistration.objects.filter(teamreg=teamreg) if teamreg is not None else None
        matches = (Match.objects.filter(hometeamreg__team=team) | Match.objects.filter(
            awayteamreg__team=team)).order_by('-datetime')
        context['team'] = team
        context['teamreg'] = teamreg
        context['players'] = players
        context['matches'] = matches
        context['show_team'] = True
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        team_id = int(request.GET['team']) if 'team' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, team_id=team_id))


class PlayersView(TemplateView):
    template_name = 'players.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs['tournament_id'] != 0:
            tournament = Tournament.objects.get(id=kwargs['tournament_id'])
            players = PlayerTournamentRegistration.objects.filter(teamreg__tournament=tournament)
            context['tournament'] = tournament
        else:
            players = PlayerTournamentRegistration.objects.filter(teamreg__tournament__season=kwargs['season'])
            teams = TeamTournamentRegistration.objects.filter(tournament__season=kwargs['season']).values('team')
            genre_filter = Genre.objects.filter(team__in=teams).distinct()
            context['genre_filter'] = genre_filter
        context['players'] = players.order_by('person__name')
        context['show_team'] = True
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, tournament_id=tournament_id))


class SinglePlayerView(TemplateView):
    template_name = 'single-player.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = Person.objects.get(id=kwargs['player_id'])
        context['playerregs'] = PlayerTournamentRegistration.objects.filter(person=person)
        context['playerreg'] = PlayerTournamentRegistration.objects.filter(person=person).latest('person')
        context['about'] = str(person.summary).split('\n')
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        player_id = int(request.GET['player']) if 'player' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, player_id=player_id))


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        return render(request, self.template_name, self.get_context_data(**common_info))

    def post(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(to='index')
        else:
            return render(request, self.template_name, self.get_context_data(**common_info,
                                                                             error_message=_('Usuário não encontrado ou'
                                                                                             ' senha inválida.')))


class CustomLogoutView(LogoutView):
    next_page = 'index'


class CustomSignupView(TemplateView):
    template_name = 'signup.html'

    def get(self, request, *args, **kwargs):
        # activate('pt-br')
        common_info = get_common_info(request)
        form = CustomUserCreationForm()
        return render(request, self.template_name, self.get_context_data(**common_info, form=form))

    def post(self, request, *args, **kwargs):
        # activate('pt-br')
        common_info = get_common_info(request)
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(to='person-data')
        return render(request, self.template_name, self.get_context_data(**common_info, form=form))


class PersonDataView(TemplateView):
    template_name = 'person-data.html'

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        person = Person.objects.get(user_profile=request.user)
        form = PersonForm(instance=person)
        return render(request, self.template_name, self.get_context_data(**common_info, form=form))

    def post(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        person = Person.objects.get(user_profile=request.user)
        form = PersonForm(request.POST, request.FILES, instance=person)
        if form.is_valid():
            form.save()
            return redirect(to='person-data')
        return render(request, self.template_name, self.get_context_data(**common_info, form=form))


class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    success_url = '/password_reset/done/'
    form_class = CustomPasswordResetForm


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = '/password_reset/complete/'
    form_class = CustomSetPasswordForm


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'


class MatchInputView(PermissionRequiredMixin, TemplateView):
    template_name = 'match-input.html'
    permission_required = 'core.add_matchevent'
    permission_denied_message = _('Usuário não autorizado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = Match.objects.get(id=kwargs['match_id'])
        matchevents = MatchEvent.objects.filter(match=match)
        team_tables = [
            [
                [
                    (p.shirtno, ),
                    (p.person.short, ),
                    (p.get_goal_count_at_match(context['match']), p.id, t.id, 'goal'),
                    (p.get_foul_count_at_match(context['match']), p.id, t.id, 'foul'),
                    (p.get_yellowcard_count_at_match(context['match']), p.id, t.id, 'yellow card'),
                    (p.get_redcard_count_at_match(context['match']), p.id, t.id, 'red card'),
                    (p.get_owngoal_count_at_match(context['match']), p.id, t.id, 'own goal'),
                    (p.get_tiebreakgoal_count_at_match(context['match']), p.id, t.id, 'tie-break penalty goal'),
                ]
                for p in PlayerTournamentRegistration.objects.filter(teamreg=t)
            ]
            for t in [context['match'].hometeamreg, context['match'].awayteamreg]
        ]
        team_tables[0].sort(key=lambda x: try_int(x[0][0]))
        team_tables[1].sort(key=lambda x: try_int(x[0][0]))
        context['match'] = match
        context['matchevents'] = matchevents
        context['team_tables'] = team_tables
        context['gmaplink'] = gmaplink(context['match'].venue.address)
        context['input_permission'] = True
        return context

    @staticmethod
    def process_event(request):
        match = Match.objects.get(id=int(request.POST['match']))
        if request.POST['event'] == 'start_match':
            match.actualstart = datetime.now(pytz.timezone(TIME_ZONE))
            match.status = 2
            match.save()
        elif request.POST['event'] == 'finish_match':
            match.actualfinish = datetime.now(pytz.timezone(TIME_ZONE))
            match.status = 3
            match.save()
        elif request.POST['event'] == 'match_event':
            timestamp = datetime.now(pytz.timezone(TIME_ZONE))
            minutes = (timestamp-match.actualstart).total_seconds() / 60 if match.actualstart is not None else 0
            matchevent = MatchEvent(
                timestamp=timestamp,
                matchtimeminutes=minutes,
                match=match,
                playerreg=PlayerTournamentRegistration.objects.get(id=int(request.POST['player'])),
                teamreg=TeamTournamentRegistration.objects.get(id=int(request.POST['team'])),
                eventtype=MatchEventType.objects.get(name=str(request.POST['eventtype'])),
            )
            matchevent.save()

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        match_id = int(request.GET['match']) if 'match' in request.GET else (
            int(request.POST['match']) if 'match' in request.POST else 0)
        return render(request, self.template_name, self.get_context_data(**common_info, match_id=match_id))

    def post(self, request, *args, **kwargs):
        match_id = int(request.POST['match']) if 'match' in request.POST else 0
        self.process_event(request)
        target_url = reverse('match-input') + f'?match={match_id}'
        return redirect(to=target_url)


class MatchEventAddView(TemplateView):
    template_name = 'match-event-add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match'] = Match.objects.get(id=kwargs['match_id'])
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        timestamp = datetime.now(pytz.timezone(TIME_ZONE))
        match_id = int(request.GET['match']) if 'match' in request.GET else 0
        match = Match.objects.get(id=match_id) if match_id > 0 else None
        playerreg_id = int(request.GET['player']) if 'player' in request.GET else 0
        teamreg_id = int(request.GET['team']) if 'team' in request.GET else 0
        eventtype_name = str(request.GET['eventtype']) if 'eventtype' in request.GET else None
        eventtype = MatchEventType.objects.get(name=eventtype_name) if eventtype_name is not None else 0
        if match is not None and match.actualstart is not None:
            minutes = (timestamp-match.actualstart).total_seconds() / 60
        else:
            minutes = 0
        initial_data = {
            'timestamp': timestamp,
            'matchtimeminutes': minutes,
            'match': match,
            'playerreg': playerreg_id,
            'teamreg': teamreg_id,
            'eventtype': eventtype,
        }
        form = MatchEventForm(initial=initial_data)
        return render(request, self.template_name, self.get_context_data(**common_info, match_id=match_id, form=form))

    def post(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        form = MatchEventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to='match-input')
        return render(request, self.template_name, self.get_context_data(**common_info, form=form))


class MatchEventListVew(ListView):
    model = MatchEvent
    template_name = 'match-event-list.html'
    context_object_name = 'matchevents'

    def get_queryset(self):
        match_id = self.request.GET.get('match')
        if match_id:
            return MatchEvent.objects.filter(match__id=match_id)
        return super().get_queryset()


class MatchEventUpdateView(UpdateView):
    model = MatchEvent
    form_class = MatchEventForm
    template_name = 'match-event-update.html'
    success_url = reverse_lazy('match-event')

    def get_success_url(self):
        query_params = self.request.GET.urlencode()
        return f"{reverse('match-event')}?{query_params}"


class MatchEventDeleteView(DeleteView):
    model = MatchEvent
    template_name = 'match-event-delete.html'
    success_url = reverse_lazy('match-event')

    def get_success_url(self):
        query_params = self.request.GET.urlencode()
        return f"{reverse('match-event')}?{query_params}"


class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gmaplink'] = gmaplink('Rio de Janeiro')
        return context

    def form_valid(self, form):
        form.send_mail()
        messages.success(self.request, 'Contact email sent')
        return super(ContactView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Contact email error - not sent')
        return super(ContactView, self).form_invalid(form)


class AwardsView(TemplateView):
    template_name = 'awards.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs['tournament_id'] != 0:
            tournaments = Tournament.objects.filter(id=kwargs['tournament_id'])
        else:
            tournaments = Tournament.objects.filter(season=context['season'])
        topscorer = [sorted(PlayerTournamentRegistration.objects.filter(teamreg__tournament=tournament),
                            key=lambda g: g.get_goal_count(), reverse=True) for tournament in tournaments]
        fairplay = [sorted(TeamTournamentRegistration.objects.filter(tournament=tournament),
                           key=lambda t: t.get_fairplay_score(), reverse=False) for tournament in tournaments]
        topscorer = [[t for t in t_ if t.get_goal_count() > 0] for t_ in topscorer]
        if len(tournaments) > 1:
            topscorer = [t_[:10] for t_ in topscorer]
        context['tournament_topscorer_fairplay'] = zip(tournaments, topscorer, fairplay)
        return context

    def get(self, request, *args, **kwargs):
        common_info = get_common_info(request)
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(**common_info, tournament_id=tournament_id))
