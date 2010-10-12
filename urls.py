from django.conf import settings
from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^djinn/', include('djinn.foo.urls')),
    url(r'^$', 'django.views.generic.simple.direct_to_template', 
        {'template':'base_index.html'}, name='base_index'),
    url(r'^contact/$', lambda r: HttpResponseRedirect('http://www.raaum.org'), name='contact'),
    (r'^transform/', include('mttransform.urls')),
    (r'^haplotype/', include('mthaplotype.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)

if settings.DEBUG:
    urlpatterns += patterns('',
            (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
