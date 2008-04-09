import email.Message
import email.Parser
import formatter
import htmllib
import mimetools
import MimeWriter
import quopri
import StringIO
import traceback

from zope import interface
from zope import component
import zope.sendmail.interfaces

from collective.singing import interfaces

def header(text, encoding):
    assert isinstance(text, unicode)
    
    try:
        return text.encode()
    except UnicodeEncodeError:
        encoded_subj = quopri.encodestring(
            text.encode(encoding), header=True)
        return '=?%s?Q?%s?=' % (encoding.upper(), encoded_subj)

def create_html_mail(subject, html, text=None, from_addr=None, to_addr=None,
                     encoding='UTF-8'):
    """Create a mime-message that will render HTML in popular
    MUAs, text in better ones.

    Ripped from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/67083
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
        
    out = StringIO.StringIO() # output buffer for our message
    htmlin = StringIO.StringIO(html) # input buffer for the HTML
    txtin = StringIO.StringIO(text) # input buffer for the plain text
    writer = MimeWriter.MimeWriter(out)

    # Set up some basic headers.  Place subject here because
    # smtplib.sendmail expects it to be in the message, as relevant
    # RFCs prescribe.
    writer.addheader("Subject", header(subject, encoding))
    writer.addheader("MIME-Version", "1.0")
    if from_addr:
        writer.addheader("From", from_addr)
    if to_addr:
        writer.addheader("To", to_addr)

    # Start the multipart section of the message.
    # Multipart/alternative seems to work better on some MUAs than
    # multipart/mixed.
    writer.startmultipartbody("alternative")
    writer.flushheaders()

    # Make plain text section quoted-printable
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/plain", [("charset", encoding)])
    mimetools.encode(txtin, pout, 'quoted-printable')
    txtin.close()

    # The HTML subpart is quoted-printable, too
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/html", [("charset", encoding)])
    mimetools.encode(htmlin, pout, 'quoted-printable')
    htmlin.close()

    # You're done; close your writer and return the message as a string
    writer.lastpart()
    msg = out.getvalue().encode()
    out.close()

    parser = email.Parser.Parser()
    return parser.parsestr(msg)

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
