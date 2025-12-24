# calculator.py
import math
R = 6371

def bearing(latlong1, latlong2):
    b1 = math.radians(latlong1[0])
    b2 = math.radians(latlong2[0])
    da = math.radians(latlong2[1]) - math.radians(latlong1[1])
    y = math.sin(da) * math.cos(b2)
    x = math.cos(b1) * math.sin(b2) - math.sin(b1) * math.cos(b2) * math.cos(da)
    bearing_degrees = (math.degrees(math.atan2(y, x)) + 360) % 360
    # 返回度数值，而不是方位角字符串
    return bearing_degrees

def dist(latlong1, latlong2):
    coords1 = [
        math.cos(math.radians(latlong1[1])) * math.cos(math.radians(latlong1[0])),
        math.sin(math.radians(latlong1[1])) * math.cos(math.radians(latlong1[0])),
        math.sin(math.radians(latlong1[0]))
        ]
    coords2 = [
        math.cos(math.radians(latlong2[1])) * math.cos(math.radians(latlong2[0])),
        math.sin(math.radians(latlong2[1])) * math.cos(math.radians(latlong2[0])),
        math.sin(math.radians(latlong2[0]))
        ]
    linedist = (
        (coords1[0] - coords2[0]) ** 2 + \
        (coords1[1] - coords2[1]) ** 2 + \
        (coords1[2] - coords2[2]) ** 2
        ) ** 0.5
    angle = math.acos((2 - linedist ** 2) / 2)
    distance = R * angle
    if distance > 100: return round(distance / 100) * 100
    return round(distance / 10) * 10

# 如果你想在 calculator.py 中也提供一个格式化方位的函数，可以这样写：
def bearing_to_string(bearing_degrees):
    """将度数转换为方位角字符串"""
    if 0 <= bearing_degrees < 22.5:    return 'N'
    elif 22.5 <= bearing_degrees < 67.5:    return 'NE'
    elif 67.5 <= bearing_degrees < 112.5:    return 'E'
    elif 112.5 <= bearing_degrees < 157.5:    return 'SE'
    elif 157.5 <= bearing_degrees < 202.5:    return 'S'
    elif 202.5 <= bearing_degrees < 247.5:    return 'SW'
    elif 247.5 <= bearing_degrees < 292.5:    return 'W'
    elif 292.5 <= bearing_degrees < 337.5:    return 'NW'
    elif 337.5 <= bearing_degrees < 360:    return 'N'
    else: # 处理度数超出 0-360 范围的情况
        return bearing_to_string((bearing_degrees + 360) % 360)