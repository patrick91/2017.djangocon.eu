# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import datetime as dt
import requests
from django.core.management.base import BaseCommand
from conference.schedule.models import Slot


DATABASE_NAME = "djangocon_eu2017"


CONFIG = {
    "config": {
        "pycon_name": "DjangoCon Europe 2017",
        "pycon_logo": "https://pbs.twimg.com/profile_images/776690513038770176/lv-VuHb7_400x400.jpg",
        "pycon_color": "#7F4C74",
        "twitter_hashtag": "#DjangoCon",
        "pycon_db": DATABASE_NAME,
        "active": True,
    }
}


BASE_URL = 'https://pycon-630b8.firebaseio.com/{}.json'.format(
    DATABASE_NAME
)


class SlotSerializer(object):

    def __init__(self, queryset):
        self.queryset = queryset

    @classmethod
    def get_slot_type(cls, slot):
        if slot.is_talk:
            return "talk"

        if slot.is_workshop:
            return "workshop"

        if slot.title in ("Coffee Break", "Lunch"):
            return "break"

        return "other"

    @classmethod
    def get_end_time(cls, time, duration):
        combined = dt.datetime.combine(dt.date.today(), time)
        end_time = combined + dt.timedelta(hours=1)
        return end_time.time()

    @classmethod
    def to_pycon_app(cls, slot):
        submission = slot.talk if slot.talk else slot.workshop
        endtime = cls.get_end_time(slot.start, slot.duration)

        return {
            "active": True,
            "avatar": slot.get_image(),
            "bio": getattr(submission, "author_bio", ""),
            "description": slot.abstract,
            "end_date": slot.day.strftime("%d.%m."),
            "end_time": endtime.strftime("%H:%M"),
            "id": str(slot.pk),
            "speaker": slot.author,
            "start_date": slot.day.strftime("%d.%m."),
            "start_time": slot.start.strftime("%H:%M"),
            "title": slot.title,
            "twitter": slot.twitter,
            "type": cls.get_slot_type(slot),
            "votes": ["", ]
        }

    def serialize(self):
        data = [self.to_pycon_app(slot) for slot in self.queryset]
        return {"Odeon": data}


class Command(BaseCommand):

    def handle(self, *args, **options):
        qs = Slot.objects.all()
        serializer = SlotSerializer(qs)
        update = serializer.serialize()

        data = {
            "main": CONFIG,
            "rooms": update
        }

        requests.put(BASE_URL, json=data)