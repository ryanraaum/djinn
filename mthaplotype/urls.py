from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^', 'mthaplotype.views.haplotype_handler', name='haplotype'),
)


