import datetime

from zope import component
from zope import schema
import zope.i18n.interfaces
import zope.schema.interfaces
import zope.schema.vocabulary
import zope.publisher.browser
from zope.app.pagetemplate import viewpagetemplatefile
import z3c.form.interfaces
from z3c.form import button
from z3c.form import field
from z3c.form import form
import z3c.form.browser.checkbox

from collective.singing import interfaces
from collective.singing import subscribe
from collective.singing import MessageFactory as _
from collective.singing import message
from collective.singing.browser import utils
from collective.singing.browser import wizard
from collective.singing.channel import channel_lookup

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

    def _show_forgot_button(self):
        btn = self.buttons['forgot']
        form = self.request.form
        button_name = '%s.buttons.%s' % (self.prefix, btn.__name__)
        return (self.parent.status == self.parent.already_subscribed_message or
                form.get(button_name))

    @button.buttonAndHandler(
        _('Send my subscription details'),
        name='forgot',
        condition=lambda form:form._show_forgot_button())
    def handle_forgot(self, action):
        data, errors = self.parent.extractData()
        if errors:
            self.parent.status = form.EditForm.formErrorsMessage
            return

        comp_data = {}
        for key, value in data.items():
            name = key.split('.')[-1]
            if key.startswith('composer.'):
                comp_data[name] = value

        secret = self.parent._secret(comp_data, self.request)
        subs = self.context.subscriptions
        subscriptions = subs.query(secret=secret)
        if len(subscriptions) == 0:
            self.status = _(u"Your subscription isn't known to us.")
        else:
            subscription = tuple(subscriptions)[0]
            composer = self.context.composers[self.parent.format()]
            msg = composer.render_forgot_secret(subscription)
            status, status_msg = message.dispatch(msg)
            if status != u'sent':
                raise RuntimeError(
                    "There was an error with sending your e-mail.  Please try "
                    "again later.")
            else:
                self.parent.status = _(u"Thanks.  We sent you a message.")

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
    already_subscribed_message = _(u"You are already subscribed.")

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

        # We assume here that the language of the request is the
        # desired language of the subscription:
        pl = component.queryAdapter(
            self.request, zope.i18n.interfaces.IUserPreferredLanguages)
        if pl is not None:
            metadata['languages'] = pl.getPreferredLanguages()

        try:
            subscription = self.context.subscriptions.add_subscription(
                self.context, secret, comp_data, coll_data, metadata)
        except ValueError:
            self.status = self.already_subscribed_message
            self.finished = False
            self.current_step.updateActions()
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

class ForgotSecret(utils.OverridableTemplate, form.Form):
    ignoreContext = True
    index = viewpagetemplatefile.ViewPageTemplateFile('form.pt')

    label = _(u"Retrieve a link to your personalized subscription settings")
    
    successMessage = _(u"Thanks.  We sent you a message.")
    notKnownMessage = _(u"Your subscription isn't known to us.")
    
    fields = field.Fields(
        schema.TextLine(
            __name__='address',
            title=_(u"Address"),
            description=_(u"The address you're already subscribed with"),
            ),
        )

    @button.buttonAndHandler(_('Send'), name='send')
    def handle_send(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.EditForm.formErrorsMessage
            return

        address = data['address'].lower()
        for channel in channel_lookup():
            subscriptions = channel.subscriptions.query(key=address)
            if len(subscriptions):
                subscription = tuple(subscriptions)[0]
                composer = channel.composers[subscription.metadata['format']]
                msg = composer.render_forgot_secret(subscription)
                status, status_msg = message.dispatch(msg)
                if status != u'sent':
                    raise RuntimeError(
                        "There was an error with sending your e-mail.  Please "
                        "try again later.")
                self.status = self.successMessage
                break
        else:
            self.status = self.notKnownMessage
