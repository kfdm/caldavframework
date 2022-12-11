"""
Format converstions

To simplify when adding fields to our model, we want to collect
all of our conversion code into a single place
"""

import icalendar

from . import models


def from_ical(data: icalendar.Calendar):
    # Given icalendar data, we want to walk to find the first vtodo
    # and then convert it to a dictionary sutible to be used to populate
    # a models.Event object.
    for event in data.walk("vtodo"):
        return {
            "raw": data.to_ical().decode("utf8"),
            "summary": event.decoded("SUMMARY").decode("utf8"),
            "created": event.decoded("CREATED"),
            "status": event.decoded("STATUS").decode("utf8"),
            "description": event.decoded("DESCRIPTION", b"").decode("utf8"),
            "updated": event.decoded("LAST-MODIFIED"),
        }


# Given a models.Event object, we want to pull out the values needed
# to convert it into a proper icalendar object.
def to_ical(instance: models.Event):
    def setup():
        # If we have an existing raw representation, we want to decode
        # it so that we can update it.
        if instance.raw:
            calendar = icalendar.Calendar.from_ical(instance.raw)
            for event in calendar.walk("vtodo"):
                return calendar, event
        # If we do not otherwise have an object, we want to create
        # a new object that can be populated
        else:
            calendar = icalendar.Calendar()
            calendar["version"] = "2.0"
            calendar["PRODID"] = "todo-server"
            event = icalendar.Todo()
            calendar.add_component(event)
            return calendar, event

    calendar, event = setup()

    def replace(key, value):
        event.pop(key)
        event.add(key, value)

    replace("uid", instance.pk)
    replace("summary", instance.summary)
    replace("created", instance.created)
    replace("last-modified", instance.updated)
    replace("description", instance.description)

    return calendar.to_ical().decode("utf-8")
