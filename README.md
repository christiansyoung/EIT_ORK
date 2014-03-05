EIT_ORK
=======

Repo for the "Experts in Team" course at NTNU. 2014, group ORK.

With Virtualenvwrapper:

```
git clone git@github.com:lizter/EIT_ORK.git
cd EIT_ORK
mkvirtualenv eit
pip install -r requirements.txt

python service.py
```

Load data from schema.sql

```
python
from service import init_db
init_db()
```
