EIT_ORK
=======

Repo for the "Experts in Team" course at NTNU. 2014, group ORK.

####With Virtualenvwrapper

```
git clone git@github.com:lizter/EIT_ORK.git
cd EIT_ORK
mkvirtualenv eit
pip install -r requirements.txt
python service.py
```

####Load data from schema.sql

```
python
from service import init_db
init_db()
```

####Deploy on RPi

```
cd /var/websites/EIT_ORK/
git pull origin master
find . -name '*.pyc' -delete
supervisorctl restart webservice
```

####Start simulation

Takes five sec to kill with ^C, since it's a thread without proper interrupt shit..

```
cd /var/websites/EIT_ORK/
source venv/bin/activate
python weather_simulation.py
````

####Unleash hell

Makes a post request with a nasty storm to force closing the window in auto mode

```
cd /var/websites/EIT_ORK/
source venv/bin/activate
python windy_weather.py
```

####Troubleshooting

- gunicorn process log: (tail -f / less) /var/log/supervisor/webservice-stdout<HASH>.log
- restart nginx: service nginx restart
