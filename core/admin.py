from django.contrib import admin

from .models import Competition, Genre, Season, Tournament, Role, Person, Team, TeamTournamentRegistration, GameStage, \
    Group, PlayerTournamentRegistration, MatchStatus, Match, MatchEventType, MatchEvent, Venue


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'competition', 'genre', 'season')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'short', 'doc', 'dob', 'email', 'phone1', 'phone2', 'address', 'bankdata', 'photo')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'genre', 'admin', 'short', 'description', 'logo', 'photo')


@admin.register(TeamTournamentRegistration)
class TeamTournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'tournament', 'team', 'capitain')


@admin.register(GameStage)
class GameStageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'tournament', 'gamestage')


@admin.register(PlayerTournamentRegistration)
class PlayerTournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'teamreg', 'shirtno')


@admin.register(MatchStatus)
class MatchStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'matchno', 'group', 'hometeamreg', 'awayteamreg', 'datetime', 'refree', 'matchofficial', 'status',
        'venue', 'summarytext', 'summaryphoto')


@admin.register(MatchEventType)
class MatchEventTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'timestamp', 'matchtimeminutes', 'match', 'playerreg', 'teamreg', 'eventtype')


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'website')
