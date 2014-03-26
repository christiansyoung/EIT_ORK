from math import cos, sin, sqrt, radians, pi


g = 9.81


def air_pressure(wind_speed, window_width, window_height, wind_direction, window_angle, window_opening_angle, left_hinge):
    v = wind_speed
    b = window_width
    h = window_height
    theta = radians(270 - wind_direction + window_angle + 180 if left_hinge else 0)
    alpha = radians(window_opening_angle)

    return v*b*h*(cos(theta)*sin(alpha) + sin(theta)*(1-sin(alpha)))


def must_close_window(wind_speed, width, height, wind_direction, window_angle, window_opening_angle, motor_torsion, left_hinge):
    v = wind_speed
    b = width
    h = height
    theta = radians(270 - wind_direction + window_angle + 180 if left_hinge else 0)
    alpha = radians(window_opening_angle)
    T = motor_torsion
    yn = 1.5
    p = 1.25
    arm = 0.5

    Fm = T*g/(arm*yn)

    if radians(1) < theta < radians(179):
        return v > sqrt(Fm/(2.5*p*b*h*sin(alpha-theta)**2))
    else:
        return 0.7*v > sqrt(Fm/(2.5*p*b*h))


def room_wind_speed(wind_speed, width, height, wind_direction, window_angle, window_opening_angle, motor_torsion, left_hinge):
    y = air_pressure(wind_speed, width, height, wind_direction, window_angle, window_opening_angle, left_hinge)
    A = 9
    hr = 2.4
    gamma = 3
    theta = radians(270 - wind_direction + window_angle + 180 if left_hinge else 0)
    alpha = radians(window_opening_angle)
    if theta > pi/2 + alpha/2:
        return 0
    return y/(sqrt(A)*hr*gamma)