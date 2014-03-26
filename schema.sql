CREATE TABLE configuration (
window_id INT PRIMARY KEY NOT NULL,
area INT NOT NULL,
hinge INT NOT NULL,
name TEXT NOT NULL,
width INT NOT NULL,
height INT NOT NULL,
angle INT NOT NULL,
enginepower INT NOT NULL,
draftthreshold INT NOT NULL);


CREATE TABLE sensordata (
window_id INT NOT NULL,
wind_angle INT,
wind_speed INT,
temperature INT,
preasure INT,
humidity INT,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (window_id, timestamp)
);

CREATE TABLE window (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL
);

CREATE TABLE state (
window_id INTEGER PRIMARY KEY NOT NULL,
open BOOLEAN,
auto BOOLEAN,
timer_id INT
);

CREATE TABLE timer (
id INTEGER PRIMARY KEY AUTOINCREMENT,
window_id INT NOT NULL,
timestamp TIMESTAMP NOT NULL
);

INSERT INTO window (name) VALUES ('Window 1');
INSERT INTO configuration (window_id, area, hinge, name, width, height, angle, enginepower, draftthreshold) VALUES (1,9,1,'',0.24,0.3,0,7.2,1);
INSERT INTO state (window_id, open, auto, timer_id) VALUES (1,0,1,0);
