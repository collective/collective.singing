from zope import component
from zope import interface
from zope import schema

import z3c.form 
from collective.singing.interfaces import IDynamicVocabularyCollection

class DynamicVocabularyCollSeqConverter(
    z3c.form.converter.CollectionSequenceDataConverter):
    component.adapts(
        IDynamicVocabularyCollection, z3c.form.interfaces.ISequenceWidget)

    def toWidgetValue(self, value):
        """Convert from Python bool to HTML representation."""
        widget = self.widget
        if not widget.terms:
            widget.updateTerms()
        return [widget.terms.getTerm(entry).token
                for entry in value if entry in widget.terms]
