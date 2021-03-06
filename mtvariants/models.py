from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from types import IntType

from oldowan.polymorphism import Polymorphism as Poly


# QuerySetManager information from http://www.djangosnippets.org/snippets/734/
class QuerySetManager(models.Manager):

    def __getattr__(self, name):
        return getattr(self.get_query_set(), name)

    def get_query_set(self):
        return self.model.QuerySet(self.model)


# ImmutableModel information from 
# http://www.fairviewcomputing.com/blog/2008/06/22/immutable-django-model-fields/
class ImmutableModel(models.Model):
    immutable_fields = []
    class Meta:
        abstract = True

    def __setattr__(self, name, value):
        if name == 'immutable_fields' or name in self.immutable_fields:
            if getattr(self, name, None) is not None:
                raise AttributeError, "'%s' is immutable" % name
        super(ImmutableModel, self).__setattr__(name, value)


class Polymorphism(ImmutableModel, Poly):

    position    = models.IntegerField(editable=False)
    insert      = models.IntegerField(editable=False)
    value       = models.CharField(max_length=1, editable=False)
    reference   = models.CharField(max_length=1, editable=False)
    
    objects = QuerySetManager()

    immutable_fields = ['position', 'insert', 'value', 'reference']
        
    def save(self, **kwargs):
        """override save to ensure unique db entries""" 
        if self.id is None:
            # try to find a pre-existing identical polymorphism 
            like_me = Polymorphism.objects.filter(position =self.position, 
                                                  insert   =self.insert, 
                                                  value    =self.value, 
                                                  reference=self.reference)[:1]
            if len(like_me) == 1:
                # if I find a pre-existing polymorphism, take it's id
                self.id = like_me[0].id
            else:
                # otherwise, save new polymorphism to db
                super(Polymorphism, self).save(**kwargs)
        else:
            # if I already have an id, I am already in the db
            # do nothing - thereby enforcing non-modifiability of db polymorphisms 
            # (?? - are there other routes into the db?)
            return
                
    def __unicode__(self):
        if self.insert == 0:
            if self.value == '-':
                return u'%s%s' % (self.position, 'd')
            else:
                return u'%s%s' % (self.position, self.value)
        return u'%s.%s%s' % (self.position, self.insert, self.value)

    class Meta:
        unique_together = (("position", "insert", "value", "reference"),)

    class QuerySet(QuerySet):
    
        def in_range(self, start, end):
            if not all([isinstance(start, IntType), isinstance(end, IntType)]):
                raise TypeError, "both arguments must be integers"
            return self.filter(position__gte=start).filter(position__lte=end).distinct()


class Entry(models.Model):
    
    name = models.TextField()
    
    objects = QuerySetManager()

    def __unicode__(self):
        return "%s" % self.name

    class QuerySet(QuerySet):
    
        @staticmethod
        def __validate_polys__(polys):
            # accept either collection or single object,
            # first, if the argument is not a collection, make it a list
            if not hasattr(polys, '__contains__'):
                polys = [polys]
            # make sure that all the arguments are Polymorphisms
            for p in polys:
                if not isinstance(p, Polymorphism):
                    raise TypeError, "argument must be a Polymorphism instance"
            # next, for any polymorphisms that did not come out of the database
            # (i.e. no id),
            # grab their ids if they are in the database, otherwise drop them
            # (no point in searching the database for entries with or w/o polys
            #  that aren't in the db to start with!)
            for p in polys:
                if p.id is None:
                    try:
                        x = Polymorphism.objects.get(position   = p.position, 
                                                     insert     = p.insert,
                                                     value      = p.value,
                                                     reference  = p.reference)
                        p.id = x.id
                    except ObjectDoesNotExist:
                        # if polymorphism is not in the db, don't bother searching
                        # for it
                        polys.remove(p)
            return polys

        def with_polymorphisms(self, polys):
            polys = self.__validate_polys__(polys)
            if len(polys) == 0:
                return self.none()
            poly_ids = list(p.id for p in polys)
            return self.filter(sequences__polymorphisms__in = poly_ids)

        def only_polymorphisms(self, polys, range_start=None, range_end=None):
            polys = self.__validate_polys__(polys)
            if len(polys) == 0:
                return self.none()
            other_poly_ids = []
            if range_start is not None and range_end is not None:
                if range_start < range_end:
                    other_poly_ids = list(x['id'] for x in 
                            Polymorphism.objects.in_range(range_start, range_end).values('id'))
                else:
                    raise ArgumentError, "range start is not less than end"
            else:
                # otherwise, all object primary id's are auto-generated and sequential,
                # so the list of all primary keys is just 1 to total number
                # (+1 in the python range construct)
                other_poly_ids = list(x['id'] for x in Polymorphism.objects.values('id'))
            # remove the ids that I want
            for p in polys:
                if p.id in other_poly_ids:
                    other_poly_ids.remove(p.id)

            desired_poly_ids = list(p.id for p in polys)
            # first, must have the polymorphim given
            qset = self.filter(sequences__polymorphisms__in = desired_poly_ids)
            # then exclude sequences with any other polymorphisms
            return qset.exclude(sequences__polymorphisms__in = other_poly_ids).distinct()

        def not_polymorphisms(self, polys):
            polys = self.__validate_polys__(polys)
            if len(polys) == 0:
                return self.all()
            poly_ids = list(p.id for p in polys)
            return self.exclude(sequences__polymorphisms__in = poly_ids)
            
        def in_range(self, start, end):
            if not all([isinstance(start, IntType), isinstance(end, IntType)]):
                raise TypeError, "both arguments must be integers"
            return self.filter(sequences__start__lte=start).filter(sequences__end__gte=end).distinct()


class Sequence(models.Model):

    value           = models.TextField()
    chromosome      = models.CharField(max_length=2)
    start           = models.IntegerField()
    end             = models.IntegerField()
    polymorphisms   = models.ManyToManyField(Polymorphism, related_name='sequences')
    entry           = models.ForeignKey(Entry, related_name='sequences')
    
    def __unicode__(self):
        return "%s:%i-%i:%s" % (self.chromosome, self.start, self.end, self.value[:10])
        
    def __cmp__(self, other):
        if self.value == other.value:
            return 0
        elif self.value > other.value:
            return 1
        return -1

    


