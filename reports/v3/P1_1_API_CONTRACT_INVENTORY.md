# VAYUMARG 3.0 — P1.1 API CONTRACT INVENTORY & CANONICAL IDENTITY AUDIT

**Audit Date:** 2026-11-07  
**Auditor:** Principal FastAPI Architect & API Security Lead  
**Classification:** REST API Specification & Contract Invariant Report  
**Status:** COMPLETE & INDEPENDENTLY RECONCILED  

---

## 1. Executive Summary

Milestone P1.1 established complete contract stabilization across all 47 endpoints of the Vayumarg FastAPI application. The monolithic `server.py` implementation was modularized into specialized routers and service layers, achieving **100% path-for-path, method-for-method, and schema-for-schema OpenAPI parity** against the baseline.

Additionally, the integration-test naming friction between `storm_sid` and `canonical_sid` was formally resolved through dual-field serialization and dual-field request parsing.

---

## 2. Canonical Storm Identity Resolution (`storm_sid` vs `canonical_sid`)

### Problem
* The historical database model uses UUID primary keys for `Storm.id` and partitions external identifiers into `StormAlias.agency_storm_id` with `source_agency='IBTRACS'`.
* Some API endpoints returned `canonical_sid`, while client applications, demonstration scenario fixtures, and integration tests expected `storm_sid`.
* `ForecastRequest` previously accepted only `storm_sid` or `storm_name`, failing if a client supplied `canonical_sid`.

### Authoritative Architecture
* **Contract Ground Truth:** The alphanumeric IBTrACS identifier (e.g., `2023156N10067`) is the canonical tropical cyclone identifier.
* **Dual-Field Guarantee:**
  1. All storm responses (`/api/storms`, `/api/storms/{id}`, `/api/storms/{id}/track`) serialize both `canonical_sid` and `storm_sid` with the identical string value:
     ```json
     {
       "storm_id": "2023156N10067",
       "canonical_sid": "2023156N10067",
       "storm_sid": "2023156N10067",
       "canonical_name": "BIPARJOY"
     }
     ```
  2. `ForecastRequest` accepts either `canonical_sid`, `storm_sid`, or `storm_name`:
     ```python
     storm_ident = (req.canonical_sid or req.storm_sid or req.storm_name or "").strip()
     ```
  3. Zero breaking changes were introduced to existing frontend consumers, and all integration tests pass transparently.

---

## 3. Exhaustive 47-Endpoint API Inventory

| HTTP Method | Route URL Path | Router Module | Request Schema | Response Schema | Fallback Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | `server.py` | None | FileResponse (`index.html`) | Static UI fallback |
| **GET** | `/favicon.svg` | `server.py` | None | FileResponse | 404 |
| **GET** | `/favicon.ico` | `server.py` | None | FileResponse | 404 |
| **GET** | `/api/health` | `routers/health.py` | None | `HealthStatus` | Offline Demo Cache |
| **GET** | `/api/summary` | `routers/health.py` | None | `PlatformSummary` | Offline Demo Cache |
| **GET** | `/api/governance` | `routers/health.py` | None | Governance dict | In-memory governance ledger |
| **GET** | `/api/methodology` | `routers/health.py` | None | Methodology dict | In-memory methodology specs |
| **GET** | `/api/forecast/methodology` | `routers/health.py` | None | Methodology dict | In-memory methodology specs |
| **GET** | `/api/storms` | `routers/storms.py` | Query params | `list[StormSummary]` | Local target storms |
| **GET** | `/api/storms/{storm_identifier}` | `routers/storms.py` | Path param | `StormProfile` | Offline `*_profile.json` |
| **GET** | `/api/storms/{storm_identifier}/track` | `routers/storms.py` | Query params | `TrackResponse` (GeoJSON) | Offline `*_track.json` |
| **GET** | `/api/storms/{storm_identifier}/satellite` | `routers/storms.py` | Path param | Satellite crop meta | Target storms registry |
| **POST** | `/api/forecast/generate` | `routers/forecast.py` | `ForecastRequest` | `CycloneForecastOutput` | Baseline extrapolation cache |
| **GET** | `/api/storms/{storm_identifier}/forecast`| `routers/forecast.py` | Query params | `CycloneForecastOutput` | Baseline extrapolation cache |
| **POST** | `/api/forecast/verify` | `routers/forecast.py` | `VerificationRequest`| `HindsightVerificationOutput`| Database retrospective evaluation |
| **GET** | `/api/forecast/demo-cases` | `routers/forecast.py` | None | `list[DemoScenario]` | `data/demo_cache/scenarios.json` |
| **GET** | `/api/demo/scenarios` | `routers/forecast.py` | None | `list[DemoScenario]` | `data/demo_cache/scenarios.json` |
| **GET** | `/api/scenarios` | `routers/forecast.py` | None | `list[DemoScenario]` | `data/demo_cache/scenarios.json` |
| **GET** | `/api/satellite/crops` | `routers/satellite.py` | None | `list[SatelliteCropMeta]` | Local HDF5 filesystem scan |
| **GET** | `/api/satellite/crop/{name}/image` | `routers/satellite.py` | Query params | PNG Bytes (`image/png`) | Disk render |
| **GET** | `/api/satellite/crops/{name}/preview`| `routers/satellite.py` | Query params | PNG Bytes (`image/png`) | Disk render |
| **GET** | `/api/satellite/crop/{name}/metrics` | `routers/satellite.py` | Query params | `PhysicalCropMetrics` | Disk HDF5 metric calculator |
| **GET** | `/api/satellite/crops/{name}/metrics`| `routers/satellite.py` | Query params | `PhysicalCropMetrics` | Disk HDF5 metric calculator |
| **GET** | `/api/v1/satellite/health` | `routes_satellite.py` | None | Health dict | Service check |
| **GET** | `/api/v1/satellite/crops` | `routes_satellite.py` | None | `list[CropSummary]` | Ingestion service scan |
| **GET** | `/api/v1/satellite/crops/{id}` | `routes_satellite.py` | Path param | `CropDetail` | Ingestion service lookup |
| **GET** | `/api/v1/satellite/crops/{id}/channels/{ch}` | `routes_satellite.py` | Path params | `ChannelDetail` | Physical analytics engine |
| **GET** | `/api/v1/satellite/crops/{id}/channels/{ch}/preview` | `routes_satellite.py` | Query params | PNG Bytes | Colormap renderer |
| **GET** | `/api/v1/satellite/crops/{id}/labels`| `routes_satellite.py` | Path param | Label association dict | Ground-truth metadata match |
| **GET** | `/api/v1/satellite/legends/{colormap}`| `routes_satellite.py` | Path param | Legend spec dict | Color table generator |
| **GET** | `/api/v1/satellite/legends/{colormap}/image` | `routes_satellite.py` | Path param | PNG Bytes | Colorbar generator |
| **GET** | `/api/dataset/summary` | `routes_dataset.py` | None | Summary dict | Disk dataset scanner |
| **GET** | `/api/dataset/samples` | `routes_dataset.py` | Query params | `list[Sample]` | Manifest parser |
| **GET** | `/api/dataset/samples/{id}` | `routes_dataset.py` | Path param | `SampleDetail` | Disk sample inspector |
| **GET** | `/api/dataset/preview/{storm}/{ch}/{cm}` | `routes_dataset.py` | Path params | PNG Bytes | Colormap preview cache |
| **GET** | `/api/dataset/pixel` | `routes_dataset.py` | Query params | Pixel inspection dict | Raw HDF5 array indexer |
| **GET** | `/api/dataset/export/manifest.json` | `routes_dataset.py` | None | JSON file download | Dataset manifest generator |
| **GET** | `/api/dataset/export/metadata.csv` | `routes_dataset.py` | None | CSV file download | Dataset CSV generator |
| **GET** | `/api/ml/registry` | `routes_ml.py` | None | Registry dict | Read-only model registry |
| **GET** | `/api/ml/models/{model_id}` | `routes_ml.py` | Path param | Model metadata dict | Model registry query |
| **POST** | `/api/ml/infer/satellite_cnn` | `routes_ml.py` | Inference request | Prediction dict | ResNet-18 forward pass |
| **POST** | `/api/ml/infer/convlstm` | `routes_ml.py` | Sequence request | Prediction dict | ConvLSTM forward pass |
| **POST** | `/api/ml/infer/track_gru` | `routes_ml.py` | Trajectory request | Prediction dict | Track GRU & Hybrid forward pass |
| **GET** | `/api/ml/track/storms` | `routes_ml.py` | None | `list[Storm]` | Track evaluation registry |
| **GET** | `/api/ml/convlstm/sequences` | `routes_ml.py` | Query params | `list[Sequence]` | ConvLSTM sequence parser |
| **GET** | `/api/ml/insat_evaluations` | `routes_ml.py` | None | Evaluation dict | Held-out evaluation ledger |
| **GET** | `/api/ml/image/{filename}` | `routes_ml.py` | Path param | Image Bytes | Image file response |

---

## 4. Frontend Consumer Verification

All frontend screens in `frontend/src/components/` (`OverviewScreen`, `SatelliteScreen`, `AIModelLabScreen`, `ForecastLabScreen`, `MethodologyScreen`, `DatasetExplorerScreen`) query these endpoints exclusively via `frontend/src/api.ts`.

Production build (`npm run build`) confirmed zero TypeScript type errors and zero broken API contracts.
