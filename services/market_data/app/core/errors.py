"""Provider-neutral failures safe to expose to API consumers."""
class MarketDataError(Exception):
    def __init__(self, message='Market data provider failed', *, code='upstream_error', status_code=502):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
