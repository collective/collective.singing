import datetime
import persistent
from zope import interface
from zope import schema
import zope.interface.interface

import collective.singing.interfaces
from collective.singing import MessageFactory as _

class ISubjectsCollectorBase(collective.singing.interfaces.ICollector):
    pass

class IFilteredSubjectsCollectorBase(collective.singing.interfaces.ICollector):
    pass

class SubjectsCollectorBase(persistent.Persistent):
    """A template class that allows you to create a simple collector
    that presents one field with a vocabulary to the user.

    You can provide the vocabulary and the title of the field by
    overriding methods and attributes.
    """
    interface.implements(ISubjectsCollectorBase)

    title = _(u"Subjects collector")

    field_name = 'subjects'
    field_title = _(u"Subjects")

    def __init__(self, id, title):
        self.id = id
        self.title = title
        super(SubjectsCollectorBase, self).__init__()

    @property
    def full_schema(self):
        vocabulary = self.vocabulary()
        field = schema.Set(
            __name__=self.field_name,
            title=self.field_title,
            value_type=schema.Choice(vocabulary=vocabulary))

        interface.directlyProvides(
            field, collective.singing.interfaces.IDynamicVocabularyCollection)

        return zope.interface.interface.InterfaceClass(
            'Schema',
            bases=(collective.singing.interfaces.ICollectorSchema,),
            attrs={field.__name__: field})

    @property
    def schema(self):
        vocabulary = self._vocabulary()
        field = schema.Set(
            __name__=self.field_name,
            title=self.field_title,
            value_type=schema.Choice(vocabulary=vocabulary))

        interface.directlyProvides(
            field, collective.singing.interfaces.IDynamicVocabularyCollection)

        return zope.interface.interface.InterfaceClass(
            'Schema',
            bases=(collective.singing.interfaces.ICollectorSchema,),
            attrs={field.__name__: field})

    def get_items(self, cue=None, subscription=None):
        if subscription is not None:
            data = subscription.collector_data.get(
                self.field_name, set())
        else:
            data = set()

        return self.get_items_for_selection(cue, data), self.now()

    def now(self):
        return datetime.datetime.now()
    
    def _vocabulary(self):
        return self.vocabulary()

    def get_items_for_selection(self, cue, data):
        """Override this method and return a list of items that match
        the set of choices from the vocabulary given in ``data``.  Do
        not return items that are older than ``cue``.
        """
        raise NotImplementedError()

    def vocabulary(self):
        """Override this method and return a zope.schema.vocabulary
        vocabulary.
        """
        raise NotImplementedError()

class FilteredSubjectsCollectorBase(SubjectsCollectorBase):
    interface.implements(IFilteredSubjectsCollectorBase)

    filtered_items = []

    def _vocabulary(self):
        if self.filtered_items:
            return zope.schema.vocabulary.SimpleVocabulary(
                [t for t in self.vocabulary()
                 if t.token in self.filtered_items])
        else:
            return self.vocabulary()

