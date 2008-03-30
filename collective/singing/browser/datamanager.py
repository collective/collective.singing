import zope.component
import zope.schema
import zope.interface

import z3c.form.datamanager

class SetToDictField(z3c.form.datamanager.AttributeField):
    """Puts a Set into a Dict field."""

    key_attr = 'name'
        
    def get(self):
        """See z3c.form.interfaces.IDataManager"""
        # get the right adapter or context
        context = self.context
        if self.field.interface is not None:
            context = self.field.interface(context)
        return getattr(context, self.field.__name__).values()

    def set(self, value):
        """See z3c.form.interfaces.IDataManager"""
        if self.field.readonly:
            raise TypeError("Can't set values on read-only fields "
                            "(name=%s, class=%s.%s)"
                            % (self.field.__name__,
                               self.context.__class__.__module__,
                               self.context.__class__.__name__))
        # get the right adapter or context
        context = self.context
        if self.field.interface is not None:
            context = self.field.interface(context)
        dict = {}
        for item in value:
            dict[getattr(item, self.key_attr)] = item          
        setattr(context, self.field.__name__, dict)
