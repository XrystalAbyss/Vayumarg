"""Satellite data discovery, HDF5 ingestion, physical analytics, visualization, and alignment utilities."""

from vayumarg.satellite.alignment import (
    AlignmentCandidate,
    SatelliteTrackAligner,
    calculate_haversine_distance_km,
)
from vayumarg.satellite.analytics import (
    ChannelAnalytics,
    SatelliteImageAnalyticsEngine,
)
from vayumarg.satellite.mosdac_adapter import (
    INSAT_IMAGER_CHANNELS,
    SUPPORTED_MOSDAC_PRODUCTS,
    MOSDACAdapter,
    MOSDACProductSpec,
    SpectralChannelSpec,
)
from vayumarg.satellite.provenance import (
    AUTHENTIC_SATELLITE_REGISTRY,
    DANA_IMD_INELIGIBILITY_NOTICE,
    GroundTruthObservation,
    ProvenanceRecord,
    get_provenance_by_identifier,
)
from vayumarg.satellite.service import (
    CropSummary,
    SatelliteImageService,
    get_satellite_service,
)
from vayumarg.satellite.tcir_adapter import (
    TCIRAdapter,
    TCIRDatasetProfile,
    TCIRFrameMetadata,
)
from vayumarg.satellite.visualizer import (
    COLORMAP_SPECS,
    ColormapSpec,
    LegendTick,
    SatelliteVisualizer,
)

__all__ = [
    "TCIRAdapter",
    "TCIRFrameMetadata",
    "TCIRDatasetProfile",
    "MOSDACAdapter",
    "MOSDACProductSpec",
    "SpectralChannelSpec",
    "SUPPORTED_MOSDAC_PRODUCTS",
    "INSAT_IMAGER_CHANNELS",
    "SatelliteTrackAligner",
    "AlignmentCandidate",
    "calculate_haversine_distance_km",
    "SatelliteVisualizer",
    "COLORMAP_SPECS",
    "ColormapSpec",
    "LegendTick",
    "SatelliteImageAnalyticsEngine",
    "ChannelAnalytics",
    "AUTHENTIC_SATELLITE_REGISTRY",
    "DANA_IMD_INELIGIBILITY_NOTICE",
    "GroundTruthObservation",
    "ProvenanceRecord",
    "get_provenance_by_identifier",
    "SatelliteImageService",
    "get_satellite_service",
    "CropSummary",
]
