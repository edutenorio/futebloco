import datetime
import os
import uuid

from django.db import models
from stdimage.models import StdImageField
from dynamic_filenames import FilePattern


def get_file_path(_instance, filename):
    """Generates a file name to store images"""
    filename, file_extension = os.path.splitext(filename)
    return f'{uuid.uuid4()}{file_extension}'


class Competition(models.Model):
    name = models.CharField(name='name', max_length=255)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(name='name', max_length=255)

    def __str__(self):
        return self.name


class Season(models.Model):
    name = models.CharField(name='name', max_length=255)

    def __str__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(name='name', max_length=255)
    competition = models.ForeignKey(to=Competition, on_delete=models.CASCADE)
    genre = models.ForeignKey(to=Genre, on_delete=models.CASCADE)
    season = models.ForeignKey(to=Season, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(name='name', max_length=255)

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(name='name', max_length=255)
    short = models.CharField(name='short', max_length=255)
    doc = models.CharField(name='doc', max_length=15, null=True, blank=True)
    dob = models.DateField(name='dob', null=True, blank=True)
    email = models.EmailField(name='email', max_length=255, null=True, blank=True)
    phone1 = models.CharField(name='phone1', max_length=25, null=True, blank=True)
    phone2 = models.CharField(name='phone2', max_length=25, null=True, blank=True)
    address = models.CharField(name='address', max_length=255, null=True, blank=True)
    bankdata = models.TextField(name='bankdata', null=True, blank=True)
    photo = StdImageField(name='photo', upload_to=FilePattern(filename_pattern='person-photos/{uuid:base32}{ext}'),
                          null=True, blank=True, variations={'large': (1200, 800, True),
                                                             'medium': (600, 400, True),
                                                             'thumb': (300, 200, True)})
    roles = models.ManyToManyField(to=Role)

    def get_age(self):
        now = datetime.datetime.now()
        return now.year - self.dob.year - int((now.month, now.day) < (self.dob.month, self.dob.day))

    def tournament_count(self):
        return PlayerTournamentRegistration.objects.filter(person_id=self.id).count()

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(name='name', max_length=255)
    genre = models.ForeignKey(to=Genre, on_delete=models.CASCADE)
    admin = models.ForeignKey(to=Person, on_delete=models.CASCADE)
    short = models.CharField(name='short', max_length=4)
    description = models.TextField(name='description', null=True, blank=True)
    logo = StdImageField(name='logo', upload_to=FilePattern(filename_pattern='team-logos/{uuid:base32}{ext}'),
                         null=True, blank=True, variations={'standard': (300, 300),
                                                            'small': (70, 70),
                                                            'thumb': (46, 46)})
    photo = StdImageField(name='photo', upload_to=FilePattern(filename_pattern='team-photos/{uuid:base32}{ext}'),
                          null=True, blank=True, variations={'large': (1200, 800, True),
                                                             'medium': (600, 400, True),
                                                             'thumb': (300, 200, True)})
    website = models.URLField(name='website', max_length=255, null=True, blank=True)
    facebook = models.URLField(name='facebook', max_length=255, null=True, blank=True)
    instagram = models.URLField(name='istagram', max_length=255, null=True, blank=True)
    twitter = models.URLField(name='twitter', max_length=255, null=True, blank=True)
    youtube = models.URLField(name='youtube', max_length=255, null=True, blank=True)

    def get_tournament_count(self):
        return TeamTournamentRegistration.objects.filter(team_id=self.id).count()

    def get_match_count(self):
        return Match.objects.filter(hometeamreg__team__id=self.id).count() \
            + Match.objects.filter(awayteamreg__team__id=self.id).count()

    def get_win_count(self):
        return sum([match.is_homewin() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.is_awaywin() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_draw_count(self):
        return sum([match.is_draw() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.is_draw() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_loss_count(self):
        return sum([match.is_awaywin() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.is_homewin() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_goalscored_count(self):
        return sum([match.get_homescore() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_awayscore() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_goalconceded_count(self):
        return sum([match.get_awayscore() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_homescore() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_tiebreakgoalscored_count(self):
        return sum([match.get_hometiebreakscore() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_awaytiebreakscore() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_tiebreakgoalconceded_count(self):
        return sum([match.get_awaytiebreakscore() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_hometiebreakscore() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_fault_count(self):
        return sum([match.get_homefaults() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_awayfaults() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_faultagainst_count(self):
        return sum([match.get_awayfaults() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_homefaults() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_yellowcard_count(self):
        return sum([match.get_homeyellowcards() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_awayyellowcards() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_redcard_count(self):
        return sum([match.get_homeredcards() for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_awayredcards() for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_owngoal_count(self):
        return MatchEvent.objects.filter(teamreg__team__id=self.id, eventtype__name='own goal').count()

    def get_cleansheet_count(self):
        return sum([match.get_awayscore() == 0 for match in Match.objects.filter(hometeamreg__team__id=self.id)]) \
            + sum([match.get_homescore() == 0 for match in Match.objects.filter(awayteamreg__team__id=self.id)])

    def get_title_count(self):
        return sum([match.is_homewin() for match in Match.objects.filter(hometeamreg__team__id=self.id,
                                                                         group__gamestage__id=3)]) \
            + sum([match.is_awaywin() for match in Match.objects.filter(awayteamreg__team__id=self.id,
                                                                        group__gamestage__id=3)])

    def get_runnerup_count(self):
        return sum([match.is_awaywin() for match in Match.objects.filter(hometeamreg__team__id=self.id,
                                                                         group__gamestage__id=3)]) \
            + sum([match.is_homewin() for match in Match.objects.filter(awayteamreg__team__id=self.id,
                                                                        group__gamestage__id=3)])

    def get_thirdplace_count(self):
        return sum([match.is_homewin() for match in Match.objects.filter(hometeamreg__team__id=self.id,
                                                                         group__gamestage__id=2)]) \
            + sum([match.is_awaywin() for match in Match.objects.filter(awayteamreg__team__id=self.id,
                                                                        group__gamestage__id=2)])

    def __str__(self):
        return self.name


class TeamTournamentRegistration(models.Model):
    tournament = models.ForeignKey(to=Tournament, on_delete=models.CASCADE)
    team = models.ForeignKey(to=Team, on_delete=models.CASCADE)
    capitain = models.ForeignKey(to=Person, on_delete=models.CASCADE)
    photo = StdImageField(name='photo', upload_to=FilePattern(filename_pattern='team-photos/{uuid:base32}{ext}'),
                          null=True, blank=True, variations={'large': (1200, 800, True),
                                                             'medium': (600, 400, True),
                                                             'thumb': (300, 200, True)})

    def get_group_results(self, group_id):
        result = {'matches': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'goalsscored': 0, 'goalsconceded': 0,
                  'goaldifference': 0, 'tiebreakgoals': 0, 'faults': 0, 'yellowcards': 0, 'redcards': 0}
        # Results when playing as home team
        for match in Match.objects.filter(hometeamreg_id=self.id, group_id=group_id, status__id__gt=1):
            result['matches'] += 1
            result['wins'] += match.is_homewin()
            result['draws'] += match.is_draw()
            result['losses'] += match.is_awaywin()
            result['goalsscored'] += match.get_homescore()
            result['goalsconceded'] += match.get_awayscore()
            result['goaldifference'] += match.get_homescore() - match.get_awayscore()
            result['tiebreakgoals'] += match.get_hometiebreakscore()
            result['faults'] += match.get_homefaults()
            result['yellowcards'] += match.get_homeyellowcards()
            result['redcards'] += match.get_homeredcards()
        # Result when playing as away team
        for match in Match.objects.filter(awayteamreg_id=self.id, group_id=group_id, status__id__gt=1):
            result['matches'] += 1
            result['wins'] += match.is_awaywin()
            result['draws'] += match.is_draw()
            result['losses'] += match.is_homewin()
            result['goalsscored'] += match.get_awayscore()
            result['goalsconceded'] += match.get_homescore()
            result['goaldifference'] += match.get_awayscore() - match.get_homescore()
            result['tiebreakgoals'] += match.get_awaytiebreakscore()
            result['faults'] += match.get_awayfaults()
            result['yellowcards'] += match.get_awayyellowcards()
            result['redcards'] += match.get_awayredcards()
        result['points'] = 3*result['wins'] + 1*result['draws']
        result['idx'] = result['points'] * 1E6 + result['wins'] * 1E4 + (50 + result['goaldifference']) * 1E2 \
                        + (result['goalsscored'] + result['tiebreakgoals']) * 1 + (99 - result['redcards']) * 1.0E-2 \
                        + (99 - result['yellowcards']) * 1.0E-4 + (999 - result['faults']) * 1E-7
        return result

    def __str__(self):
        return f'Registry: ({self.tournament}) <-> ({self.team})'


class GameStage(models.Model):
    name = models.CharField(name='name', max_length=255)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(name='name', max_length=255)
    tournament = models.ForeignKey(to=Tournament, on_delete=models.CASCADE)
    gamestage = models.ForeignKey(to=GameStage, on_delete=models.CASCADE)
    teams = models.ManyToManyField(to=TeamTournamentRegistration)

    def get_results(self):
        results = [(teamreg, teamreg.get_group_results(self.id)) for teamreg in self.teams.all()]
        results.sort(reverse=True, key=lambda item: item[1]['idx'])
        return results

    def __str__(self):
        return self.name


class PlayerTournamentRegistration(models.Model):
    person = models.ForeignKey(to=Person, on_delete=models.CASCADE)
    teamreg = models.ForeignKey(to=TeamTournamentRegistration, on_delete=models.CASCADE)
    position = models.CharField(name='position', max_length=20, null=True, blank=True)
    shirtno = models.CharField(name='shirtno', max_length=10)

    def __str__(self):
        return f'Registry: ({self.teamreg}) <-> ({self.person}) Shirt ({self.shirtno})'


class MatchStatus(models.Model):
    name = models.CharField(name='name', max_length=11)

    class Meta:
        verbose_name_plural = 'Match statuses'

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(name='name', max_length=255)
    address = models.CharField(name='address', max_length=255, null=True, blank=True)
    website = models.URLField(name='website', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    matchno = models.IntegerField(name='matchno')
    group = models.ForeignKey(to=Group, on_delete=models.CASCADE)
    hometeamreg = models.ForeignKey(to=TeamTournamentRegistration, related_name='hometeamreg', on_delete=models.CASCADE)
    awayteamreg = models.ForeignKey(to=TeamTournamentRegistration, related_name='awayteamreg', on_delete=models.CASCADE)
    datetime = models.DateTimeField(name='datetime', null=True, blank=True)
    refree = models.ForeignKey(to=Person, null=True, blank=True, related_name='refree', on_delete=models.SET_NULL)
    matchofficial = models.ForeignKey(to=Person, null=True, blank=True, related_name='matchofficial',
                                      on_delete=models.SET_NULL)
    status = models.ForeignKey(to=MatchStatus, on_delete=models.CASCADE, default=1)
    venue = models.ForeignKey(to=Venue, on_delete=models.CASCADE)
    summarytext = models.TextField(name='summarytext', null=True, blank=True)
    summaryphoto = models.ImageField(name='summaryphoto', null=True, blank=True, upload_to='match_summaries')

    class Meta:
        verbose_name_plural = 'Matches'

    def get_homescore(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.hometeamreg, eventtype__name='goal').count() \
            + MatchEvent.objects.filter(match_id=self.id, teamreg=self.awayteamreg, eventtype__name='own goal').count()

    def get_awayscore(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.awayteamreg, eventtype__name='goal').count() \
            + MatchEvent.objects.filter(match_id=self.id, teamreg=self.hometeamreg, eventtype__name='own goal').count()

    def get_hometiebreakscore(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.hometeamreg,
                                         eventtype__name='tie-break penalty goal').count()

    def get_awaytiebreakscore(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.awayteamreg,
                                         eventtype__name='tie-break penalty goal').count()

    def is_draw(self):
        return 1 if self.get_homescore() == self.get_awayscore() else 0

    def is_homewin(self):
        return 1 if self.get_homescore() > self.get_awayscore() else 0

    def is_awaywin(self):
        return 1 if self.get_homescore() < self.get_awayscore() else 0

    def get_homefaults(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.hometeamreg, eventtype__name='fault').count()

    def get_awayfaults(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.awayteamreg, eventtype__name='fault').count()

    def get_homeyellowcards(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.hometeamreg,
                                         eventtype__name='yellow card').count()

    def get_awayyellowcards(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.awayteamreg,
                                         eventtype__name='yellow card').count()

    def get_homeredcards(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.hometeamreg, eventtype__name='red card').count()

    def get_awayredcards(self):
        return MatchEvent.objects.filter(match_id=self.id, teamreg=self.awayteamreg, eventtype__name='red card').count()

    def __str__(self):
        return f'M({self.matchno}): ({self.hometeamreg.team}) vs ({self.awayteamreg.team})'


class MatchEventType(models.Model):
    name = models.CharField(name='name', max_length=255)

    def __str__(self):
        return self.name


class MatchEvent(models.Model):
    timestamp = models.DateTimeField(name='timestamp', null=True, blank=True)
    matchtimeminutes = models.FloatField(name='matchtimeminutes', null=True, blank=True)
    match = models.ForeignKey(to=Match, on_delete=models.CASCADE)
    playerreg = models.ForeignKey(to=PlayerTournamentRegistration, on_delete=models.CASCADE, null=True, blank=True)
    teamreg = models.ForeignKey(to=TeamTournamentRegistration, on_delete=models.CASCADE, null=True, blank=True)
    eventtype = models.ForeignKey(to=MatchEventType, on_delete=models.CASCADE)

    def __str__(self):
        return ''.join([f'{self.eventtype}', f' ({self.playerreg.person})' if self.playerreg else '',
                        f' ({self.teamreg.team})' if self.teamreg else '',
                        f' at {self.matchtimeminutes:.2f} min' if self.matchtimeminutes else ''])
