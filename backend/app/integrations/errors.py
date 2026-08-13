class IntegrationError(RuntimeError):
    """Raised when an external enterprise integration fails."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
    ) -> None:
        super().__init__(message)

        self.code = code