import datetime as dt
from dateutil import tz

# Using togglapi from repo ["Toggl Target" of mos3abof](https://github.com/mos3abof/toggl_target)
from togglapi import api

import config

###############################################
# FUNCTIONS
###############################################

def get_current_duration_in_hours_from_date_string(date_string:str)->float:
    start_date_local=dt.datetime.strptime(date_string, config.TIME_FORMAT).astimezone(tz.gettz(config.TIMEZONE))
    now_local=dt.datetime.now().astimezone(tz.gettz(config.TIMEZONE))
    return (now_local-start_date_local).total_seconds()/60.0/60.0

def get_start_of_week_from_datetime(date:dt.datetime)->dt.datetime:
    weekday=date.weekday()
    start_of_week=date-dt.timedelta(days=weekday)
    return start_of_week.date()

def get_start_of_week_from_string(date:str)->dt.datetime:
    #e.g. 2023-03-27T08:35:47+00:00
    date=dt.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
    return get_start_of_week_from_datetime(date)

def format_hours_to_string(hours:float)->str:
    if hours<0:
        return f"-{format_hours_to_string(-hours)}"
    return '{0:02.0f}:{1:02.0f} h'.format(*divmod(hours * 60, 60))

###############################################
# MAIN
###############################################
def main()->None:
    start_date=dt.datetime.strptime(config.START_DATE_STRING, '%Y-%m-%d')
    end_date=dt.datetime.utcnow()

    # fetch data from toggl (giving time in UTC)
    toggl_api=api.TogglAPI(config.API_TOKEN, '+00:00')
    if(config.V):print(f"Fetching time entries from {start_date} to {end_date}")
    time_entries=toggl_api.get_time_entries(start_date=start_date.isoformat(), end_date=end_date.isoformat())

    start_monday=get_start_of_week_from_datetime(start_date)
    next_monday=get_start_of_week_from_datetime(end_date+dt.timedelta(days=7))

    week_between_start_and_now=(next_monday-start_monday)/7
    if(config.V):print(f"Weeks between start monday ({start_monday}) and next monday ({next_monday}): {week_between_start_and_now.days} weeks")

    target_hours=week_between_start_and_now.days*config.HOURS_PER_WEEK
    if(config.V):print(f"Target hours for {week_between_start_and_now.days} weeks à {config.HOURS_PER_WEEK} hours per week: {target_hours} hours")
    if(config.V):print('########################')

    last_monday=get_start_of_week_from_datetime(end_date)
    # TODO: Optimize this when there are many entries
    seconds_tracked_this_week=sum(max(entry['duration'], 0) for entry in time_entries if get_start_of_week_from_string(entry['start'])>=last_monday)
    seconds_tracked_before_this_week=sum(max(entry['duration'], 0) for entry in time_entries)-seconds_tracked_this_week


    # THE SECRET INGREDIENT IS CRIME
    seconds_tracked_before_this_week*=config.CRIME_FACTOR
    total_seconds_tracked=seconds_tracked_before_this_week+seconds_tracked_this_week


    tracked_hours=(total_seconds_tracked / 60.0) / 60.0
    tracked_hours+=config.CARRY_OVER
    if(config.V):print(f"Tracked hours since {start_date.date()}: {format_hours_to_string(tracked_hours)}")

    last_entry=time_entries[-1]
    current_duration=0
    if last_entry['duration']<0:
        current_duration=get_current_duration_in_hours_from_date_string(last_entry['start'])
        if(config.V):print(f"Current duration:  {format_hours_to_string(current_duration)}")

        tracked_hours+=current_duration
        if(config.V):print(f"Tracked hours (including current duration): {format_hours_to_string(tracked_hours)}")

    if(config.V):print('########################')

    tracked_hours_this_week=(seconds_tracked_this_week / 60.0) / 60.0
    tracked_hours_this_week+=current_duration
    print(f"Tracked this week: {format_hours_to_string(tracked_hours_this_week)}")


    still_to_do=target_hours-tracked_hours
    done_hours_this_week=config.HOURS_PER_WEEK-still_to_do
    overtime=done_hours_this_week-tracked_hours_this_week
    print(f"Previous overtime: {format_hours_to_string(overtime)}")
    print(f"Done this week:    {format_hours_to_string(done_hours_this_week)}")
    print(f"Target hours:      {format_hours_to_string(config.HOURS_PER_WEEK)}")
    print('                   -------')
    print(f"Still to do:       {format_hours_to_string(still_to_do)}")


    percentage=1.-(still_to_do/config.HOURS_PER_WEEK)
    print(f"Done of this week: {percentage*100:.2f} %")

if __name__ == '__main__':
    main()
