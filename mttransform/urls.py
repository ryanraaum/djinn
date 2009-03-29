from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^documentation.html', 'django.views.generic.simple.direct_to_template', 
        {'template':'mttransform/documentation.html'}, name='mttransform_docs'),
    url(r'^seq2sites/', 'mttransform.views.seq2sites_handler', name='seq2sites'),
    url(r'^sites2seq/', 'mttransform.views.sites2seq_handler', name='sites2seq'),
)

