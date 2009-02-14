import unittest
from mtvariants.models import Entry, Sequence, Polymorphism

class EntryQueriesTestCase(unittest.TestCase):
    def setUp(self):
        self.e_a, created = Entry.objects.get_or_create(name='a')
        self.e_b, created = Entry.objects.get_or_create(name='b')
        self.e_c, created = Entry.objects.get_or_create(name='c')
        self.e_d, created = Entry.objects.get_or_create(name='d')
    
        self.a, created = Sequence.objects.get_or_create(chromosome='mt', 
                                                         start=1, 
                                                         end=10, 
                                                         value='AAAAAAAAAA', 
                                                         entry=self.e_a)
        self.b, created = Sequence.objects.get_or_create(chromosome='mt', 
                                                         start=1, 
                                                         end=15, 
                                                         value='AAGAACAAAAAAAAA', 
                                                         entry=self.e_b)
        self.c, created = Sequence.objects.get_or_create(chromosome='mt', 
                                                         start=1, 
                                                         end=10, 
                                                         value='AAGAAAAATA', 
                                                         entry=self.e_c)
        self.d, created = Sequence.objects.get_or_create(chromosome='mt', 
                                                         start=1, 
                                                         end=10, 
                                                         value='GAAAAAAAAA', 
                                                         entry=self.e_d)
        self.e, created = Sequence.objects.get_or_create(chromosome='mt', 
                                                         start=21, 
                                                         end=30, 
                                                         value='AAAAAAAAAA', 
                                                         entry=self.e_d)

        self.p1, created = Polymorphism.objects.get_or_create(position=1, 
                                                              insert=0, 
                                                              value='G', 
                                                              reference='A')
        self.p2, created = Polymorphism.objects.get_or_create(position=3, 
                                                              insert=0, 
                                                              value='G', 
                                                              reference='A')
        self.p3, created = Polymorphism.objects.get_or_create(position=6, 
                                                              insert=0, 
                                                              value='C', 
                                                              reference='A')
        self.p4, created = Polymorphism.objects.get_or_create(position=9, 
                                                              insert=0, 
                                                              value='T', 
                                                              reference='A')
    
        self.b.polymorphisms = [self.p2, self.p3]
        self.c.polymorphisms = [self.p2, self.p4]
        self.d.polymorphisms = [self.p1]

    def testWithPolymorphism(self):
        """Find all entries having polymorphism X"""
        result = Entry.objects.with_polymorphism(self.p2)
        self.assert_(self.e_b in result)
        self.assert_(self.e_c in result)

    def testNotPolymorphism(self):
        """Find all entries having polymorphism X but not polymorphism Y"""
        result = Entry.objects.with_polymorphism(self.p2).not_polymorphism(self.p4)
        self.assert_(self.e_b in result)
        self.assert_(self.e_c not in result)

    def testInRange(self):
        """Find all entries covering positions A-B"""
        result = Entry.objects.in_range(1,10)
        self.assert_(self.e_a in result)
        self.assert_(self.e_b in result)
        self.assert_(self.e_c in result)
        self.assert_(self.e_d in result)

    def testMultipleInRange(self):
        """Find all entries covering positions A-B and C-D"""
        result = Entry.objects.in_range(1,10).in_range(21,30)
        self.assert_(self.e_a not in result)
        self.assert_(self.e_b not in result)
        self.assert_(self.e_c not in result)
        self.assert_(self.e_d in result)

    def testInRangeWithPolymorphism(self):
        """Find all entries covering positions A-B with polymorphism X"""
        result = Entry.objects.in_range(1,15).with_polymorphism(self.p2)
        self.assert_(self.e_b in result)
        self.assertEquals(len(result), 1)


