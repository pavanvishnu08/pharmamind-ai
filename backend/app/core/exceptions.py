"""
PharmaMind AI - Custom Domain Exceptions
"""

from fastapi import HTTPException, status

class PharmaMindException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str = "GENERIC_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class EntityNotFoundException(PharmaMindException):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type} with identifier '{entity_id}' not found.",
            error_code="ENTITY_NOT_FOUND"
        )


class MedicalAdviceProhibitedException(PharmaMindException):
    def __init__(self, detail: str = "PharmaMind AI provides educational biomedical information only and is strictly prohibited from generating clinical diagnoses or individual prescribing decisions."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="MEDICAL_ADVICE_PROHIBITED"
        )


class InsufficientEvidenceException(PharmaMindException):
    def __init__(self, query: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authoritative biomedical evidence could not be verified for query: '{query}'.",
            error_code="INSUFFICIENT_EVIDENCE"
        )


class DatabaseUnavailableException(PharmaMindException):
    def __init__(self, detail: str = "Primary database is currently unreachable."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="DATABASE_UNAVAILABLE"
        )

