from django import forms
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from oldowan.mitotype import HVRMatcher
from oldowan.mitotype import prevalidate_submission

HVRM = HVRMatcher()

import re
import os

class HaplotypeForm(forms.Form):
    query       = forms.CharField(widget=forms.widgets.Textarea(),
                                  required=False)
    file        = forms.FileField(required=False)

def haplotype_handler(request):
    if request.method == 'POST':
        form = HaplotypeForm(request.POST, request.FILES)
        if form.is_valid():
            return process_haplotypes(form)
        else:
            return HttpResponse('form is not valid')

    form = HaplotypeForm()
    return render_to_response('mthaplotype/index.html',
                              {'form': form})


#----------------------------------------------------------------------------#
# PROCESSORS
#----------------------------------------------------------------------------#

def process_haplotypes(form):
    """Process data submitted in seq2sites form"""

    # submission validation and error reporting
    problems = []
    valid = True

    # first, just assume whatever is in the textarea is the submission
    # even if that may be nothing
    content = form.cleaned_data['query']   

    # then check to see if a file was supplied, and if so, replace the
    # previously assumed content with the file data
    if form.cleaned_data['file'] is not None:
        if form.cleaned_data['file'].multiple_chunks():
            pass
            # error - return with error
        content = form.cleaned_data['file'].read()

    # clear off any trailing whitespace and convert to non-unicode string
    content = str(content).strip()

    # make sure something was submitted
    if len(content) == 0:
        valid = False
        HttpResponseRedirect(reverse('mttransform.views.seq2sites'))

    # validate and determine format
    vi = prevalidate_submission(content)
    
    if vi.valid:
        results = HVRM.match(content, vi)
        c = Context({'results': results})

    else: # not valid
        problems.append(vi.problem)
        c = Context({'problems':problems})

    t = loader.get_template('mthaplotype/mthaplotype_results.html')
    return HttpResponse(t.render(c))

