CREATE TABLE configuration (
window_id INT PRIMARY KEY NOT NULL,
name TEXT NOT NULL,
width INT NOT NULL,
height INT NOT NULL,
angle INT NOT NULL,
enginepower INT NOT NULL,
draftthreshold INT NOT NULL);

CREATE TABLE sensordata (
window_id INT PRIMARY KEY NOT NULL,
wind_angle INT,
wind_speed INT,
temperature INT,
preasure INT,
humidity INT
time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE window (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL
);

CREATE TABLE state (
window_id INT PRIMARY KEY NOT NULL,
open BOOLEAN,
auto BOOLEAN,
timer_id INT
);

CREATE TABLE timer (
id INT PRIMARY KEY AUTOINCREMENT,
window_id INT NOT NULL,
hour INT NOT NULL,
minute INT NOT NULL
);

INSERT INTO window (name) VALUES ('Window 1');
INSERT INTO configuration (window_id, name, width, height, angle, enginepower, draftthreshold) VALUES (1,'',0,0,0,0,0);