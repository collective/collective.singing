import os

from zope import interface
from zope import component
import zope.pagetemplate.interfaces
import z3c.form.interfaces
import z3c.form.widget

def extract_data_prefixed(subforms):
    data, errors = {}, []
    for form in subforms:
        subform_data, subform_errors = form.extractData()
        d = {}
        for key, value in subform_data.items():
            newkey = '%s.%s' % (form.prefix, key)
            assert newkey not in d, "Name clash: %s" % newkey
            d[newkey] = value
        data.update(d)
        errors.extend(subform_errors)
    return data, tuple(errors)

class OverridableTemplate(object):
    """Subclasses of this class must set the template they want to use
    as the default template as the ``index`` attribute, not the
    ``template`` attribute that's normally used for forms.
    
    Users of this package may override the template used by one of the
    forms by using the ``browser`` directive and specifying their own
    template.
    """
    @property
    def template(self):
        return self.index
