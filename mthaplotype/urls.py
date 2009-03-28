from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^', 'mthaplotype.views.haplotype_handler', name='mthaplotype_haplotype'),
    url(r'^documentation.html', 'django.views.generic.simple.direct_to_template', 
        {'template':'mthaplotype/documentation.html'}, name='mthaplotype_docs'),
)


