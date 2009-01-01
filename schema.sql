CREATE TABLE configuration (
id INTEGER PRIMARY KEY AUTOINCREMENT,
window_id INT NOT NULL,
name TEXT NOT NULL,
width INT NOT NULL,
height INT NOT NULL,
angle INT NOT NULL,
enginepower INT NOT NULL,
draftthreshold INT NOT NULL);

CREATE TABLE sensordata (
id INTEGER PRIMARY KEY AUTOINCREMENT,
window_id INT NOT NULL,
wind_angle INT,
wind_speed INT,
temperature INT,
preasure INT,
humidity INT);

CREATE TABLE window (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL
);

INSERT INTO window (name) VALUES ('Window 1');
INSERT INTO configuration (window_id, name, width, height, angle, enginepower, draftthreshold) VALUES (1,'',0,0,0,0,0);