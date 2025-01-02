# cfgpocket.py
# Config file pattern for small applications
# Flipped the setter pattern to no-set

from reportlab.lib.colors import yellow, green, blue, red, black

class Cfg:
    __conf = {
            "guidelines": True,
            "guidecolor": red,
            "outfile": "hello.pdf",
            "author": "pocket.py",
            "title": None,
            "subject": None,
            "keywords": None,
            "fontName": "Helvetica",
            "bullet": chr(8226),
            "drawBoundary": 0,
            "attempt": 2
            }
    __no_setters = ["attempt"]
                 #__setters = ["outfile","gridlines","author","title","subject",
                 #"keywords","fontName","bullet"]

    @staticmethod
    def config(name):
        return Cfg.__conf[name]

    @staticmethod
    def get(name):
        return Cfg.__conf[name]

    @staticmethod
    def set(name, value):
        if name in Cfg.__no_setters:
            raise NameError("Name not accepted in set() method")
        else:
            Cfg.__conf[name] = value
        #if name in App.__setters:
        #    App.__conf[name] = value
        #else:
        #    raise NameError("Name not accepted in set() method")
