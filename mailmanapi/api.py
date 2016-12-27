import os
import json
import shutil
from .utils import parse_boolean, \
                   get_mailinglist, \
                   get_error_code, \
                   get_error_message
from Mailman import Errors, \
                    UserDesc, \
                    MailList, \
                    Utils, \
                    Defaults, \
                    Message, \
                    i18n, \
                    mm_cfg
from bottle import HTTPResponse, \
                   request

_ = i18n._

CWD = os.path.abspath(os.path.dirname(__file__))


def list_lists():
    """Lists existing mailing lists on the server.

    **Method**: GET

    **URI**: /

    Returns a list of dictionaries containing the basic attributes for
    each mailing list that exist on this server.

    **Parameters**:
      * `address` (optional): email address to search for in lists."""

    all_lists = Utils.list_names()
    lists = []

    address = request.query.get('address')
    for listname in all_lists:
        if listname == Defaults.MAILMAN_SITE_LIST:
            continue

        mlist = get_mailinglist(listname, lock=False)

        members = mlist.getMembers()
        if not address or address in members:
            list_values = {
                'listname': listname,
                'archive_private': mlist.archive_private,
                'real_name': mlist.real_name,
                'description': mlist.description,
                'member_count': -1,
                'created': mlist.created_at,
                'owner': mlist.owner
            }

            lists.append(list_values)

    return HTTPResponse(body=json.dumps(lists),
                        content_type='application/json')


def list_attr(listname):
    """Returns basic attributes of specific list.

    **Method**: GET

    **URI**: /<listname>

    Returns a dictionary containing the basic attributes for
    a specific mailing list that exist on this server."""

    lists = []

    try:
        mlist = get_mailinglist(listname, lock=False)
    except Errors.MMUnknownListError, e:
        message = get_error_message(e.__class__.__name__) + ': ' + str(e)
        return HTTPResponse(status=get_error_code(e.__class__.__name__),
                            body=json.dumps({'message': message}),
                            content_type='application/json')
    list_values = {
        'listname': listname,
        'archive_private': mlist.archive_private,
        'real_name': mlist.real_name,
        'description': mlist.description,
        'member_count': len(mlist.getMembers()),
        'created': mlist.created_at,
        'owner': mlist.owner
    }
    lists.append(list_values)
    return HTTPResponse(body=json.dumps(lists),
                        content_type='application/json')


def subscribe(listname):
    """Adds a new subscriber to the list called `<listname>`

    **Method**: PUT

    **URI**: /<listname>/members

    **Parameters**:

      * `address`: email address that is to be subscribed to the list.
      * `fullname`: full name of the person being subscribed to the list.
      * `digest`: if this equals `true`, the new subscriber will receive
        digests instead of every mail sent to the list.

    """
    address = request.forms.get('address')
    fullname = request.forms.get('fullname')
    digest = parse_boolean(request.forms.get('digest'))

    mlist = get_mailinglist(listname, lock=False)
    userdesc = UserDesc.UserDesc(address, fullname, digest=digest)
    message = 'Success'
    status_code = 200
    try:
        mlist.AddMember(userdesc)
    except (Errors.MMSubscribeNeedsConfirmation,
            Errors.MMNeedApproval,
            Errors.MMAlreadyAMember,
            Errors.MembershipIsBanned,
            Errors.MMBadEmailError,
            Errors.MMHostileAddress), e:
        class_name = e.__class__.__name__
        # Don't append error string for MMSubscribeNeedsConfirmation exception.
        if class_name == 'MMSubscribeNeedsConfirmation':
            message = get_error_message(e.__class__.__name__)
        else:
            message = get_error_message(e.__class__.__name__) + ': ' + str(e)
        status_code = get_error_code(e.__class__.__name__)
    finally:
        mlist.Save()
        mlist.Unlock()
    return HTTPResponse(status=status_code,
                        body=json.dumps({'message': message}),
                        content_type='application/json')


def unsubscribe(listname):
    """Unsubscribe an email address from the mailing list.

    **Method**: DELETE

    **URI**: /<listname>/members

    **Parameters**:

      * `address`: email address that is to be unsubscribed from the list

    """
    address = request.forms.get('address')
    mlist = get_mailinglist(listname, lock=False)
    message = 'Success'
    status_code = 200
    try:
        mlist.ApprovedDeleteMember(address, admin_notif=False, userack=True)
    except Errors.NotAMemberError, e:
        message = get_error_message(e.__class__.__name__) + ': ' + str(e)
        status_code = get_error_code(e.__class__.__name__)
    finally:
        mlist.Save()
        mlist.Unlock()
    return HTTPResponse(status=status_code,
                        body=json.dumps({'message': message}),
                        content_type='application/json')


def create_list(listname):
    """Create an email list.

    **Method**: POST

    **URI**: /<listname>

    **Parameters**:

      * `admin`: email of list admin
      * `password`: list admin password
      * `subscribe_policy`: 1) Confirm; 2) Approval; 3)Confirm and approval. Default is Confirm (1)
      * `archive_private`: 0) Public; 1) Private. Default is Public (0)
      * `emailhost`: email host
      * `urlhost`: url host
      * `notification_email`: email for notification. If null assumes admin email.
      * `quiet`: 0) Send email notification on list creation; 1) No notification email. Default is to send notification (0) """

    admin = request.forms.get('admin')
    password = request.forms.get('password')
    urlhost = request.forms.get('urlhost')
    emailhost = request.forms.get('emailhost')
    subscribe_policy = request.forms.get('subscribe_policy', 1)
    archive_private = request.forms.get('archive_private', 0)
    quiet = request.forms.get('quiet', 0)
    notification_email = request.forms.get('notification_email')

    status_code = 200
    try:
        subscribe_policy = int(subscribe_policy)
        archive_private = int(archive_private)
        quiet = int(quiet)
        if notification_email is None:
            notification_email = admin
    except ValueError, e:
        message = 'Invalid parameters: ' + str(e)
        return HTTPResponse(status=get_error_code('InvalidParams'),
                            body=json.dumps({'message': message}),
                            content_type='application/json')

    if subscribe_policy < 1 or subscribe_policy > 3:
        subscribe_policy = 1

    if archive_private < 0 or archive_private > 1:
        archive_private = 0

    if quiet < 0 or quiet > 1:
        quiet = 0

    if password is None or password == '':
        message = 'Invalid password'
        return HTTPResponse(status=get_error_code('InvalidPassword'),
                            body=json.dumps({'message': message}),
                            content_type='application/json')
    else:
        password = Utils.sha_new(password).hexdigest()

    mail_list = MailList.MailList()
    message = 'Success'
    try:
        mail_list.Create(listname, admin, password, urlhost=urlhost, emailhost=emailhost)
        mail_list.archive_private = archive_private
        mail_list.subscribe_policy = subscribe_policy
        mail_list.Save()
        if not quiet:
            # print 'Sending notification email.'
            i18n.set_language('en')
            listname = listname
            password = password
            admin_url = mail_list.GetScriptURL('admin', absolute=1)
            listinfo_url = mail_list.GetScriptURL('listinfo', absolute=1)
            requestaddr = mail_list.GetRequestEmail()
            siteowner = notification_email
            text = """ The mailing list {0} has just been created for you.  The
                following is some basic information about your mailing list.

                Your mailing list password is:

                    {1}

                You need this password to configure your mailing list.  You also need
                it to handle administrative requests, such as approving mail if you
                choose to run a moderated list.

                You can configure your mailing list at the following web page:

                    {2}

                The web page for users of your mailing list is:

                    {3}

                You can even customize these web pages from the list configuration
                page.  However, you do need to know HTML to be able to do this.

                There is also an email-based interface for users (not administrators)
                of your list; you can get info about using it by sending a message
                with just the word `help' as subject or in the body, to:

                    {4}

                To unsubscribe a user: from the mailing list 'listinfo' web page,
                click on or enter the user's email address as if you were that user.
                Where that user would put in their password to unsubscribe, put in
                your admin password.  You can also use your password to change
                member's options, including digestification, delivery disabling, etc.

                Please address all questions to {5}. """
            text = text.format(listname, password, admin_url, listinfo_url, requestaddr, siteowner)
            email_title = 'Your new mailing list: {0}'
            email_title = email_title.format(listname)
            msg = Message.UserNotification(
                admin, notification_email,
                _(email_title),
                text, 'en')
            msg.send(mail_list)
    except (Errors.BadListNameError, AssertionError,
            Errors.MMBadEmailError, Errors.MMListAlreadyExistsError), e:
        message = get_error_message(e.__class__.__name__) + ': ' + str(e)
        status_code = get_error_code(e.__class__.__name__)
    finally:
        mail_list.Unlock()
    return HTTPResponse(status=status_code,
                        body=json.dumps({'message': message}),
                        content_type='application/json')


def delete_list(listname):
    """Delete an email list.

    **Method**: DELETE

    **URI**: /<listname>

    **Parameters**:

      * `delete_archives`: If this equals to 'true', archives will be deleted
      as well"""

    delete_archives = parse_boolean(request.forms.get('delete_archives'))
    mlist = get_mailinglist(listname, lock=False)
    """
    if mlist.Authenticate((mm_cfg.AuthCreator,
                           mm_cfg.AuthListAdmin,
                           mm_cfg.AuthSiteAdmin),
                          password) == mm_cfg.UnAuthorized:
        return HTTPResponse(status=403,
                            body=json.dumps(
                                {'message': \
                                 'Not authorized to delete this list'}
                            ),
                            content_type='application/json')

    # Do the MTA-specific list deletion tasks
    if mm_cfg.MTA:
        modname = 'Mailman.MTA.' + mm_cfg.MTA
        __import__(modname)
        sys.modules[modname].remove(mlist, cgi=1)
    """

    REMOVABLES = ['lists/%s']
    if delete_archives:
        REMOVABLES.extend(['archives/private/%s',
                           'archives/private/%s.mbox',
                           'archives/public/%s',
                           'archives/public/%s.mbox',
                           ])
    listname = mlist.internal_name()
    for dirtmpl in REMOVABLES:
        dir = os.path.join(mm_cfg.VAR_PREFIX, dirtmpl % listname)
        if os.path.islink(dir):
            try:
                os.unlink(dir)
            except OSError, e:
                return HTTPResponse(status=500,
                                    body=json.dumps({'message': str(e)}),
                                    content_type='application/json')
        elif os.path.isdir(dir):
            try:
                shutil.rmtree(dir)
            except OSError, e:
                return HTTPResponse(status=500,
                                    body=json.dumps({'message': str(e)}),
                                    content_type='application/json')
    return HTTPResponse(body=json.dumps({'message': 'Success'}),
                        content_type='application/json')


def members(listname):
    """Lists subscribers for the `listname` list.

    **Method**: GET

    **URI**: /<listname>/members

    **Parameters**:

      * `address` (optional): email address to search for in list."""

    address = request.query.get('address')
    try:
        mlist = MailList.MailList(listname.lower(), lock=False)
    except Errors.MMUnknownListError, e:
        message = get_error_message(e.__class__.__name__) + ': ' + listname
        return HTTPResponse(status=get_error_code(e.__class__.__name__),
                            body=json.dumps({'message': message}),
                            content_type='application/json')
    if not address:
        return HTTPResponse(body=json.dumps(mlist.getMembers()),
                            content_type='application/json')
    else:
        member = []
        try:
            memberKey = mlist.getMemberKey(address)
        except Errors.NotAMemberError, e:
            message = get_error_message(e.__class__.__name__) + ': ' + str(e)
            return HTTPResponse(status=get_error_code(e.__class__.__name__),
                                body=json.dumps({'message': message}),
                                content_type='application/json')
        member_values = {
            'address': memberKey,
            'fullname': mlist.getMemberName(memberKey)
        }
        member.append(member_values)
        return HTTPResponse(body=json.dumps(member),
                            content_type='application/json')
