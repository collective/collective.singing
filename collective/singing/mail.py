import formatter
import htmllib
import quopri
import StringIO
import traceback
import email 

from email.Header import Header
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import formatdate

from zope import interface
from zope import component
import zope.sendmail.interfaces

from collective.singing import interfaces

def create_html_mail(subject, html, text=None, from_addr=None, to_addr=None,
                     encoding='UTF-8'):
    """Create a mime-message that will render HTML in popular
    MUAs, text in better ones.
    """
    html = html.encode(encoding)
    if text is None:
        # Produce an approximate textual rendering of the HTML string,
        # unless you have been given a better version as an argument
        textout = StringIO.StringIO()
        formtext = formatter.AbstractFormatter(formatter.DumbWriter(textout))
        parser = htmllib.HTMLParser(formtext)
        parser.feed(html)
        parser.close()
        text = textout.getvalue()
        del textout, formtext, parser
    else:
        text = text.encode(encoding)
        
    # if we would like to include images in future, there should 
    # probably be 'related' instead of 'mixed'
    msg = MIMEMultipart('mixed')
    # maybe later :)  msg['From'] = Header("%s <%s>" % (send_from_name, send_from), encoding)
    msg['Subject'] = Header(subject, encoding)
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate(localtime=True)
    msg["Message-ID"]=email.Utils.make_msgid()
    msg.preamble = 'This is a multi-part message in MIME format.'

    alternatives = MIMEMultipart('alternative')
    msg.attach(alternatives)
    alternatives.attach( MIMEText(text, 'plain', _charset=encoding) )
    alternatives.attach( MIMEText(html, 'html',  _charset=encoding) )

    return msg

class Dispatch(object):
    """An IDispatcher registered for ``email.message.Message`` that'll
    send e-mails using ``zope.sendmail``.

    To send a test e-mail, we'll first create an e-mail object:

      >>> message = email.Message.Message()
      >>> message['From'] = 'daniel@testingunderground.com'
      >>> message['To'] = 'plone-users@lists.sourceforge.net'
      >>> message.set_payload('Hello, Plone users!')

    ``Dispatch`` adapts ``email.Message.Message``:
     
      >>> dispatcher = Dispatch(message)
     
    Sending a message without a configured ``IMailDelivery`` will fail:
     
      >>> dispatcher() # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      ComponentLookupError: (<InterfaceClass zope.sendmail.interfaces.IMailDelivery>, '')

    Let's provide our own ``IMailDelivery`` and see what happens:

      >>> class MyMailDelivery(object):
      ...     interface.implements(zope.sendmail.interfaces.IMailDelivery)
      ...
      ...     def send(self, from_, to, message):
      ...         print 'From: ', from_
      ...         print 'To: ', to
      ...         print 'Message follows:'
      ...         print message

      >>> component.provideUtility(MyMailDelivery())
      >>> dispatcher()
      From:  daniel@testingunderground.com
      To:  plone-users@lists.sourceforge.net
      Message follows:
      From: daniel@testingunderground.com
      To: plone-users@lists.sourceforge.net
      <BLANKLINE>
      Hello, Plone users!
      (u'sent', None)

    Note that the last line is the return value.

    If the delivery fails, we'll get a return value with u'error' as
    the first element.

      >>> class MyException(Exception):
      ...     pass
      >>> class MyFailingMailDelivery(object):
      ...     interface.implements(zope.sendmail.interfaces.IMailDelivery)
      ...
      ...     def send(self, from_, to, message):
      ...         raise MyException('This is a test')
      >>> component.provideUtility(MyFailingMailDelivery())
      >>> status, message = dispatcher()
      >>> status
      u'error'
      >>> print message # doctest: +NORMALIZE_WHITESPACE
      Traceback (most recent call last):
      MyException: This is a test
    """
    
    interface.implements(interfaces.IDispatch)
    component.adapts(email.Message.Message)

    def __init__(self, message):
        self.message = message

    def __call__(self):
        msg = self.message
        delivery = component.getUtility(zope.sendmail.interfaces.IMailDelivery)
        try:
            delivery.send(msg['From'], msg['To'], msg.as_string())
        except Exception, e:
            # TODO: log
            return u'error', traceback.format_exc(e)
        else:
            return u'sent', None
