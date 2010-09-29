from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^result/(\d+)/?$', 'mthaplotype.views.hap_result', name='hap_result'),
    url(r'^', 'mthaplotype.views.haplotype_handler', name='haplotype'),
)


