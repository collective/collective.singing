import z3c.form 
from zope import component
from zope import interface
from zope import schema
from collective.singing.interfaces import IDynamicVocabularyCollection

class CollectionSequenceDataConverter(z3c.form.converter.BaseDataConverter):
    """A special converter between collections and sequence widgets."""

    component.adapts(
        IDynamicVocabularyCollection, z3c.form.interfaces.ISequenceWidget)

    def toWidgetValue(self, value):
        """Convert from Python bool to HTML representation."""
        widget = self.widget
        if not widget.terms:
            widget.updateTerms()
        return [widget.terms.getTerm(entry).token
                for entry in value if widget.terms.__contains__(entry)]

    def toFieldValue(self, value):
        """See interfaces.IDataConverter"""
        widget = self.widget
        if not widget.terms:
            widget.updateTerms()
        collectionType = self.field._type
        if isinstance(collectionType, tuple):
            collectionType = collectionType[-1]
        return collectionType([widget.terms.getValue(token) for token in value])


        
