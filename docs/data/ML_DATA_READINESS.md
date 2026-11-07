# Scientific Data Readiness for AI/ML Modeling (F1 Foundation)

## 1. Machine Learning Architectural Context

Vayumarg is designed to power two independent modeling subsystems developed by separate sub-teams:

- **Module A:** Satellite-based current-state cyclone classification and intensity estimation (Team: Ishhan, Ishika, Kirti).
- **Module B:** Independent cyclone track and future wind-intensity prediction (Team: Chandan, Khushi, Hiten).

> [!IMPORTANT]
> **Architectural Independence Guarantee:**  
> Module B **must not depend** on Module A predictions to function. Both modules independently ingest ground-truth data from the shared Vayumarg scientific database.

---

## 2. Module A Data Readiness: Satellite Raster Alignment

### Scientific Objective
Estimate current cyclone intensity (maximum sustained wind speed and IMD classification) directly from geostationary satellite channels (INSAT-3D/3DR TIR1, TIR2, MIR, VIS).

### Ground-Truth Pairing Contract (`ModuleAExportRecord`)
Module A requires ground-truth observation targets paired to satellite raster acquisition timestamps:

```python
class ModuleAExportRecord(BaseModel):
    storm_id: UUID
    sid: str  # IBTrACS Storm Identifier
    canonical_name: str
    season_year: int
    primary_basin: str
    observation_time_utc: datetime  # Synoptic timestamp
    latitude: float  # Ground-truth vortex center
    longitude: float  # Ground-truth vortex center
    imd_wind_speed_knots: float | None  # IMD 3-min sustained ground truth
    imd_category: str | None  # IMD severity category (D, CS, VSCS, etc.)
    jtwc_wind_speed_knots: float | None  # JTWC 1-min sustained ground truth
    wmo_wind_speed_knots: float | None  # WMO 10-min sustained ground truth
    central_pressure_hpa: float | None  # Minimum central pressure
    is_retrospective_best_track: bool  # Retrospective best-track flag
    satellite_matching_window_minutes: int = 30
```

### Readiness Metrics for Module A
- **Total Satellite-Era Storms (1982–2026):** `464 storms`
- **Total Modern High-Resolution Storms (INSAT-3D Era, 2014–2026):** Over 70 major cyclones available for immediate raster pairing.
- **Vortex Center Coordinates:** PostGIS SRID 4326 Point geometries available for automatic spatial bounding-box cropping of satellite arrays.
- **IMD Intensity Labels:** 9,467 non-null 3-minute sustained wind observations with authentic IMD grades.

---

## 3. Module B Data Readiness: Trajectory & Intensity Forecasting

### Scientific Objective
Predict future 6h, 12h, 24h, 48h, 72h cyclone track coordinates and wind intensity from historical sequence vectors.

### Trajectory Sequence Contract (`ModuleBExportRecord`)
Module B consumes chronological sequence vectors partitioned by storm:

```python
class ModuleBExportRecord(BaseModel):
    storm_id: UUID
    sid: str
    canonical_name: str
    season_year: int
    primary_basin: str
    total_trajectory_points: int
    trajectory: list[ModuleBTrajectoryPoint]
```

### Critical Forecasting Lineage: Retrospective Best-Track vs Operational Advisories

> [!WARNING]
> **Data Leakage & Smoothing Risk in ML Track Forecasting:**  
> In retrospective best-track archives (such as IBTrACS), storm center positions and peak intensities are smoothed **post-season** by meteorological agencies with full knowledge of subsequent satellite imagery, coastal radar, and surface landfall observations.  
> 1. Models trained on smoothed best tracks must acknowledge that operational real-time observations have higher measurement noise and uncertainty.  
> 2. Module B sequence extractors must strictly enforce causal chronological ordering ($t \le t_0$) so that future observations ($t > t_0$) are never leaked into the input feature vector.  
> 3. The `is_retrospective_best_track` boolean flag in `TrackObservation` explicitly labels this lineage.
> 4. Regional Domain Filtering: NI regional track forecasting models should filter by `quality_flag == 'VALID'` (96,667 points) unless explicitly studying trans-basin dynamics (7,707 `CROSS_BASIN` points).
> 5. Reproducibility Freeze: Both modules should link experimental baselines to Dataset Snapshot `vayumarg-nio-ibtracs-f1.1-freeze` (Manifest SHA-256 `441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107`).

### Readiness Metrics for Module B
- **Total Available Cyclone Trajectories:** `1,860 complete storm tracks`.
- **Chronological Sequence Points:** `104,374 observation steps` spanning 185 seasons.
- **Continuous Multi-Day Tracks:** Modern cyclones (e.g., BIPARJOY) provide up to 113 consecutive synoptic steps across 13 days of storm lifetime.

---

## 4. Extraction API Usage

Both modules can extract their tailored data contracts directly through `vayumarg.contracts.export`:

```python
from vayumarg.database.engine import get_db_session
from vayumarg.contracts.export import export_module_a_dataset, export_module_b_dataset

with get_db_session() as session:
    # Module A: Satellite alignment export for 2020 season
    mod_a_data = export_module_a_dataset(session, season_year=2020)

    # Module B: Trajectory sequence export for Cyclone Amphan
    mod_b_data = export_module_b_dataset(session, sid="2020136N10088")
```

