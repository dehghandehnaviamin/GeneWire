//! Experimental pull-based htsget/BAM byte streams. Transport success is not
//! evidence of complete or scientifically correct genomic results.
mod error;
mod model;
mod network;
mod stream;
mod ticket;

pub use error::{Category, Error, Result};
pub use model::{Configuration, Destination, Limits, MAX_CHUNK, Query, UpstreamProfile};
pub use network::ip;
pub use stream::{CapabilityEvidence, Cleanup, Client, Phase, Report, State, Stream};
