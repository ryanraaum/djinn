from oldowan.mitotype import prevalidate_submission
from celery.decorators import task
from mthaplotype.models import Haplotyping

import subprocess
import tempfile

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
        h.completed = True
        in_data = h.in_data.encode('ascii', 'ignore')

        vi = prevalidate_submission(in_data)
        if vi.valid:
            infile = tempfile.NamedTemporaryFile()
            outfile = tempfile.TemporaryFile()

            infile.write(in_data)
            infile.flush()

            p = subprocess.Popen(['mitotype', '-f', infile.name], stdout=outfile)
            exit_status = p.wait()

            # rewind the outfile
            outfile.seek(0)
            results = outfile.read()

            infile.close()
            outfile.close()
            
            if exit_status == 0:
                h.success = True
                h.out_data = results
            else:
                h.success = False
                h.problems = results

            h.save()
            return True
        else: # not valid
            h.success = False
            h.completed = True
            h.problems = vi.problem
            h.save()
            return False

