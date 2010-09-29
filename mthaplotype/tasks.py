from oldowan.mitotype import HVRMatcher
from oldowan.mitotype import prevalidate_submission
from celery.decorators import task
from mthaplotype.models import Haplotyping

#----------------------------------------------------------------------------#
# PROCESSORS
#----------------------------------------------------------------------------#

@task
def process_haplotypes(h_id):
    """Process data submitted in seq2sites form"""

    hlist = Haplotyping.objects.filter(id=h_id) 
    if len(hlist) != 1:
        return False
    else:
        h = hlist[0]
        print(h)
        h.completed = True
        in_data = h.in_data.encode('ascii', 'ignore')
        print(in_data)

        vi = prevalidate_submission(in_data)
        if vi.valid:
            HVRM = HVRMatcher()
            results = HVRM.match(in_data, vi)
            result_strings = [str(r) for r in results]
            h.out_data = '\n'.join(result_strings)
            h.success = True
            h.save()
            return True
        else: # not valid
            h.success = False
            h.completed = True
            h.problems = vi.problem
            h.save()
            return False

