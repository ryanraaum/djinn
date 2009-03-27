from django import forms
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from oldowan.mtconvert import sites2seq
from oldowan.mtconvert import str2sites
from oldowan.mtconvert import seq2sites
from oldowan.mtconvert import sites2str
from oldowan.fasta import fasta
from oldowan.fasta import entry2str

import re
import os

class Seq2SitesForm(forms.Form):
    query       = forms.CharField(widget=forms.widgets.Textarea(), 
                                  required=False)
    query_file  = forms.FileField(required=False)

class Sites2SeqForm(forms.Form):
    FORMAT_CHOICES = [('motif_only', 'Motif only'), 
                      ('name_and_motif', 'Name and Motif'), 
                      ('name_n_and_motif', 'Name, N, and Motif')]
    OUTPUT_CHOICES = [('HVR1', 'HVR1'), 
                      ('HVR2', 'HVR2'), 
                      ('HVR1and2', 'HVR1 and HVR2'), 
                      ('HVR1to2', 'HVR1 through HVR2'), 
                      ('coding', 'Coding Region'), 
                      ('all', 'All')]

    format      = forms.ChoiceField(widget=forms.widgets.RadioSelect(), 
                                    choices=FORMAT_CHOICES,
                                    required=True,
                                    initial='motif_only')
    output      = forms.ChoiceField(widget=forms.widgets.RadioSelect(), 
                                    choices=OUTPUT_CHOICES,
                                    required=True,
                                    initial='hvr1')
    content     = forms.CharField(widget=forms.widgets.Textarea(),
                                  required=False)
    add16k      = forms.BooleanField(label='Add 16000 to every site?', 
                                     required=False)
    file        = forms.FileField(required=False)

def sites2seq_handler(request):
    if request.method == 'POST':
        form = Sites2SeqForm(request.POST, request.FILES)
        if form.is_valid():
            return process_sites2seq(form)
        else:
            return HttpResponse('form is not valid')

    form = Sites2SeqForm()
    return render_to_response('mttransform/mttransform_sites2seq.html',
                              {'form': form})


def seq2sites_handler(request):
    if request.method == 'POST':
        form = Seq2SitesForm(request.POST, request.FILES)
        if form.is_valid():
            return process_seq2sites(form)
        else:
            return HttpResponse('form is not valid.')

    form = Seq2SitesForm()
    return render_to_response('mttransform/mttransform_seq2sites.html',
                              {'form': form})

#----------------------------------------------------------------------------#
# CONSTANTS
#----------------------------------------------------------------------------#

MAX_SEQS        = 100
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

    # submission validation and error reporting
    problems = []
    valid = True

    # first, just assume whatever is in the textarea is the submission
    # even if that may be nothing
    content = form.cleaned_data['query']   

    # then check to see if a file was supplied, and if so, replace the
    # previously assumed content with the file data
    if form.cleaned_data['query_file'] is not None:
        if form.cleaned_data['query_file'].multiple_chunks():
            pass
            # error - return with error
        content = form.cleaned_data['query_file'].read()

    # clear off any trailing whitespace
    content.strip()

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
                problems.append('Too many sequences submitted; current maximum allowed is %d' % MAX_SEQS)

    if valid:
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

        c = Context({'results': results})

    else: # not valid
        c = Context({'problems':problems})

    t = loader.get_template('mttransform/mttransform_sites.html')
    return HttpResponse(t.render(c))


def process_sites2seq(form):
    """Process data submitted in sites2seq form"""

    problems = []
    valid = True

    # first, just assume whatever is in the textarea is the submission
    # even if that may be nothing
    content = form.cleaned_data['content']

    # then check to see if a file was supplied, and if so, replace the
    # previously assumed content with the file data
    if form.cleaned_data['file'] is not None:
        if form.cleaned_data['file'].multiple_chunks():
            pass
            # error - return with error
        content = form.cleaned_data['file'].read()

    content_lines = content.strip().split('\n')
    names = []
    ns = []
    motifs = []
    count = 0
    for curr_line in content_lines:
        line = re.sub(r'[,;]', ' ', curr_line)

        count += 1
        name = 'Seq%s' % count
        n = 1
        motif = line
        if form.cleaned_data['format'] == 'name_and_motif':
            split = line.split(' ', 1)
            if len(split) == 2:
                name, motif = split 
            else:
                valid = False
                msg = 'The entry "%s" is not correctly formatted' % curr_line
                problems.append(msg)
        elif form.cleaned_data['format'] == 'name_n_and_motif':
            split = line.split(' ', 2)
            if len(split) == 3:
                name, n, motif = split 
                if re.match(r'^[0-9]+$', n) is None:
                    valid = False
                    problems.append("One of the given 'N's is not a number")
                else:
                    n = int(n)
            else:
                valid = False
                msg = 'The entry "%s" is not correctly formatted' % curr_line
                problems.append(msg)
        names.append(name)
        ns.append(n)
        motifs.append(motif)
        
    if valid:
        pnames = []
        pseqs = []
        for name,n,motif in zip(names,ns,motifs):
            try:
                sites = str2sites(motif)
                seq = sites2seq(sites, region=form.cleaned_data['output'], add16k=form.cleaned_data['add16k'])
                for i in range(n):
                    pnames.append(name)
                    pseqs.append(seq)
            except Exception, e:
                valid = False
                problems.append(e)

    if valid:
        as_fasta = ''.join(list(entry2str({'name':name,'sequence':seq}, WRAP) 
                                for name,seq in zip(pnames, pseqs)))
        c = Context({'results': as_fasta})

    else: # not valid
        c = Context({'problems':problems})

    t = loader.get_template('mttransform/mttransform_seqs.html')
    return HttpResponse(t.render(c))

