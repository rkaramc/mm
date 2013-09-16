class MMException(Exception):
    pass

class MetadataContainerException(Exception):
    pass

class MMRequestException(Exception):
    pass


class SalesforceMoreThanOneRecord(Exception):
    '''
    Error Code: 300
    The value returned when an external ID exists in more than one record. The
    response body contains the list of matching records.
    '''
    pass


class SalesforceMalformedRequest(Exception):
    '''
    Error Code: 400
    The request couldn't be understood, usually becaue the JSON or XML body contains an error.
    '''
    pass


class SalesforceExpiredSession(Exception):
    '''
    Error Code: 401
    The session ID or OAuth token used has expired or is invalid. The response
    body contains the message and errorCode.
    '''
    pass


class SalesforceRefusedRequest(Exception):
    '''
    Error Code: 403
    The request has been refused. Verify that the logged-in user has
    appropriate permissions.
    '''
    pass


class SalesforceResourceNotFound(Exception):
    '''
    Error Code: 404
    The requested resource couldn't be found. Check the URI for errors, and
    verify that there are no sharing issues.
    '''
    pass


class SalesforceGeneralError(Exception):
    '''
    A non-specific Salesforce error.
    '''
    pass