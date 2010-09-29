from django.db import models

class Haplotyping(models.Model):
    in_data = models.TextField()
    out_data = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)
    success = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    problems = models.TextField(default='')

