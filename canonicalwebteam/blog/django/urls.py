from django.urls import path, register_converter
from canonicalwebteam.blog.django.views import (
    index,
    article_redirect,
    article,
    feed,
)


class FourDigitYearConverter:
    regex = "[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%04d" % value


class TwoDigitMonthConverter:
    regex = "[0-9]{2}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%02d" % value


class TwoDigitDayConverter:
    regex = "[0-9]{2}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%02d" % value


register_converter(FourDigitYearConverter, "yyyy")
register_converter(TwoDigitMonthConverter, "mm")
register_converter(TwoDigitDayConverter, "dd")


urlpatterns = [
    path(r"<yyyy:year>/<mm:month>/<dd:day>/<slug>", article_redirect),
    path(r"<yyyy:year>/<mm:month>/<slug>", article_redirect),
    path(r"<yyyy:year>/<slug>", article_redirect),
    path(r"feed", feed),
    path(r"<slug>", article, name="article"),
    path(r"", index),
]
