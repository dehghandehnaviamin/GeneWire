use std::fmt;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Category {
    InvalidQuery,
    InvalidState,
    Unsupported,
    TicketInvalid,
    AccessDenied,
    NetworkPolicy,
    ResponseInvalid,
    TransportFailed,
    ResourceLimit,
    DeadlineExceeded,
    Cancelled,
    InternalFailure,
    CleanupTimeout,
}

/// Intentionally contains no remote text, URLs, credentials or query identifiers.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Error {
    pub category: Category,
}
impl Error {
    pub fn new(category: Category) -> Self {
        Self { category }
    }
}
impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self.category)
    }
}
impl std::error::Error for Error {}
pub type Result<T> = std::result::Result<T, Error>;
pub(crate) fn err<T>(category: Category) -> Result<T> {
    Err(Error::new(category))
}
