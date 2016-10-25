import os
import json
from .utils import parse_boolean, \
                   get_mailinglist, \
                   get_error_code, \
                   get_error_message
from Mailman import Errors, \
                    UserDesc, \
                    MailList, \
                    Utils, \
                    Defaults
from bottle import HTTPResponse, \
                   request

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
        mlist = get_mailinglist(listname)
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

    mlist = get_mailinglist(listname)
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
    mlist = get_mailinglist(listname)
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

    **Method**: PUT

    **URI**: /<listname>

    **Parameters**:

      * `admin`: email of list admin
      * `password`: list admin password
      * `subscribe_policy`: 1) Confirm; 2) Approval; 3)Confirm and approval.
      Default is Confirm (1)
      * `archive_private`: 0) Public; 1) Private. Default is Public (0) """
    admin = request.forms.get('admin')
    password = request.forms.get('password')
    subscribe_policy = request.forms.get('subscribe_policy', 1)
    archive_private = request.forms.get('archive_private', 0)

    status_code = 200
    try:
        subscribe_policy = int(subscribe_policy)
        archive_private = int(archive_private)
    except ValueError, e:
        message = 'Invalid parameters: ' + str(e)
        return HTTPResponse(status=get_error_code('InvalidParams'),
                            body=json.dumps({'message': message}),
                            content_type='application/json')

    if subscribe_policy < 1 or subscribe_policy > 3:
        subscribe_policy = 1

    if archive_private < 0 or archive_private > 1:
        archive_private = 0

    if password == '':
        message = 'Invalid password'
        return HTTPResponse(status=get_error_code('InvalidPassword'),
                            body=json.dumps({'message': message}),
                            content_type='application/json')
    else:
        password = Utils.sha_new(password).hexdigest()

    mail_list = MailList.MailList()
    message = 'Success'
    try:
        mail_list.Create(listname, admin, password)
        mail_list.archive_private = archive_private
        mail_list.subscribe_policy = subscribe_policy
        mail_list.Save()
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

    **URI**: /<listname>"""
    mlist = get_mailinglist(listname)
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
