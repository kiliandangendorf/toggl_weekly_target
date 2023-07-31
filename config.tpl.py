###############################################
# CONFIGURATION
###############################################

# Toggl API Token
API_TOKEN='<your api token goes here>'

# date-string from which to start fetching hours in format 'YYYY-MM-DD'
START_DATE_STRING='2023-03-01'

# target hours per week
HOURS_PER_WEEK=30

# Decimal of hours to carry over from before the start date (negative: overtime, positive: undertime)
CARRY_OVER=0.0

# Fetch time entries until the end of the week (True) or only until today now (False)
# Useful if you have entries in future as vacation or something
FETCH_UNTIL_END_OF_WEEK=True

# Toggl data comes in UTC (GMT) and needs to be converted to local time
TIMEZONE='Europe/Berlin'

# Verbose output
V=False

# Toggl data comes in this format (you shouldn't need to change this)
TIME_FORMAT='%Y-%m-%dT%H:%M:%S%z'

# The secret ingredient is crime ;) (multiply tracked hours before start date with this factor)
CRIME_FACTOR=1.