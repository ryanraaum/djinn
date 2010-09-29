from django import forms
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from mthaplotype.models import Haplotyping
from mthaplotype.tasks import process_haplotypes

class HaplotypeForm(forms.Form):
    query       = forms.CharField(widget=forms.widgets.Textarea(),
                                  required=False)
    file        = forms.FileField(required=False)

def haplotype_handler(request):
    if request.method == 'POST':
        form = HaplotypeForm(request.POST, request.FILES)
        if form.is_valid():
            # submission validation and error reporting
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
                return HttpResponseRedirect(reverse('haplotype'))

            h = Haplotyping(in_data=content)
            h.save()

            celery_async = process_haplotypes.delay(h.id)

            return HttpResponseRedirect('result/%d/' % h.id)
        else:
            return HttpResponse('form is not valid')

    form = HaplotypeForm()
    return render_to_response('mthaplotype/index.html',
                              {'form': form})


def hap_result(request, h_id):

    hlist = Haplotyping.objects.filter(id=h_id)

    template_data = {'id': h_id}
    if len(hlist) != 1:
        template_data['problems'] = "That result could not be found"
    else:
        h = hlist[0]
        if h.completed:
            if h.success:
                template_data['result'] = h.out_data
            else:
                template_data['problems'] = h.problems

    return render_to_response('mthaplotype/mthaplotype_results.html',
                              template_data)
