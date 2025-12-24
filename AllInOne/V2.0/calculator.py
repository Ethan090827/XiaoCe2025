import math
R = 6371
def bearing(latlong1, latlong2) -> float:
    b1 = math.radians(latlong1[0])
    b2 = math.radians(latlong2[0])
    da = math.radians(latlong2[1]) - math.radians(latlong1[1])
    y = math.sin(da) * math.cos(b2)
    x = math.cos(b1) * math.sin(b2) - math.sin(b1) * math.cos(b2) * math.cos(da)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def latlongbrng(latlong1, latlong2) -> float:
    x = latlong2[0]-latlong1[0]
    y=min(latlong2[1]-latlong1[1], latlong2[1]-latlong1[1]+360, latlong2[1]-latlong1[1]-360, key=abs)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

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
