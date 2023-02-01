import sqlite3

from django.shortcuts import render
from django.views.generic.base import TemplateView

from futebloco.settings import DATABASES
from .models import Tournament, Group, Match, Season, MatchEvent, Team, TeamTournamentRegistration, \
    PlayerTournamentRegistration
from .gmaplink import gmaplink


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        context['tournaments'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        return render(request, self.template_name, self.get_context_data(season_id=season_id))


class GroupsView(TemplateView):
    template_name = 'groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # General items
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        context['tournament'] = Tournament.objects.get(id=kwargs['tournament_id'])
        context['groups'] = Group.objects.filter(gamestage_id=1, tournament_id=kwargs['tournament_id'])
        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else Tournament.objects.filter(
            season_id=season_id).first().id
        return render(request, self.template_name, self.get_context_data(season_id=season_id,
                                                                         tournament_id=tournament_id))


class SingleGroupView(TemplateView):
    template_name = 'single-group.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        context['tournament'] = Tournament.objects.get(id=kwargs['tournament_id'])
        context['group'] = Group.objects.get(id=kwargs['group_id'])
        context['group_results'] = context['group'].get_results()
        context['matches'] = Match.objects.filter(group_id=kwargs['group_id']).order_by('matchno')

        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        group_id = int(request.GET['group']) if 'group' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(season_id=season_id,
                                                                         tournament_id=tournament_id,
                                                                         group_id=group_id))


class SingleResultView(TemplateView):
    template_name = 'single-result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        context['match'] = Match.objects.get(id=kwargs['match_id'])
        context['matchevents'] = MatchEvent.objects.filter(match__id=context['match_id'])
        context['gmaplink'] = gmaplink(context['match'].venue.address)
        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        match_id = int(request.GET['match']) if 'match' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(season_id=season_id, match_id=match_id))


class FixturesView(TemplateView):
    template_name = 'fixtures.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        if kwargs['tournament_id'] != 0:
            context['matches'] = Match.objects.filter(group__tournament_id=kwargs['tournament_id']).order_by('matchno')
            context['tournament'] = Tournament.objects.get(id=kwargs['tournament_id'])
        else:
            context['matches'] = Match.objects.filter(
                group__tournament__season_id=kwargs['season_id']).order_by('matchno')
        context['show_group'] = True
        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(season_id=season_id,
                                                                         tournament_id=tournament_id))


class TeamsView(TemplateView):
    template_name = 'teams.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        context['tournament'] = Tournament.objects.get(id=kwargs['tournament_id'])
        teamregs = TeamTournamentRegistration.objects.filter(tournament_id=kwargs['tournament_id']).order_by(
            'team__name')
        groups = [Group.objects.get(tournament_id=kwargs['tournament_id'], teams__id=teamreg.id, gamestage_id=1)
                  for teamreg in teamregs]
        context['teamregs_groups'] = zip(teamregs, groups)
        context['group_filter'] = Group.objects.filter(teams__in=teamregs, gamestage_id=1).order_by('name').distinct()
        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else Tournament.objects.filter(
            season_id=season_id).first().id
        return render(request, self.template_name, self.get_context_data(season_id=season_id,
                                                                         tournament_id=tournament_id))


class SingleTeamView(TemplateView):
    template_name = 'single-team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.get(id=kwargs['season_id'])
        context['tournament'] = Tournament.objects.get(id=kwargs['tournament_id'])
        context['all_tournaments_season'] = Tournament.objects.filter(season_id=kwargs['season_id'])
        context['team'] = Team.objects.get(id=kwargs['team_id'])
        context['teamreg'] = TeamTournamentRegistration.objects.get(team_id=kwargs['team_id'],
                                                                    tournament_id=kwargs['tournament_id'])
        context['players'] = PlayerTournamentRegistration.objects.filter(teamreg_id=context['teamreg'].id)
        context['teamregs'] = TeamTournamentRegistration.objects.filter(team_id=kwargs['team_id']).order_by(
            '-tournament__season__id')
        context['matches'] = (Match.objects.filter(hometeamreg__team__id=context['team'].id) \
                              | Match.objects.filter(awayteamreg__team__id=context['team'].id)).order_by('-datetime')
        return context

    def get(self, request, *args, **kwargs):
        season_id = int(request.GET['season']) if 'season' in request.GET else Season.objects.last().id
        tournament_id = int(request.GET['tournament']) if 'tournament' in request.GET else 0
        team_id = int(request.GET['team']) if 'team' in request.GET else 0
        return render(request, self.template_name, self.get_context_data(season_id=season_id,
                                                                         tournament_id=tournament_id,
                                                                         team_id=team_id))
