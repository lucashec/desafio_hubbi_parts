from rest_framework.exceptions import APIException


class BusinessException(APIException):
    """
    Exceção base para erros de negócio.
    """

    status_code = 400
    default_detail = "Erro de negócio."
    default_code = "business_error"


class ResourceNotFoundException(APIException):
    """
    Exceção para recurso não encontrado.
    """

    status_code = 404
    default_detail = "Recurso não encontrado."
    default_code = "not_found"


class UnauthorizedException(APIException):
    """
    Exceção para acesso não autorizado.
    """

    status_code = 401
    default_detail = "Não autorizado."
    default_code = "unauthorized"


class ForbiddenException(APIException):
    """
    Exceção para acesso proibido.
    """

    status_code = 403
    default_detail = "Acesso proibido."
    default_code = "forbidden"


class ConflictException(APIException):
    """
    Exceção para conflito de dados.
    """

    status_code = 409
    default_detail = "Conflito de dados."
    default_code = "conflict"
