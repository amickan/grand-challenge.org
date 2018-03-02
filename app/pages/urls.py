from django.conf.urls import url

from pages.views import (
    page,
    insertedpage,
    PageList,
    PageCreate,
    PageUpdate,
)

urlpatterns = [
    url(r'^pages/$', PageList.as_view(), name='list'),
    url(r'^pages/create/$', PageCreate.as_view(), name='create'),
    url(r'^(?P<page_title>[\w-]+)/$', page, name='detail'),
    url(r'^(?P<page_title>[\w-]+)/update/$', PageUpdate.as_view(), name='update'),

    url(r'^(?P<page_title>[\w-]+)/insert/(?P<dropboxpath>.+)/$', insertedpage,
        name='insert-detail'),
]
