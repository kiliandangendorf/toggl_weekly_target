# Toggl Weekly Target
Show weekly target hours from Toggl in short format.

Using `togglapi`` from repo ["Toggl Target" of mos3abof](https://github.com/mos3abof/toggl_target).

## Usage
Edit `config.tpl.py` and set your Toggl API token, date from which you want to start counting and your target hours per week.
```python
API_TOKEN='<your api token goes here>'

# date-string from which to start fetching hours in format 'YYYY-MM-DD'
START_DATE_STRING='2023-03-01'

# target hours per week
HOURS_PER_WEEK=30
```

Rename `config.tpl.py` to `config.py`:
```bash
mv config.tpl.py config.py
```

And run `main.py`:
```bash
python main.py
```

## Output
```
Tracked this week: 13:27 h
Previous overtime: 14:07 h
Done this week:    27:34 h
Target hours:      30:00 h
                   -------
Still to do:       02:26 h
Done of this week: 91.88 %
```

## Troubleshooting

Maybe you need to install `python-dateutil`:
```bash
pip install python-dateutil
```