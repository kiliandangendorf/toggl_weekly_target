#!/usr/bin/python3

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

def get_start_of_week_from_datetime(date:dt.datetime)->dt.date: #dt.datetime:
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
    return '{0:02.0f}:{1:02.0f} h'.format(*divmod(round(hours,2) * 60, 60))

def print_stats_aligned(stats:list[tuple[str,str]])->None:
    max_key_length=max(len(k) for k,v in stats)
    max_value_length=max(len(v) for k,v in stats)
    
    for key, value in stats:
        if key=='-':
            print(value*(2+max_key_length+max_value_length))
            continue
        spaces=1+max_key_length-len(key)+max_value_length-len(value)
        print(f"{key}:{' '*(spaces)}{value}")

def read_cache_or_get_default()->tuple[dt.datetime,int]:
    # Note this date will be a monday (beginning of week)
    try:
        with open(config.CACHE_FILE, 'r') as cache_file:
            cache_content=cache_file.readlines()
            cache_date=dt.datetime.strptime(cache_content[0].strip(), '%Y-%m-%d')
            cache_seconds=float(cache_content[1].strip())
            if(config.V):print(f"Found cache file, using start date: {cache_date.date()} and seconds tracked before: {cache_seconds}")
            return cache_date, cache_seconds
    except FileNotFoundError:
        if(config.V):print(f"No cache file found, using default start date: {config.START_DATE_STRING}")
        return dt.datetime.strptime(config.START_DATE_STRING, '%Y-%m-%d'), .0
    except Exception as e:
        print(f"Error reading cache file: {e}")
        return dt.datetime.strptime(config.START_DATE_STRING, '%Y-%m-%d'), .0

def write_cache(date:dt.date, seconds_tracked_before:float)->None:
    # Note to give a monday and seconds according to this date
    with open(config.CACHE_FILE, 'w') as cache_file:
        cache_file.write(f"{date}\n{seconds_tracked_before}")

###############################################
# MAIN
###############################################
def main()->None:    
    start_date, seconds_tracked_before_cache=read_cache_or_get_default()
    utc_now=dt.datetime.now(dt.timezone.utc)
    end_date=utc_now

    start_monday=get_start_of_week_from_datetime(start_date)
    next_monday=get_start_of_week_from_datetime(end_date+dt.timedelta(days=7))

    if config.FETCH_UNTIL_END_OF_WEEK:
        # set end date to next monday, to fetch all entries until the end of the week
        end_date=dt.datetime.combine(next_monday, dt.datetime.min.time())

    # fetch data from toggl (giving time in UTC)
    toggl_api=api.TogglAPI(config.API_TOKEN, '+00:00')
    if(config.V):print(f"Fetching time entries from {start_date.date()} to {end_date.date()}")
    time_entries=toggl_api.get_time_entries(start_date=start_date.isoformat(), end_date=end_date.isoformat())

    if type(time_entries) is str:
        print(f"Error fetching time entries: {time_entries}")
        raise Exception(f"Received no JSON from Toggl, got string instead: '{time_entries}'")

    week_between_start_and_now=(next_monday-start_monday)/7
    if seconds_tracked_before_cache>0:
        week_between_start_and_now=(next_monday-get_start_of_week_from_datetime(dt.datetime.strptime(config.START_DATE_STRING, '%Y-%m-%d')))/7
    if(config.V):print(f"Weeks between start monday ({start_monday}) and next monday ({next_monday}): {week_between_start_and_now.days} weeks")

    target_hours=week_between_start_and_now.days*config.HOURS_PER_WEEK
    if(config.V):print(f"Target hours for {week_between_start_and_now.days} weeks à {config.HOURS_PER_WEEK} hours per week: {target_hours} hours")
    if(config.V):print('########################')

    last_monday=get_start_of_week_from_datetime(utc_now)
    # TODO: Optimize this when there are many entries
    seconds_tracked_this_week=sum(max(entry['duration'], 0) for entry in time_entries if get_start_of_week_from_string(entry['start'])>=last_monday)
    seconds_tracked_before_this_week=sum(max(entry['duration'], 0) for entry in time_entries)-seconds_tracked_this_week
    # add optional cache
    seconds_tracked_before_this_week+=seconds_tracked_before_cache
    write_cache(last_monday, seconds_tracked_before_this_week)


    # THE SECRET INGREDIENT IS CRIME
    seconds_tracked_before_this_week*=config.CRIME_FACTOR
    total_seconds_tracked=seconds_tracked_before_this_week+seconds_tracked_this_week



    tracked_hours=(total_seconds_tracked / 60.0) / 60.0
    tracked_hours+=config.CARRY_OVER
    if(config.V):print(f"Tracked hours since {start_date.date()}: {format_hours_to_string(tracked_hours)}")

    last_entry=time_entries[-1]
    # list all entries that duration is negative (i.e. still running)
    current_duratios_list=[entry for entry in time_entries if entry['duration']<0]
    current_duration=0
    if len(current_duratios_list)>0:
        for current_duration_entry in current_duratios_list:
            current_duration+=get_current_duration_in_hours_from_date_string(current_duration_entry['start'])
        if(config.V):print(f"Current duration:  {format_hours_to_string(current_duration)}")

        tracked_hours+=current_duration
        if(config.V):print(f"Tracked hours (including current duration): {format_hours_to_string(tracked_hours)}")

    if(config.V):print('########################')

    stats:list[tuple[str,str]]=[]

    tracked_hours_this_week=(seconds_tracked_this_week / 60.0) / 60.0
    tracked_hours_this_week+=current_duration
    #print(f"Tracked this week: {format_hours_to_string(tracked_hours_this_week)}")
    stats.append(('Tracked this week',format_hours_to_string(tracked_hours_this_week)))


    still_to_do=target_hours-tracked_hours
    done_hours_this_week=config.HOURS_PER_WEEK-still_to_do
    overtime=done_hours_this_week-tracked_hours_this_week
    #print(f"Previous overtime: {format_hours_to_string(overtime)}")
    stats.append(('Previous overtime',format_hours_to_string(overtime)))
    #print(f"Done this week:    {format_hours_to_string(done_hours_this_week)}")
    stats.append(('Done this week',format_hours_to_string(done_hours_this_week)))
    #print(f"Target hours:      {format_hours_to_string(config.HOURS_PER_WEEK)}")
    stats.append(('Target hours',format_hours_to_string(config.HOURS_PER_WEEK)))
    #print('                   -------')
    stats.append(('-','-'))
    #print(f"Still to do:       {format_hours_to_string(still_to_do)}")
    stats.append(('Still to do',format_hours_to_string(still_to_do)))


    percentage=1.-(still_to_do/config.HOURS_PER_WEEK)
    #print(f"Done of this week: {percentage*100:.2f} %")
    stats.append(('Done of this week',f"{percentage*100:.2f} %"))

    print_stats_aligned(stats)

if __name__ == '__main__':
    main()
