API Documentation
=================

Requests can be made to any of the URI's below, strictly using the HTTP methods indicated.

The body of all responses contains valid JSON objects. Unless otherwise noted, successful requests get as response a 200 (OK) status code for response, and true in the response body. Failed requests will get responses with some HTTP error code in the 400s, and a string describing the problem in the response body.

Supported methods:

List Lists
++++++++++
Lists existing mailing lists on the server.

    **Method**: GET

    **URI**: /

    Returns a list of the mailing lists that exist on this server.

    **Parameters**:
        * `address` (optional): email address to search for in lists.

Create List
+++++++++++
Create a new list.

    **Method**: POST

    **URI**: /<listname>

    **Parameters**:
        * `admin`: email of list admin
        * `password`: list admin password
        * `subscribe_policy`: 1) Confirm; 2) Approval; 3)Confirm and approval.
          Default is Confirm (1)
        * `archive_private`: 0) Public; 1) Private. Default is Public (0)
        * `emailhost`: email host
        * `urlhost`: url host
        * `notification_email`: email for notification. If null assumes admin email.
        * `quiet`: 0) Send email notification on list creation; 1) No notification email. Default is to send notification (0)

Delete List
+++++++++++
Delete a list.

    **Method**: DELETE

    **URI**: /<listname>

    **Parameters**:
        * `delete_archives`: If this equals to 'true', archives will be deleted
          as well

List Attributes
+++++++++++++++
Get the list attributes.

    **Method**: GET

    **URI**: /<listname>

    Returns a dictionary containing the basic attributes for a specific mailing
    list that exist on this server.

Subscribe
+++++++++
Adds a new subscriber to the list called `<listname>`

    **Method**: PUT

    **URI**: /<listname>/members

    **Parameters**:

      * `address`: email address that is to be subscribed to the list.
      * `fullname`: full name of the person being subscribed to the list.
      * `digest`: if this equals `true`, the new subscriber will receive
        digests instead of every mail sent to the list.

Unsubscribe
+++++++++++
Unsubscribe an email address from the mailing list.

    **Method**: DELETE

    **URI**: /<listname>/members

    **Parameters**:

      * `address`: email address that is to be unsubscribed from the list

Members
+++++++
Lists subscribers for the `listname` list.

    **Method**: GET

    **URI**: /<listname>/members

    **Parameters**:
        * `address` (optional): email address to search for in list.

    Returns an array of email addresses.
