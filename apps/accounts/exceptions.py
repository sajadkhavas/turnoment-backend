class AccountsDomainError(Exception):
    default_code = "accounts_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code or self.default_code


class OtpRateLimited(AccountsDomainError):
    default_code = "otp_rate_limited"

    def __init__(self, message: str, *, retry_after: int):
        super().__init__(message)
        self.retry_after = max(1, int(retry_after))


class OtpInvalid(AccountsDomainError):
    default_code = "otp_invalid"


class OtpExpired(AccountsDomainError):
    default_code = "otp_expired"


class OtpConsumed(AccountsDomainError):
    default_code = "otp_consumed"


class AccountInactive(AccountsDomainError):
    default_code = "account_inactive"
