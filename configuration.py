import configparser
from typing import Dict, Callable


def dont_care(d, name):
    return True


def present(d, name):
    return name in d.keys()


def is_integer(d, name):
    if not present(d, name):
        return False
    # noinspection PyBroadException
    try:
        v = int(d[name])
    except:
        return False
    return True


def is_integer_nonzero_positive(d, name):
    if not present(d, name):
        return False
    if not is_integer(d, name):
        return False
    int_val = int(d[name])
    return int_val > 0


def is_boolean(d, name):
    if not present(d, name):
        return False
    # noinspection PyBroadException
    try:
        v = d[name].lower()
        return v in ["true", "false", "1", "0", "yes", "no", "on", "off"]
    except:
        return False
    return True


graphics_schema: Dict[str, Callable[[Dict[str, object], str], bool]] = {
    "width": is_integer_nonzero_positive,
    "height": is_integer_nonzero_positive,
    "full_screen": is_boolean,
    "max_fps": lambda x, y: is_integer_nonzero_positive(x, y) and int(x[y]) >= 30,  # minimum fps
}


def get_graphics_settings():
    settings = configparser.ConfigParser()
    settings.read("settings.ini")
    graphics_settings = settings["graphics"]
    if validate_section(graphics_settings, graphics_schema, True):
        return graphics_settings
    else:
        return None


def validate_section(section, schema, strict):
    if strict:
        for k in section.keys():
            if k not in schema.keys():
                return False
    for field, validator in schema.items():
        res = validator(section, field)
        if not res:
            return False
    return True
