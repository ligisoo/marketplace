from django.db import models


class League(models.Model):
    """Model to store league/competition information"""
    api_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)
    flag = models.URLField(blank=True, null=True)
    season = models.IntegerField()
    round = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['api_id', 'season']

    def __str__(self):
        return f"{self.name} ({self.season})"


class Team(models.Model):
    """Model to store team information"""
    api_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    logo = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Venue(models.Model):
    """Model to store venue information"""
    api_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name or "Unknown Venue"


class Fixture(models.Model):
    """Model to store fixture/match information"""

    STATUS_CHOICES = [
        ('TBD', 'Time To Be Defined'),
        ('NS', 'Not Started'),
        ('1H', 'First Half'),
        ('HT', 'Halftime'),
        ('2H', 'Second Half'),
        ('ET', 'Extra Time'),
        ('P', 'Penalty In Progress'),
        ('FT', 'Match Finished'),
        ('AET', 'Match Finished After Extra Time'),
        ('PEN', 'Match Finished After Penalty'),
        ('BT', 'Break Time'),
        ('SUSP', 'Match Suspended'),
        ('INT', 'Match Interrupted'),
        ('PST', 'Match Postponed'),
        ('CANC', 'Match Cancelled'),
        ('ABD', 'Match Abandoned'),
        ('AWD', 'Technical Loss'),
        ('WO', 'WalkOver'),
    ]

    api_id = models.IntegerField(unique=True)
    referee = models.CharField(max_length=200, blank=True, null=True)
    timezone = models.CharField(max_length=100)
    date = models.DateTimeField()
    timestamp = models.BigIntegerField()

    # Venue
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)

    # Status
    status_long = models.CharField(max_length=100)
    status_short = models.CharField(max_length=10, choices=STATUS_CHOICES)
    elapsed = models.IntegerField(null=True, blank=True)

    # League
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='fixtures')

    # Teams
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_fixtures')

    # Goals
    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)
    home_goals_halftime = models.IntegerField(null=True, blank=True)
    away_goals_halftime = models.IntegerField(null=True, blank=True)
    home_goals_fulltime = models.IntegerField(null=True, blank=True)
    away_goals_fulltime = models.IntegerField(null=True, blank=True)
    home_goals_extratime = models.IntegerField(null=True, blank=True)
    away_goals_extratime = models.IntegerField(null=True, blank=True)
    home_goals_penalty = models.IntegerField(null=True, blank=True)
    away_goals_penalty = models.IntegerField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name} - {self.date.strftime('%Y-%m-%d')}"

    @property
    def is_finished(self):
        """Check if match is finished"""
        return self.status_short in ['FT', 'AET', 'PEN']

    @property
    def is_live(self):
        """Check if match is currently live"""
        return self.status_short in ['1H', '2H', 'HT', 'ET', 'P']

    def get_result_string(self):
        """Get formatted result string"""
        if self.home_goals is not None and self.away_goals is not None:
            result = f"{self.home_goals}-{self.away_goals}"
            if self.status_short == 'FT':
                return f"FT {result}"
            elif self.status_short == 'AET':
                return f"AET {result}"
            elif self.status_short == 'PEN':
                pen_result = f"{self.home_goals_penalty}-{self.away_goals_penalty}"
                return f"Pen {pen_result} (AET {result})"
            elif self.is_live:
                return f"{result} ({self.status_short})"
            return result
        return self.status_short


class APIUsageLog(models.Model):
    """Track API usage to stay within limits"""

    endpoint = models.CharField(max_length=200)
    date = models.DateField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    request_params = models.JSONField(null=True, blank=True)
    response_cached = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.endpoint} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def get_daily_count(cls, date=None):
        """Get count of API requests for a specific date"""
        from datetime import date as dt_date
        if date is None:
            date = dt_date.today()
        return cls.objects.filter(date=date, response_cached=False).count()

    @classmethod
    def can_make_request(cls, limit=100):
        """Check if we can make another API request within daily limit"""
        return cls.get_daily_count() < limit
