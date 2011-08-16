from datetime import datetime
import re
import urllib
from HTMLParser import HTMLParser, HTMLParseError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from releng.models import Iso

class IsoListParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

        self.hyperlinks = []
        self.url_re = re.compile('(?!\.{2})/$')

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == "href":
                    if value != '../' and self.url_re.search(value) != None:
                        self.hyperlinks.append(value[:-1])

    def parse(self, url):
        try:
            remote_file = urllib.urlopen(url)
            data = remote_file.read()
            remote_file.close()
            self.feed(data)
            self.close()
            return self.hyperlinks
        except HTMLParseError:
            raise CommandError('Couldn\'t parse "%s"' % url)

class Command(BaseCommand):
    help = 'Gets new isos from %s' % settings.ISO_LIST_URL

    def handle(self, *args, **options):
        parser = IsoListParser()
        isonames = Iso.objects.values_list('name', flat=True)
        active_isos = parser.parse(settings.ISO_LIST_URL)

        # create any names that don't already exist
        for iso in active_isos:
            if iso not in isonames:
                new = Iso(name=iso, active=True)
                new.save()
        now = datetime.utcnow()
        # and then mark all other names as no longer active
        Iso.objects.filter(active=True).exclude(name__in=active_isos).update(
                active=False, removed=now)

# vim: set ts=4 sw=4 et:
