"""Display-only metric projection; no changes to world coordinates or MQTT data."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Viewport:
    room_x: float
    room_z: float
    scale: float
    padding: float

    @classmethod
    def fit(cls, room_x, room_z, max_width, max_height, padding):
        if not all(math.isfinite(float(v)) for v in (room_x, room_z, max_width, max_height, padding)):
            raise ValueError('Visualizer dimensions must be finite')
        if room_x <= 0 or room_z <= 0 or padding < 0:
            raise ValueError('Room dimensions must be positive')
        scale = min((max_width - 2 * padding) / room_x,
                    (max_height - 2 * padding) / room_z)
        if scale <= 0:
            raise ValueError('Visualizer window too small for its padding')
        return cls(room_x, room_z, scale, padding)

    @property
    def width(self):
        return math.ceil(2 * self.padding + self.room_x * self.scale)

    @property
    def height(self):
        return math.ceil(2 * self.padding + self.room_z * self.scale)

    def project(self, x, z):
        return self.padding + x * self.scale, self.padding + (self.room_z - z) * self.scale

    def contains(self, x, z):
        return 0 <= x <= self.room_x and 0 <= z <= self.room_z


def draw_room(canvas, view):
    p = view.padding
    right, _ = view.project(view.room_x, view.room_z)
    _, bottom = view.project(0, 0)
    canvas.create_rectangle(p, p, right, bottom, fill='#303a43', outline='#8395a7', width=2)
    step = max(1, math.ceil(max(view.room_x, view.room_z) / 12))
    for x in range(0, math.ceil(view.room_x), step):
        horizontal, _ = view.project(x, 0)
        canvas.create_line(horizontal, p, horizontal, bottom, fill='#465460')
        canvas.create_text(horizontal, bottom + 14, text=str(x), fill='#d8e1e8')
    for z in range(0, math.ceil(view.room_z), step):
        _, vertical = view.project(0, z)
        canvas.create_line(p, vertical, right, vertical, fill='#465460')
        canvas.create_text(p - 20, vertical, text=str(z), fill='#d8e1e8')
    canvas.create_text((p + right) / 2, 12, text=f'Z ↑  {view.room_z:g} m', fill='white')
    canvas.create_text((p + right) / 2, bottom + 34,
                       text=f'X →  {view.room_x:g} m · origine (0, 0) in basso a sinistra', fill='white')


def draw_entities(canvas, view, entities, radius=5):
    canvas.delete('entity')
    visible = outside = invalid = 0
    for entity in entities:
        try:
            x, z = map(float, entity['position'])
            ident, category = entity['id'], entity['category']
            if not math.isfinite(x) or not math.isfinite(z):
                raise ValueError('non-finite position')
        except (KeyError, TypeError, ValueError, OverflowError):
            invalid += 1
            continue
        if not view.contains(x, z):
            outside += 1
            continue
        horizontal, vertical = view.project(x, z)
        canvas.create_oval(horizontal - radius, vertical - radius,
                           horizontal + radius, vertical + radius,
                           fill='#ffe066', outline='#161c22', tags='entity')
        anchor = 'e' if x > view.room_x / 2 else 'w'
        label_x = horizontal - radius - 4 if anchor == 'e' else horizontal + radius + 4
        canvas.create_text(label_x, vertical, anchor=anchor,
                           text=f'ID {ident} · classe {category}\nX {x:.3f}  Z {z:.3f} m',
                           fill='#ffe066', tags='entity')
        visible += 1
    return visible, outside, invalid
