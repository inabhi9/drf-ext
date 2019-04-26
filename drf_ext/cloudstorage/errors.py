from drf_ext.errors import APIException


class CloudStorageError(APIException):
    pass


class UploadError(CloudStorageError):
    status_code = 503
