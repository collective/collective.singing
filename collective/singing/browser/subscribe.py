import datetime

import zope.schema.interfaces
import zope.schema.vocabulary
import zope.publisher.browser
from zope.app.pagetemplate import viewpagetemplatefile
import z3c.form.interfaces
from z3c.form import field
from z3c.form import form
import z3c.form.browser.checkbox

from collective.singing import interfaces
from collective.singing import subscribe
from collective.singing import MessageFactory as _
from collective.singing import message
from collective.singing.browser import utils
from collective.singing.browser import wizard

class Terms(zope.schema.vocabulary.SimpleVocabulary):
    zope.interface.implements(z3c.form.interfaces.ITerms)

    def getValue(self, token):
        return self.getTermByToken(token).value

class ChooseFormatStep(wizard.Step):
    prefix = 'format'

    @property
    def fields(self):
        composers = self.context.composers
        terms = Terms([
            zope.schema.vocabulary.SimpleTerm(
                name, title=composers[name].title)
            for name in sorted(composers.keys())
            ])

        format = zope.schema.Choice(
            __name__='format',
            title=_(u'Format'),
            vocabulary=terms)

        return field.Fields(format)

class SubscribeStep(wizard.Step):
    prefix = 'composer'

    @property
    def fields(self):
        format = self.parent.format()
        return field.Fields(self.context.composers[format].schema)

    def update(self):
        self.subforms = (CollectorDataForm(self.context, self.request),)
        self.subforms[0].update()
        super(SubscribeStep, self).update()

    def extractData(self):
        sub_data, sub_errors = utils.extract_data_prefixed(self.subforms)
        data, errors = self.widgets.extract()
        data.update(sub_data)
        errors = errors + sub_errors
        return data, errors

class CollectorDataForm(utils.OverridableTemplate, form.Form):
    """A subform for the collector specific data.
    """
    index = viewpagetemplatefile.ViewPageTemplateFile('sub-edit.pt')
    prefix = 'collector'
    label = _(u"Filters")
    ignoreContext = True
    
    @property
    def fields(self):
        collector = self.context.collector
        if collector is not None:
            return field.Fields(collector.schema)
        else:
            return field.Fields()

class Subscribe(wizard.Wizard):
    """The add subscription wizard.

    ``context`` is required to be of type ``IChannel``.
    """
    steps = ChooseFormatStep, SubscribeStep
    label = _(u"Fill in the information below to subscribe.")
    success_message = _(
        u"Thanks for your subscription; "
        u"we sent you a message for confirmation.")

    @property 
    def description(self):
        if hasattr(self.context, 'description'):
            return self.context.description
    
    def format(self):
        return self.before_steps[0].widgets.extract()[0]['format']

    def update_steps(self):
        super(Subscribe, self).update_steps()

        if len(self.before_steps) == 0:
            # If there's only one format, we'll skip the first step
            formats = self.context.composers.keys()
            if len(formats) == 1:
                self.current_index += 1
                format_key = '%s.widgets.%s' % (self.current_step.prefix,
                                                'format')
                self.request.form[format_key] = [formats[0]]
                super(Subscribe, self).update_steps()

    def finish(self, data):
        comp_data = {}
        coll_data = {}
        for key, value in data.items():
            name = key.split('.')[-1]
            if key.startswith('composer.collector.'):
                coll_data[name] = value
            elif key.startswith('composer.'):
                comp_data[name] = value

        # Create the data necessary to create a subscription:
        secret = self._secret(comp_data, self.request)
        metadata = dict(format=self.format(),
                        date=datetime.datetime.now(),
                        pending=True)

        try:
            subscription = self.context.subscriptions.add_subscription(
                self.context, secret, comp_data, coll_data, metadata)
        except ValueError:
            self.status = _(u"You are already subscribed.")
            return

        # Ask the composer to render a confirmation message
        composer = self.context.composers[self.format()]
        msg = composer.render_confirmation(subscription)
        status, status_msg = message.dispatch(msg)
        if status != u'sent':
            raise RuntimeError(
                "There was an error with sending your e-mail.  Please try "
                "again later.")

    def _secret(self, data, request):
        """Convenience method for looking up secrets.
        """
        composer = self.context.composers[self.format()]
        return subscribe.secret(self.context, composer, data, self.request)

class Unsubscribe(utils.OverridableTemplate,
                  zope.publisher.browser.BrowserView):
    def index(self):
        return u"<p>You have been unsubscribed.</p>"

    def __call__(self):
        secret = self.request.form['secret']
        for subscription in self.context.subscriptions.query(secret=secret):
            self.context.subscriptions.remove_subscription(subscription)
        return self.template()
