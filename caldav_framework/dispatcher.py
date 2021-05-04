import logging
import xml.etree.ElementTree as ET
from collections import defaultdict

logger = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, obj):
        self.obj = obj

        self.handlers = defaultdict(dict)
        for obj in dir(self):
            try:
                func = getattr(self, obj)
                method = getattr(func, "method")
                prop = getattr(func, "prop")
                self.handlers[method][prop] = func
            except AttributeError:
                pass

    @classmethod
    def register(cls, method, prop):
        def inner(func):
            setattr(func, "method", method)
            setattr(func, "prop", prop)
            return func

        return inner

    def dispatch(self, method, prop, **kwargs) -> (int, ET.Element):
        ele = ET.Element(prop.tag)
        try:
            func = self.handlers[method][prop.tag]
        except KeyError:
            logger.debug("Unknown %s for %s %s", prop.tag, method, self.obj)
            return 404, ele
        else:
            return func(ele=ele, prop=prop, **kwargs)


def propfind(prop):
    return Dispatcher.register("propfind", prop)


def proppatch(prop):
    return Dispatcher.register("proppatch", prop)


def report(prop):
    return Dispatcher.register("report", prop)
