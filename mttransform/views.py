from django import forms
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from mitomotifs import sites2seq
from mitomotifs import str2sites
from mitomotifs import seq2sites
from mitomotifs import sites2str
from fasta import fasta
from fasta import entry2str

import re
import os

class TransformForm(forms.Form):
    query     = forms.CharField(widget=forms.widgets.Textarea(), 
                                required=False)
    file      = forms.FileField(required=False)

def sites2seq_handler(request):
    return HttpResponse('sites2seq')

def seq2sites_handler(request):
    if request.method == 'POST':
        form = TransformForm(request.POST)
        if form.is_valid():
            return process_seq2sites(form)
        else:
            return HttpResponse('form is not valid.')
    else:
        form = TransformForm()
    
    return render_to_response('mttransform/mttransform_seq2sites.html',
                              {'form': form})

#----------------------------------------------------------------------------#
# CONSTANTS
#----------------------------------------------------------------------------#

MAX_SEQS        = 10
WRAP            = 70   # where to cut and wrap fasta output

#----------------------------------------------------------------------------#
# REGEX
#----------------------------------------------------------------------------#

RE_NON_IUPAC = re.compile(r'[^ACGTURYMKSWBDHVN]')

#----------------------------------------------------------------------------#
# UTILITY CLASSES
#----------------------------------------------------------------------------#

class Result(object):
    """Simple object to hold sites2seq results for template"""
    def __init__(self, name, value):
        self.name = name
        self.value = value

#----------------------------------------------------------------------------#
# PROCESSORS
#----------------------------------------------------------------------------#

def process_seq2sites(form):
    """Process data submitted in seq2sites form"""
    # get posted parameters
    content = form.cleaned_data['query']

    # submission validation and error reporting
    problems = []
    valid = True

    # get the submitted data
    content = content.encode('utf8')

    # make sure something was submitted
    if len(content) == 0:
        valid = False
        HttpResponseRedirect(reverse('mttransform.views.seq2sites'))

    # determine format
    format = None
    if content.startswith('>'):
        format = 'fasta'
    else:
        format = 'single_seq'
        
    # pull names and sequence out of submitted content
    names = []
    seqs = []
    if format == 'fasta':
        try:
            fnames = []
            fseqs = []
            for entry in fasta(content, 's'):
                fnames.append(entry['name'])
                fseqs.append(RE_NON_IUPAC.sub('', entry['sequence'].upper()))
            names = fnames
            seqs = fseqs
        except:
            valid = False
            problems.append('There was an error in the FASTA format')
    else:
        names = ['']
        seqs = [RE_NON_IUPAC.sub('', content.upper())]

    # enforce limits for multisequence submissions
    if format == 'fasta':
        if len(seqs) > MAX_SEQS:
                valid = False
                problems.append('too many sequences submitted')

    if not valid:
        return (False, {'problems': problems})

    result_lines = []
    sites_by_line = []
    for seq in seqs:
        try:
            sites = seq2sites(seq)
            sites_by_line.append(sites)
            result_lines.append(sites2str(sites))
        except Exception, e:
            result_lines.append('There was an error: %s' % e)

    results = list(Result(x,y) for x,y in zip(names,result_lines))

    t = loader.get_template('mttransform/mttransform_sites.html')
    c = Context({
        'results': results,
    })
    return HttpResponse(t.render(c))
