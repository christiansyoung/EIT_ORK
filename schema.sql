CREATE TABLE configuration (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
width INT NOT NULL,
height INT NOT NULL,
angle INT NOT NULL,
enginepower INT NOT NULL,
draftthreshold INT NOT NULL);

CREATE TABLE sensordata (
id INTEGER PRIMARY KEY AUTOINCREMENT,
wind_angle INT,
wind_power INT,
rain BOOLEAN);