from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'django.views.generic.simple.direct_to_template', 
        {'template':'mttransform/index.html'}, name='mttransform_index'),
    url(r'^documentation.html', 'django.views.generic.simple.direct_to_template', 
        {'template':'mttransform/documentation.html'}, name='mttransform_docs'),
    url(r'^seq2sites/', 'mttransform.views.seq2sites_handler', name='mttransform_seq2sites'),
    url(r'^sites2seq/', 'mttransform.views.sites2seq_handler', name='mttransform_sites2seq'),
)

