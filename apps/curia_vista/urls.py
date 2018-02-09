from django.conf.urls import url
from django.views.generic.list import ListView


import sys

if True in [x in sys.argv for x in ("makemigrations", "migrate", "flush")]:
  print("urls.py: Not importing things that break makemigrations, migrate, or flush")
  urlpatterns = []
else:
  print("urls.py: importing stuff that breaks if the database is not yet setup.")
  from apps.curia_vista.views import *
  urlpatterns = [
    url(r'^department/$', ListView.as_view(context_object_name='departments',
                                           queryset=Department.objects.order_by('-name'))),
    url(r'^party/$', PartyView.as_view(), name='party'),
    url(r'^vote-helper/$', VoteView.as_view(), name='vote'),

  ]
