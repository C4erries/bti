import os
import copy
from pathlib import Path

from app.schemas.plan import Plan

# Predefined plan templates; keys are internal template ids
PLAN_LIBRARY: dict[str, dict] = {
    # Based on test_3d.json plan (one-room layout with 3D objects)
    "one_room_3d": {
        "meta": {
            "width": 800,
            "height": 600,
            "unit": "px",
            "scale": {"px_per_meter": 100},
            "background": None,
            "ceiling_height_m": 2.7,
        },
        "elements": [
            {
                "id": "wall_top",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "selected": False,
                "style": {"color": "#b45a3c", "textureUrl": "/static/textures/brick_basic.png"},
                "geometry": {
                    "kind": "segment",
                    "points": [100, 100, 700, 100],
                    "openings": [
                        {
                            "id": "window_living",
                            "type": "window",
                            "from_m": 3.9,
                            "to_m": 5.1,
                            "bottom_m": 0.9,
                            "top_m": 2.1,
                        }
                    ],
                },
            },
            {
                "id": "wall_right",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "selected": False,
                "style": {"color": "#b45a3c", "textureUrl": "/static/textures/brick_basic.png"},
                "geometry": {"kind": "segment", "points": [700, 100, 700, 400]},
            },
            {
                "id": "wall_bottom",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "selected": False,
                "style": {"color": "#b45a3c", "textureUrl": "/static/textures/brick_basic.png"},
                "geometry": {
                    "kind": "segment",
                    "points": [100, 400, 700, 400],
                    "openings": [
                        {
                            "id": "door_entrance",
                            "type": "door",
                            "from_m": 0.55,
                            "to_m": 1.45,
                            "bottom_m": 0.0,
                            "top_m": 2.0,
                        }
                    ],
                },
            },
            {
                "id": "wall_left",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "selected": False,
                "style": {"color": "#b45a3c", "textureUrl": "/static/textures/brick_basic.png"},
                "geometry": {"kind": "segment", "points": [100, 400, 100, 100]},
            },
            {
                "id": "wall_middle",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": False,
                "thickness": 15,
                "selected": False,
                "style": {"color": "#a0a0a0", "textureUrl": "/static/textures/concrete.png"},
                "geometry": {
                    "kind": "segment",
                    "points": [400, 100, 400, 400],
                    "openings": [
                        {
                            "id": "door_between_rooms",
                            "type": "door",
                            "from_m": 1.55,
                            "to_m": 2.45,
                            "bottom_m": 0.0,
                            "top_m": 2.0,
                        }
                    ],
                },
            },
            {
                "id": "zone_bedroom",
                "type": "zone",
                "role": "EXISTING",
                "zoneType": "bedroom",
                "relatedTo": ["wall_top", "wall_left", "wall_bottom", "wall_middle"],
                "selected": True,
                "style": {"color": "#CCE5FF", "textureUrl": "/static/textures/wood_floor.png"},
                "geometry": {"kind": "polygon", "points": [110, 110, 392.5, 110, 392.5, 390, 110, 390]},
            },
            {
                "id": "zone_living",
                "type": "zone",
                "role": "EXISTING",
                "zoneType": "living_room",
                "relatedTo": ["wall_top", "wall_middle", "wall_right", "wall_bottom"],
                "selected": True,
                "style": {"color": "#FFE5CC", "textureUrl": "/static/textures/wood_floor.png"},
                "geometry": {"kind": "polygon", "points": [407.5, 110, 690, 110, 690, 390, 407.5, 390]},
            },
            {
                "id": "label_bedroom",
                "type": "label",
                "role": "EXISTING",
                "selected": True,
                "text": "Bedroom",
                "geometry": {"kind": "point", "x": 250, "y": 230},
            },
            {
                "id": "label_living",
                "type": "label",
                "role": "EXISTING",
                "selected": False,
                "text": "Living room",
                "geometry": {"kind": "point", "x": 550, "y": 230},
            },
        ],
        "objects3d": [
            {
                "id": "bed_1",
                "type": "bed",
                "position": {"x": 1.5, "y": 0.0, "z": 1.5},
                "size": {"x": 2.0, "y": 0.6, "z": 1.6},
                "rotation": {"x": 0.0, "y": 1.57, "z": 0.0},
                "wallId": None,
                "zoneId": "zone_bedroom",
                "selected": True,
                "meta": {"note": "Кровать в спальне"},
            },
            {
                "id": "table_1",
                "type": "table",
                "position": {"x": 4.5, "y": 0.0, "z": 1.8},
                "size": {"x": 1.6, "y": 0.75, "z": 0.9},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "wallId": None,
                "zoneId": "zone_living",
                "selected": False,
                "meta": {"usage": "dining"},
            },
            {
                "id": "chair_1",
                "type": "chair",
                "position": {"x": 4.0, "y": 0.0, "z": 1.4},
                "size": {"x": 0.6, "y": 0.9, "z": 0.6},
                "rotation": {"x": 0.0, "y": 0.3, "z": 0.0},
                "wallId": None,
                "zoneId": "zone_living",
                "selected": True,
                "meta": {"note": "Стул у стола (левый)"},
            },
            {
                "id": "chair_2",
                "type": "chair",
                "position": {"x": 5.0, "y": 0.0, "z": 1.4},
                "size": {"x": 0.6, "y": 0.9, "z": 0.6},
                "rotation": {"x": 0.0, "y": -0.3, "z": 0.0},
                "wallId": None,
                "zoneId": "zone_living",
                "selected": False,
                "meta": {"note": "Стул у стола (правый)"},
            },
            {
                "id": "door_entrance",
                "type": "door",
                "position": {"x": 1.0, "y": 0.0, "z": 3.0},
                "size": {"x": 0.9, "y": 2.0, "z": 0.1},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "wallId": "wall_bottom",
                "zoneId": "zone_living",
                "selected": True,
                "meta": {"openingDirection": "inside"},
            },
            {
                "id": "door_between_rooms",
                "type": "door",
                "position": {"x": 3.0, "y": 0.0, "z": 2.0},
                "size": {"x": 0.9, "y": 2.0, "z": 0.1},
                "rotation": {"x": 0.0, "y": 1.57, "z": 0.0},
                "wallId": "wall_middle",
                "zoneId": "zone_living",
                "selected": True,
                "meta": {"openingDirection": "to_living"},
            },
            {
                "id": "window_living",
                "type": "window",
                "position": {"x": 4.5, "y": 1.4, "z": 0.0},
                "size": {"x": 1.2, "y": 1.2, "z": 0.1},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "wallId": "wall_top",
                "zoneId": "zone_living",
                "selected": False,
                "meta": {"isBalcony": False},
            },
        ],
    },
    # Simplified studio plan
    "studio": {
        "meta": {"width": 600, "height": 400, "unit": "px", "scale": {"px_per_meter": 80}, "background": None},
        "elements": [
            {
                "id": "wall_studio_top",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "geometry": {"kind": "segment", "points": [50, 50, 550, 50]},
            },
            {
                "id": "wall_studio_right",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "geometry": {"kind": "segment", "points": [550, 50, 550, 350]},
            },
            {
                "id": "wall_studio_bottom",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "geometry": {"kind": "segment", "points": [50, 350, 550, 350]},
            },
            {
                "id": "wall_studio_left",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 20,
                "geometry": {"kind": "segment", "points": [50, 350, 50, 50]},
            },
            {
                "id": "zone_studio",
                "type": "zone",
                "role": "EXISTING",
                "zoneType": "living_room",
                "selected": True,
                "geometry": {"kind": "polygon", "points": [70, 70, 530, 70, 530, 330, 70, 330]},
            },
            {
                "id": "label_studio",
                "type": "label",
                "role": "EXISTING",
                "selected": True,
                "text": "Studio",
                "geometry": {"kind": "point", "x": 300, "y": 200},
            },
        ],
        "objects3d": [],
    },
    # Two-room simple plan
    "two_room": {
        "meta": {"width": 900, "height": 500, "unit": "px", "scale": {"px_per_meter": 90}, "background": None},
        "elements": [
            {
                "id": "wall_tr_top",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 25,
                "geometry": {"kind": "segment", "points": [100, 80, 800, 80]},
            },
            {
                "id": "wall_tr_right",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 25,
                "geometry": {"kind": "segment", "points": [800, 80, 800, 420]},
            },
            {
                "id": "wall_tr_bottom",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 25,
                "geometry": {"kind": "segment", "points": [100, 420, 800, 420]},
            },
            {
                "id": "wall_tr_left",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": True,
                "thickness": 25,
                "geometry": {"kind": "segment", "points": [100, 420, 100, 80]},
            },
            {
                "id": "wall_tr_middle",
                "type": "wall",
                "role": "EXISTING",
                "loadBearing": False,
                "thickness": 15,
                "geometry": {
                    "kind": "segment",
                    "points": [450, 80, 450, 420],
                    "openings": [
                        {
                            "id": "door_tr_middle",
                            "type": "door",
                            "from_m": 1.5,
                            "to_m": 2.4,
                            "bottom_m": 0.0,
                            "top_m": 2.0,
                        }
                    ],
                },
            },
            {
                "id": "zone_tr_left",
                "type": "zone",
                "role": "EXISTING",
                "zoneType": "bedroom",
                "selected": True,
                "geometry": {"kind": "polygon", "points": [120, 100, 430, 100, 430, 400, 120, 400]},
            },
            {
                "id": "zone_tr_right",
                "type": "zone",
                "role": "EXISTING",
                "zoneType": "living_room",
                "selected": True,
                "geometry": {"kind": "polygon", "points": [470, 100, 780, 100, 780, 400, 470, 400]},
            },
            {
                "id": "label_tr_left",
                "type": "label",
                "role": "EXISTING",
                "selected": True,
                "text": "Bedroom",
                "geometry": {"kind": "point", "x": 270, "y": 230},
            },
            {
                "id": "label_tr_right",
                "type": "label",
                "role": "EXISTING",
                "selected": True,
                "text": "Living",
                "geometry": {"kind": "point", "x": 620, "y": 230},
            },
        ],
        "objects3d": [],
    },
}

# Mapping from normalized filename to template id
PLAN_TEMPLATES = {
    "demo_3d": "one_room_3d",
    "plan_1": "one_room_3d",
    "plan_studio": "studio",
    "plan_two_rooms": "two_room",
}


def normalize_filename(filename: str) -> str:
    base = os.path.basename(filename)
    name, _sep, _ext = base.partition(".")
    return name.lower()


def get_plan_by_filename(filename: str) -> Plan | None:
    key = normalize_filename(filename)
    template_id = PLAN_TEMPLATES.get(key)
    if not template_id:
        return None
    template = PLAN_LIBRARY.get(template_id)
    if not template:
        return None
    return Plan.model_validate(copy.deepcopy(template))


def list_supported_filenames() -> list[str]:
    return sorted(PLAN_TEMPLATES.keys())
