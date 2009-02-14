from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from types import IntType

from oldowan.mitomotifs.polymorphism import Polymorphism as Poly


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


class Entry(models.Model):
    
    name = models.TextField()
    
    objects = QuerySetManager()
        
    class QuerySet(QuerySet):
    
        def with_polymorphism(self, p):
            if not isinstance(p, Polymorphism):
                raise TypeError, "argument must be a Polymorphism instance"
            if p.id is None:
                try:
                    p = Polymorphism.objects.get({'position'  :p.position, 
                                                  'insert'    :p.insert,
                                                  'value'     :p.value,
                                                  'reference' :p.reference})
                except ObjectDoesNotExist:
                    # if polymorphism is not in the db, exclude everything
                    # if the polymorphism is not in the db, no sequence has it
                    return self.none()
            return self.filter(sequences__polymorphisms__id = p.id)

        def not_polymorphism(self, p):
            if not isinstance(p, Polymorphism):
                raise TypeError, "argument must be a Polymorphism instance"
            if p.id is None:
                try:
                    p = Polymorphism.objects.get({'position'  :p.position, 
                                                  'insert'    :p.insert,
                                                  'value'     :p.value,
                                                  'reference' :p.reference})
                except ObjectDoesNotExist:
                    # if polymorphism is not in the db, just return the entering QuerySet
                    # if the polymorphism is not in the db, no sequence has it
                    return self
            return self.exclude(sequences__polymorphisms__id = p.id)
            
        def in_range(self, start, end):
            if not all([isinstance(start, IntType), isinstance(end, IntType)]):
                raise TypeError, "both arguments must be integers"
            return self.filter(sequences__start__lte=start).filter(sequences__end__gte=end).distinct()

    def __unicode__(self):
        return "%s" % self.name


class Sequence(models.Model):

    value           = models.TextField()
    chromosome      = models.CharField(max_length=2)
    start           = models.IntegerField()
    end             = models.IntegerField()
    polymorphisms   = models.ManyToManyField(Polymorphism, related_name='sequences')
    entry           = models.ForeignKey(Entry, related_name='sequences')
    
    objects = QuerySetManager()
        
    class QuerySet(QuerySet):
    
        def with_polymorphism(self, p):
            if not isinstance(p, Polymorphism):
                raise TypeError, "argument must be a Polymorphism instance"
            if p.id is None:
                try:
                    p = Polymorphism.objects.get({'position'  :p.position, 
                                                  'insert'    :p.insert,
                                                  'value'     :p.value,
                                                  'reference' :p.reference})
                except ObjectDoesNotExist:
                    # if polymorphism is not in the db, exclude everything
                    # if the polymorphism is not in the db, no sequence has it
                    return self.none()
            return self.filter(polymorphisms__id = p.id)

        def not_polymorphism(self, p):
            if not isinstance(p, Polymorphism):
                raise TypeError, "argument must be a Polymorphism instance"
            if p.id is None:
                try:
                    p = Polymorphism.objects.get({'position'  :p.position, 
                                                  'insert'    :p.insert,
                                                  'value'     :p.value,
                                                  'reference' :p.reference})
                except ObjectDoesNotExist:
                    # if polymorphism is not in the db, just return the entering QuerySet
                    # if the polymorphism is not in the db, no sequence has it
                    return self
            return self.exclude(polymorphisms__id = p.id)

        def in_range(self, start, end):
            if not all([isinstance(start, IntType), isinstance(end, IntType)]):
                raise TypeError, "both arguments must be integers"
            return self.filter(start__lte=start).filter(end__gte=end).distinct()

    def __unicode__(self):
        return "%s:%i-%i:%s" % (self.chromosome, self.start, self.end, self.value[:10])
        
    def __cmp__(self, other):
        if self.value == other.value:
            return 0
        elif self.value > other.value:
            return 1
        return -1

    


