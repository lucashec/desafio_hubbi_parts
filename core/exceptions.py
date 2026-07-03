from rest_framework.exceptions import APIException


class BusinessException(APIException):
    status_code = 400
    default_detail = "Erro de negócio."
    default_code = "business_error"


class ResourceNotFoundException(APIException):
    status_code = 404
    default_detail = "Recurso não encontrado."
    default_code = "not_found"


class UnauthorizedException(APIException):
    status_code = 401
    default_detail = "Não autorizado."
    default_code = "unauthorized"


class ForbiddenException(APIException):
    status_code = 403
    default_detail = "Acesso proibido."
    default_code = "forbidden"


class ConflictException(APIException):
    status_code = 409
    default_detail = "Conflito de dados."
    default_code = "conflict"
