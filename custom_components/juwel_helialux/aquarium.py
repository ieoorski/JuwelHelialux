import requests
import json
import logging
import re
import math

_LOGGER = logging.getLogger(__name__)
BASE_URL = "http://{0}/{1}"
HEADERS = {"Content-type": "application/x-www-form-urlencoded"}
session = requests.Session()

DEFAULT_COLOR = 25
DEFAULT_BRIGHTNESS = 25
MODELS = ["HeliaLux Spectrum 4Ch", "HeliaLux LED 2Ch", "HeliaLux LED 2x2Ch"]


class Aquarium(object):
    def __init__(self, host):
        self._host = host
        self._white = DEFAULT_COLOR
        self._red = DEFAULT_COLOR
        self._green = DEFAULT_COLOR
        self._blue = DEFAULT_COLOR
        self._brightness = DEFAULT_COLOR
        self._manual_colour = False
        self._state = False
        self._profile = None
        self._cswi = False
        self._profile_list = []
        self._ctime = None

    def post(self, path, data):
        if path != "week.html":
            try:
                response = session.post(
                    BASE_URL.format(self._host, path), headers=HEADERS, data=data
                )

                return json.loads(response.text)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("No aquarium found")
        else:
            try:
                session.post(
                    BASE_URL.format(self._host, path), headers=HEADERS, data=data
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("No aquarium found")

    def get(self, path):
        try:
            response = session.get(BASE_URL.format(self._host, path), headers=HEADERS)
            return response.content.decode("utf-8")
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Aquarium not available: %s", repr(err))
            _LOGGER.exception("No aquarium found")

    def set_manual_colour(self, state, time):
        self.post("stat", {"action": 14, "cswi": {state}, "ctime": {time}})
        return self.status()

    def set(self, white, blue, red, green):
        self._white = int(white / 2.54)
        self._blue = int(blue / 2.54)
        self._green = int(green / 2.54)
        self._red = int(red / 2.54)
        if self._manual_colour is False:
            self.set_manual_colour("true", "01:00")
        self.post(
            "color",
            {
                "action": 1,
                "ch1": self._white,
                "ch2": self._blue,
                "ch3": self._green,
                "ch4": self._red,
            },
        )
        return self.status()

    def set_profile(self, profile):
        index = self._profile_list.index(profile) + 1
        self.post(
            "week.html",
            {
                "key": "BU",
                "s0": f"P{index}+|+{profile}",
                "s1": f"P{index}+|+{profile}",
                "s2": f"P{index}+|+{profile}",
                "s3": f"P{index}+|+{profile}",
                "s4": f"P{index}+|+{profile}",
                "s5": f"P{index}+|+{profile}",
                "s6": f"P{index}+|+{profile}",
            },
        )

    def statusvars(self):
        statusvars = self.get("statusvars.js")

        if statusvars:
            self._profile = str(re.search(r"(?<=;profile=')\w+", statusvars).group())
            self._csimact = bool(re.search(r"(?<=;csimact=)\d+", statusvars).group())

    def profile_list(self):
        wpvars = self.get("wpvars.js")
        if wpvars:
            self._profile_list = list(
                re.search(r"(?P<profiles>\".+\")", wpvars)
                .group()
                .replace('"', "")
                .split(",")
            )

    def status(self):
        status = self.post(
            "stat",
            {
                "action": 10,
                "ch1": self._white,
                "ch2": self._blue,
                "ch3": self._green,
                "ch4": self._red,
            },
        )
        if status:
            if (self._white + self._blue + self._green + self._red) == 0:
                self._state = False
            else:
                self._state = True
            self._white = status["C"]["ch"][0]
            self._blue = status["C"]["ch"][1]
            self._green = status["C"]["ch"][2]
            self._red = status["C"]["ch"][3]
            self._ctime = status["S"]["ctime"]
            self._cswi = status["S"]["cswi"]
            self._brightness = int(
                math.sqrt(
                    0.1495 * pow(self._red, 2)
                    + 0.2935 * pow(self._green, 2)
                    + 0.057 * pow(self._blue, 2)
                    + 0.5 * pow(self._white, 2)
                )
            )
        else:
            self._state = False
        white = int(self._white * 2.54)
        red = int(self._red * 2.54)
        green = int(self._green * 2.54)
        blue = int(self._blue * 2.54)
        brightness = int(self._brightness * 2.54)
        return {
            "state": self._state,
            "brightness": brightness,
            "profile": self._profile,
            "profile_list": self._profile_list,
            "cswi": self._cswi,
            "ctime": self._ctime,
            "color": {
                "white": white,
                "red": red,
                "green": green,
                "blue": blue,
            },
        }

    def device_info(self):
        devvars = self.get("devvars.js")
        setvars = self.get("setvars.js")
        if devvars and setvars:
            output = re.findall(r"[^\[\];,=']+", devvars)
            model = int(re.search(r"(?<=;lamp=)\d+", setvars).group())
            return {
                "Device type": output[8],
                "Hardware version": output[9],
                "Software version": output[10],
                "IP adress": output[11],
                "MAC adress": output[12],
                "Model": MODELS[model],
            }


class AquariumConnectionError(Exception):
    """Raised when communication ended in error."""


class AquariumTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""
