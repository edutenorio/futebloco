from core.models import MatchEvent, MatchEventType, Match, Group, TeamTournamentRegistration


# Auxiliary classes analogous to the SQL VIEWs
class TeamMatchEventCount:
    def __init__(self, match_id, teamreg_id, eventtype_id):
        self.count = MatchEvent.objects.filter(match__id=match_id, teamreg__id=teamreg_id,
                                               eventtype__id=eventtype_id).count()


class PlayerMatchEventCount:
    def __init__(self, match_id, playerreg_id, eventtype_id):
        self.count = MatchEvent.objects.filter(match__id=match_id, playerreg__id=playerreg_id,
                                               eventtype__id=eventtype_id).count()


class MatchResult:
    _goal_id = MatchEventType.objects.get(name='goal').id
    _own_goal_id = MatchEventType.objects.get(name='own goal').id
    _tb_goal = MatchEventType.objects.get(name='tie-break penalty goal').id
    _fault = MatchEventType.objects.get(name='fault').id
    _yc = MatchEventType.objects.get(name='yellow card').id
    _rc = MatchEventType.objects.get(name='red card').id

    def __init__(self, match_id):
        self.match = Match.objects.get(id=match_id)
        self.homescore = TeamMatchEventCount(self.match.id, self.match.hometeamreg.id, self._goal_id).count + \
                         TeamMatchEventCount(self.match.id, self.match.awayteamreg.id, self._own_goal_id).count
        self.awayscore = TeamMatchEventCount(self.match.id, self.match.awayteamreg.id, self._goal_id).count + \
                         TeamMatchEventCount(self.match.id, self.match.hometeamreg.id, self._own_goal_id).count
        self.hometiebreakscore = TeamMatchEventCount(self.match.id, self.match.hometeamreg.id, self._tb_goal).count
        self.awaytiebreakscore = TeamMatchEventCount(self.match.id, self.match.awayteamreg.id, self._tb_goal).count
        # Winner / Loser result
        self.homewin = 1 if self.homescore >  self.awayscore else 0
        self.draw    = 1 if self.homescore == self.awayscore else 0
        self.awaywin = 1 if self.homescore <  self.awayscore else 0
        self.hometiebreakwin = 1 if self.hometiebreakscore > self.awaytiebreakscore else 0
        self.awaytiebreakwin = 1 if self.hometiebreakscore < self.awaytiebreakscore else 0
        # Other events count
        self.homefaults = TeamMatchEventCount(self.match.id, self.match.hometeamreg.id, self._fault).count
        self.homeyellowcards = TeamMatchEventCount(self.match.id, self.match.hometeamreg.id, self._yc).count
        self.homeredcards = TeamMatchEventCount(self.match.id, self.match.hometeamreg.id, self._rc).count
        self.awayfaults = TeamMatchEventCount(self.match.id, self.match.awayteamreg.id, self._fault).count
        self.awayyellowcards = TeamMatchEventCount(self.match.id, self.match.awayteamreg.id, self._yc).count
        self.awayredcards = TeamMatchEventCount(self.match.id, self.match.awayteamreg.id, self._rc).count

    def __str__(self):
        if self.match.group.game_stage.id == 2 and self.draw:
            return f'{self.match.group.tournament}: (M{self.match.matchno}) ' \
                   f'{self.match.hometeamreg.team.short} {self.homescore} ({self.hometiebreakscore}) vs ' \
                   f'({self.awaytiebreakscore}) {self.awayscore} {self.match.awayteamreg.team.short}'
        else:
            return f'{self.match.group.tournament}: (M{self.match.matchno}) ' \
                   f'{self.match.hometeamreg.team.short} {self.homescore} vs ' \
                   f'{self.awayscore} {self.match.awayteamreg.team.short}'


class TeamGroupResult:
    def __init__(self, group_id, teamreg_id):
        self.group = Group.objects.get(id=group_id)
        self.teamreg = TeamTournamentRegistration.objects.get(id=teamreg_id)
        # Group Statistics from match results
        self.matches, self.wins, self.draws, self.losses = 0, 0, 0, 0
        self.goalsscored, self.goalsconceded, self.goaldifference, self.tiebreakgoals = 0, 0, 0, 0
        self.faults, self.yellowcards, self.redcards = 0, 0, 0
        # Results where the team was the home team
        for mr in [MatchResult(match.id) for match in Match.objects.filter(hometeamreg=self.teamreg, group=self.group,
                                                                           status__id__gt=1)]:
            self.matches += 1
            self.wins += mr.homewin
            self.draws += mr.draw
            self.losses += mr.awaywin
            self.goalsscored += mr.homescore
            self.goalsconceded += mr.awayscore
            self.goaldifference += mr.homescore - mr.awayscore
            self.tiebreakgoals += mr.hometiebreakscore
            self.faults += mr.homefaults
            self.yellowcards += mr.homeyellowcards
            self.redcards += mr.homeredcards
        # Results where the team was the away team
        for mr in [MatchResult(match.id) for match in Match.objects.filter(awayteamreg=self.teamreg, group=self.group,
                                                                           status__id__gt=1)]:
            self.matches += 1
            self.wins += mr.awaywin
            self.draws += mr.draw
            self.losses += mr.homewin
            self.goalsscored += mr.awayscore
            self.goalsconceded += mr.homescore
            self.goaldifference += mr.awayscore - mr.homescore
            self.tiebreakgoals += mr.awaytiebreakscore
            self.faults += mr.awayfaults
            self.yellowcards += mr.awayyellowcards
            self.redcards += mr.awayredcards
        # Group Statistics calculated
        self.points = 3 * self.wins + 1 * self.draws
        self.idx = self.points * 1E6 + self.wins * 1E4 + (50 + self.goaldifference) * 1E2 + \
                   (self.goalsscored + self.tiebreakgoals) * 1 + (99 - self.redcards) * 1.0E-2 + \
                   (99 - self.yellowcards) * 1.0E-4 + (999 - self.faults) * 1E-7

    def __str__(self):
        return f'{self.teamreg.team.name} : P({self.matches}) W({self.wins}) D({self.draws}) ' \
               f'L({self.losses}) GS({self.goalsscored}) GC({self.goalsconceded}) GD({self.goaldifference}) ' \
               f'PTS ({self.points})'

    def sort_function(self):
        return self.idx
