"""A simplistic wizard for z3c.form that keeps previously entered
values in hidden form elements.
"""

from zope import schema
from zope.app.pagetemplate import viewpagetemplatefile
from z3c.form import button, field, form
import z3c.form.interfaces

from collective.singing import MessageFactory as _
from collective.singing.browser import utils

class Step(utils.OverridableTemplate, form.Form):
    index = viewpagetemplatefile.ViewPageTemplateFile('wizard-step.pt')
    subforms = ()
    label = u""
    description = u""
    ignoreContext = True

    def __init__(self, context, request, parent):
        super(Step, self).__init__(context, request)
        self.parent = parent

class Wizard(utils.OverridableTemplate, form.Form):

    success_message = _(u"Information submitted successfully.")
    errors_message = _(u"There were errors.")

    index = viewpagetemplatefile.ViewPageTemplateFile('wizard.pt')
    finished = False
    steps = () # Set this to be form classes
    label = u""
    description = u""
    ignoreContext = True

    fields = field.Fields(schema.Int(__name__='step', default=-1))

    def update(self):
        self.updateWidgets()
        self.before_steps = []
        self.current_step = None
        self.current_index = int(self.widgets['step'].value)

        # Don't attempt to extract from the current step if we're
        # viewing the form for the first time
        boot = False
        if self.current_index == -1:
            self.current_index = 0
            boot = True

        self.update_steps()
        
        # If we're viewing the form for the first time, let's set the
        # step to 0
        if boot:
            self.widgets['step'].value = str(0)

        # Hide all widgets from previous steps
        self._hide_widgets()
        self.widgets['step'].mode = z3c.form.interfaces.HIDDEN_MODE

        self.updateActions()
        self.actions.execute()

    def _hide_widgets(self):
        for step in self.before_steps:
            for widget in step.widgets.values():
                widget.mode = z3c.form.interfaces.HIDDEN_MODE

    def update_steps(self):
        self.before_steps = []
        for index in range(self.current_index):
            step = self.steps[index](self.context, self.request, self)
            step.update()
            self.before_steps.append(step)
            
        self.current_step = self.steps[self.current_index](
            self.context, self.request, self)
        self.current_step.update()

    def is_last_step(self):
        return len(self.before_steps) == len(self.steps) - 1

    @button.buttonAndHandler(_(u'Proceed'),
                             name='proceed',
                             condition=lambda form:not form.is_last_step())
    def handle_proceed(self, action):
        data, errors = self.current_step.extractData()
        if errors:
            self.status = self.errors_message
        else:
            self.current_index = current_index = self.current_index + 1
            self.widgets['step'].value = current_index
            self.update_steps()
            self._hide_widgets()

            # Proceed can change the conditions for the finish button,
            # so we need to reconstruct the button actions, since we
            # do not redirect.
            self.updateActions()

    @button.buttonAndHandler(_(u'Finish'),
                             name='finish',
                             condition=lambda form:form.is_last_step())
    def handle_finish(self, action):
        data, errors = self.current_step.extractData()
        if errors:
            self.status = self.errors_message
            return
        else:
            self.status = self.success_message
            self.finished = True

        data, errors = self.extractData()
        self.finish(data)

    def extractData(self):
        steps = self.before_steps + [self.current_step]
        return utils.extract_data_prefixed(steps)

    def finish(self, data):
        raise NotImplementedError
