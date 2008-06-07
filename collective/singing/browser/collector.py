import z3c.form.form
import z3c.form.field
from zope.app.pagetemplate import viewpagetemplatefile

class EditFilteredSubjectsCollector(z3c.form.form.EditForm):
    template = viewpagetemplatefile.ViewPageTemplateFile('form.pt')

    @property
    def fields(self):
        schema = self.context.schema
        field = schema[self.context.field_name]
        field.__name__ = 'filtered_items'
        field.value_type.vocabulary = self.context.vocabulary()
        field.interface = None
        return z3c.form.field.Fields(schema)
