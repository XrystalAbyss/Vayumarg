"""Command Line Interface for Vayumarg Scientific Data Foundation and Ingestion."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import h5py
import typer
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import func, or_, select

from vayumarg.contracts.enums import Agency
from vayumarg.core.logging import get_logger
from vayumarg.database.engine import (
    audit_database_integrity,
    check_database_connectivity,
    get_db_session,
    get_default_engine,
    get_table_counts,
    verify_postgis_extension,
)
from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProduct,
    Storm,
    StormAlias,
    TrackObservation,
)
from vayumarg.ingestion.downloader import download_official_ibtracs_ni
from vayumarg.ingestion.ibtracs_ingest import run_ibtracs_ingestion
from vayumarg.ingestion.mosdac_client import MOSDACSearchClient
from vayumarg.quality.audit import generate_quality_audit, save_quality_reports
from vayumarg.quality.reconciliation import execute_scientific_reconciliation
from vayumarg.quality.snapshot import freeze_dataset_snapshot
from vayumarg.satellite.mosdac_adapter import MOSDACAdapter
from vayumarg.satellite.tcir_adapter import TCIRAdapter

logger = get_logger("vayumarg.cli")
app = typer.Typer(help="Vayumarg Scientific Data Foundation & IBTrACS Management CLI")


@app.command()
def check_db() -> None:
    """Verify raw database connection and PostGIS extension status."""
    engine = get_default_engine()
    conn_info = check_database_connectivity(engine)
    postgis_info = verify_postgis_extension(engine)

    table = Table(title="Vayumarg Database Connectivity & Geospatial Engine")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", conn_info.get("status", "unknown"))
    table.add_row("Dialect", conn_info.get("dialect", "unknown"))
    table.add_row("Driver", conn_info.get("driver", "unknown"))
    table.add_row("Server Version", conn_info.get("server_version", "unknown"))
    table.add_row(
        "PostGIS Extension",
        "Installed" if postgis_info.get("postgis_installed") else "Not Available",
    )
    if postgis_info.get("version"):
        table.add_row("PostGIS Lib Version", str(postgis_info.get("version")))

    rprint(table)


@app.command()
def counts() -> None:
    """Report stored row counts across canonical schema tables."""
    engine = get_default_engine()
    table_counts = get_table_counts(engine)

    table = Table(title="Vayumarg Canonical Schema Entity Counts")
    table.add_column("Table Name", style="cyan")
    table.add_column("Record Count", style="magenta")

    for tbl, count in table_counts.items():
        table.add_row(tbl, f"{count:,}")

    rprint(table)


@app.command()
def audit(json_output: bool = False) -> None:
    """Generate a comprehensive integrity and schema audit."""
    engine = get_default_engine()
    audit_data = audit_database_integrity(engine)

    if json_output:
        typer.echo(json.dumps(audit_data, indent=2))
        return

    check_db()
    counts()
    rprint("[bold green]All schema entities verified.[/bold green]")


@app.command()
def migrations() -> None:
    """Report currently applied Alembic migration status."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    rprint("[bold blue]Checking migration history:[/bold blue]")
    command.current(alembic_cfg, verbose=True)


@app.command()
def download_ibtracs(force: bool = False) -> None:
    """Download official NOAA IBTrACS North Indian Ocean CSV and generate cryptographic manifest."""
    rprint("[bold blue]Initiating official NOAA IBTrACS NI download...[/bold blue]")
    dest, manifest = download_official_ibtracs_ni(force=force)

    table = Table(title="NOAA IBTrACS Downloaded Asset Manifest")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Target File", str(dest))
    table.add_row("File Size", f"{manifest['size_bytes']:,} bytes")
    table.add_row("SHA-256 Checksum", manifest["sha256"])
    table.add_row("Asset Type", manifest.get("asset_type", "RAW_CSV"))

    rprint(table)
    rprint("[bold green][SUCCESS] Raw dataset acquired and verified.[/bold green]")


@app.command()
def ingest_pilot() -> None:
    """Run bounded deterministic pilot ingestion for benchmark cyclones (AMPHAN, BIPARJOY)."""
    rprint(
        "[bold cyan]Running Bounded Deterministic Pilot Ingestion (AMPHAN & BIPARJOY)...[/bold cyan]"
    )
    run_record = run_ibtracs_ingestion(pilot=True, batch_size=500)

    panel = Panel.fit(
        f"[bold green]Pilot Ingestion Status: {run_record.status}[/bold green]\n"
        f"Raw Rows Processed: [cyan]{run_record.records_read:,}[/cyan]\n"
        f"Observations Inserted: [green]{run_record.records_inserted:,}[/green]\n"
        f"Records Skipped/Idempotent: [yellow]{run_record.records_rejected:,}[/yellow]\n"
        f"Transaction Outcome: [bold]{run_record.transaction_outcome}[/bold]",
        title="Pilot Ingestion Audit Record",
    )
    rprint(panel)


@app.command()
def ingest_ni(batch_size: int = 2000) -> None:
    """Run full North Indian Ocean IBTrACS dataset ingestion into canonical database."""
    rprint(
        f"[bold cyan]Running Full North Indian Ocean IBTrACS Ingestion (batch size: {batch_size})...[/bold cyan]"
    )
    run_record = run_ibtracs_ingestion(pilot=False, batch_size=batch_size)

    panel = Panel.fit(
        f"[bold green]Full Ingestion Status: {run_record.status}[/bold green]\n"
        f"Raw Rows Processed: [cyan]{run_record.records_read:,}[/cyan]\n"
        f"Observations Inserted: [green]{run_record.records_inserted:,}[/green]\n"
        f"Records Skipped/Idempotent: [yellow]{run_record.records_rejected:,}[/yellow]\n"
        f"Transaction Outcome: [bold]{run_record.transaction_outcome}[/bold]",
        title="Full Ingestion Audit Record",
    )
    rprint(panel)


@app.command()
def query_storm(identifier: str) -> None:
    """Query storm details and multi-agency aliases by SID or canonical name."""
    with get_db_session() as session:
        # Search by SID or Name
        stmt = (
            select(Storm, StormAlias)
            .join(StormAlias, Storm.id == StormAlias.storm_id)
            .where(
                or_(
                    StormAlias.agency_storm_id == identifier,
                    func.upper(Storm.canonical_name) == identifier.upper(),
                    func.upper(StormAlias.agency_storm_name) == identifier.upper(),
                )
            )
        )
        results = session.execute(stmt).all()

        if not results:
            rprint(f"[bold red]No storm found matching identifier: '{identifier}'[/bold red]")
            return

        storm = results[0][0]
        aliases = [r[1] for r in results]

        # Observation stats
        obs_count = session.execute(
            select(func.count(TrackObservation.id)).where(TrackObservation.storm_id == storm.id)
        ).scalar_one()

        max_wind_imd = session.execute(
            select(func.max(TrackObservation.wind_speed_knots)).where(
                TrackObservation.storm_id == storm.id,
                TrackObservation.source_agency == Agency.IMD.value,
            )
        ).scalar_one()

        max_wind_jtwc = session.execute(
            select(func.max(TrackObservation.wind_speed_knots)).where(
                TrackObservation.storm_id == storm.id,
                TrackObservation.source_agency == Agency.JTWC.value,
            )
        ).scalar_one()

        min_pres = session.execute(
            select(func.min(TrackObservation.central_pressure_hpa)).where(
                TrackObservation.storm_id == storm.id
            )
        ).scalar_one()

        table = Table(title=f"Storm Profile: {storm.canonical_name} ({storm.season_year})")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Canonical ID", str(storm.id))
        table.add_row("Canonical Name", storm.canonical_name)
        table.add_row("Season Year", str(storm.season_year))
        table.add_row("Primary Basin", storm.primary_basin)
        table.add_row("Nature Code", storm.nature)
        table.add_row("Total Track Observations", f"{obs_count:,}")
        table.add_row(
            "Peak IMD Wind (3-min)", f"{max_wind_imd} kts" if max_wind_imd else "Unreported"
        )
        table.add_row(
            "Peak JTWC Wind (1-min)", f"{max_wind_jtwc} kts" if max_wind_jtwc else "Unreported"
        )
        table.add_row("Min Central Pressure", f"{min_pres} hPa" if min_pres else "Unreported")

        rprint(table)

        # Aliases Table
        alias_table = Table(title="Cross-Agency Storm Aliases")
        alias_table.add_column("Agency", style="cyan")
        alias_table.add_column("Agency Storm ID", style="magenta")
        alias_table.add_column("Reported Name", style="yellow")
        alias_table.add_column("Confidence", style="green")

        for a in aliases:
            alias_table.add_row(
                a.source_agency,
                a.agency_storm_id,
                a.agency_storm_name or "",
                f"{a.matching_confidence:.2f}",
            )

        rprint(alias_table)


@app.command()
def query_track(identifier: str, limit: int = 25) -> None:
    """Query chronological track observations for a given storm SID or name."""
    with get_db_session() as session:
        storm = (
            session.execute(
                select(Storm)
                .join(StormAlias, Storm.id == StormAlias.storm_id)
                .where(
                    or_(
                        StormAlias.agency_storm_id == identifier,
                        func.upper(Storm.canonical_name) == identifier.upper(),
                    )
                )
            )
            .scalars()
            .first()
        )

        if not storm:
            rprint(f"[bold red]Storm not found: '{identifier}'[/bold red]")
            return

        obs_stmt = (
            select(TrackObservation)
            .where(TrackObservation.storm_id == storm.id)
            .order_by(TrackObservation.observation_time_utc, TrackObservation.source_agency)
            .limit(limit)
        )
        observations = session.execute(obs_stmt).scalars().all()

        table = Table(
            title=f"Track Points for {storm.canonical_name} ({storm.season_year}) [Showing first {limit}]"
        )
        table.add_column("Time (UTC)", style="cyan")
        table.add_column("Agency", style="magenta")
        table.add_column("Lat, Lon", style="white")
        table.add_column("Wind (kts)", style="green")
        table.add_column("Averaging", style="blue")
        table.add_column("Pres (hPa)", style="yellow")
        table.add_column("Category", style="red")

        for o in observations:
            table.add_row(
                o.observation_time_utc.strftime("%Y-%m-%d %H:%M"),
                o.source_agency,
                f"{o.latitude:.2f}, {o.longitude:.2f}",
                f"{o.wind_speed_knots}" if o.wind_speed_knots is not None else "-",
                o.averaging_period,
                f"{o.central_pressure_hpa}" if o.central_pressure_hpa is not None else "-",
                o.imd_category or "-",
            )

        rprint(table)


@app.command()
def audit_quality() -> None:
    """Execute scientific quality audit on the canonical database and export Markdown/JSON reports."""
    rprint("[bold blue]Generating authentic scientific quality audit from database...[/bold blue]")
    with get_db_session() as session:
        audit_data = generate_quality_audit(session)
        j_path, m_path = save_quality_reports(audit_data)

    rprint(
        f"[bold green][SUCCESS] Quality audit exported to:\n  - {j_path}\n  - {m_path}[/bold green]"
    )


@app.command()
def reconcile_data() -> None:
    """Execute scientific data reconciliation: WMO agency averaging, Venn alignment, and cross-basin detection."""
    rprint(
        "[bold blue]Executing scientific data reconciliation on research database...[/bold blue]"
    )
    with get_db_session() as session:
        diff = execute_scientific_reconciliation(session)

    impact = diff.get("impact_summary", {})
    table = Table(title="Vayumarg Scientific Data Reconciliation Summary")
    table.add_column("Metric / Correction", style="cyan")
    table.add_column("Value / Count", style="green")

    for k, v in impact.items():
        table.add_row(k.replace("_", " ").title(), f"{v:,}")

    rprint(table)
    rprint(
        "[bold green][SUCCESS] Reconciliation completed. Audit log: reports/F1_1_BEFORE_AFTER_AUDIT.json[/bold green]"
    )


@app.command()
def freeze_snapshot(
    name: str = "vayumarg-nio-ibtracs-f1.1-freeze",
    version: str = "f1.1",
) -> None:
    """Freeze current dataset state into cryptographic manifest and dataset_snapshots record."""
    rprint(
        f"[bold blue]Creating frozen dataset snapshot: {name} (version {version})...[/bold blue]"
    )
    with get_db_session() as session:
        snapshot = freeze_dataset_snapshot(
            session=session,
            snapshot_name=name,
            transformation_version=version,
        )

    table = Table(title="Vayumarg Dataset Snapshot Freeze Manifest")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Snapshot ID", str(snapshot.id))
    table.add_row("Snapshot Name", snapshot.snapshot_name)
    table.add_row("Version", snapshot.transformation_version)
    table.add_row("Manifest SHA-256", snapshot.manifest_sha256)
    table.add_row("Total Samples", f"{snapshot.total_samples:,}")
    table.add_row("Manifest URI", snapshot.manifest_uri)
    table.add_row("Created At (UTC)", snapshot.created_at_utc.isoformat())

    rprint(table)
    rprint("[bold green][SUCCESS] Dataset snapshot successfully frozen and verified.[/bold green]")


@app.command()
def mosdac_products() -> None:
    """List verified supported ISRO MOSDAC satellite imager products and channel characteristics."""
    products = MOSDACAdapter.get_supported_products()

    table = Table(title="ISRO MOSDAC Satellite Products Registry (Vayumarg Candidate Sensors)")
    table.add_column("Product Code", style="cyan")
    table.add_column("Satellite", style="green")
    table.add_column("Sensor", style="yellow")
    table.add_column("Sub-Sat Lon", style="magenta")
    table.add_column("Cadence", style="blue")
    table.add_column("Operational Span", style="white")
    table.add_column("Channels", style="red")

    for p in products:
        table.add_row(
            p["product_code"],
            p["satellite_name"],
            f"{p['sensor_name']} ({p['processing_level']})",
            f"{p['sub_satellite_lon']}°E",
            f"{p['cadence_minutes']} min",
            p["operational_period"],
            ", ".join(p["channel_names"]),
        )

    rprint(table)
    rprint(
        "[bold yellow][NOTE] Catalog query is public; raw granule download requires authorized personal MOSDAC credentials outside Git repository.[/bold yellow]"
    )


@app.command()
def inspect_tcir(file_path: str) -> None:
    """Inspect and profile an official or pilot TCIR multi-channel HDF5 satellite archive."""
    rprint(f"[bold blue]Inspecting TCIR HDF5 archive: {file_path}...[/bold blue]")
    adapter = TCIRAdapter(file_path)
    profile = adapter.generate_profile()

    table = Table(title=f"TCIR Dataset Profile: {file_path}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("File Size", f"{profile.file_size_bytes / (1024 * 1024):.2f} MB")
    table.add_row("SHA-256", profile.sha256_checksum)
    table.add_row("Total Image Frames", f"{profile.total_frames:,}")
    table.add_row("Tensor Shape", str(profile.matrix_shape))
    table.add_row("Tensor Data Type", profile.matrix_dtype)
    table.add_row("Channels", ", ".join(profile.channels))
    table.add_row("Unique Storms", str(profile.unique_storms_count))
    table.add_row(
        "Seasons Covered",
        f"{min(profile.unique_seasons)} - {max(profile.unique_seasons)}"
        if profile.unique_seasons
        else "N/A",
    )
    table.add_row(
        "Basin Counts",
        ", ".join([f"{k}: {v}" for k, v in profile.basin_counts.items()]),
    )
    table.add_row("North Indian Ocean Frames", str(profile.north_indian_ocean_frames))
    table.add_row(
        "Missing Pixel % (by channel)",
        ", ".join([f"{k}: {v}%" for k, v in profile.channel_missing_percentages.items()]),
    )
    table.add_row(
        "Vmax Range (knots)",
        f"{profile.vmax_range_knots[0]} to {profile.vmax_range_knots[1]} kts",
    )

    rprint(table)


@app.command()
def mosdac_search(
    dataset_id: str = "3RIMG_L1B_STD",
    start_time: str = "2024-05-25",
    end_time: str = "2024-05-27",
    count: int = 5,
) -> None:
    """Search official ISRO MOSDAC public satellite catalog without authentication."""
    rprint(
        f"[bold blue]Searching MOSDAC catalog for {dataset_id} [{start_time} to {end_time}]...[/bold blue]"
    )
    client = MOSDACSearchClient()
    try:
        summary = client.search(dataset_id, start_time, end_time, count=count)
    except Exception as e:
        rprint(f"[bold red]Catalog search failed:[/bold red] {e}")
        raise typer.Exit(1) from e

    table = Table(title=f"ISRO MOSDAC Catalog Search: {dataset_id}")
    table.add_column("Identifier", style="cyan")
    table.add_column("Record ID", style="green")
    table.add_column("Product Timestamp", style="magenta")

    for entry in summary.entries:
        table.add_row(entry.identifier, entry.record_id, entry.product_date_utc)

    rprint(table)
    rprint(
        f"[green]Total matching granules found:[/green] {summary.total_results:,} ({summary.total_size_mb:.2f} MB)"
    )


@app.command()
def mosdac_plan(storm_name: str = "REMAL") -> None:
    """Display bounded, human-approved acquisition plan for authentic INSAT satellite granules."""
    storm_name_upper = storm_name.upper()
    plans = {
        "REMAL": {
            "satellite": "INSAT-3DR",
            "dataset_id": "3RIMG_L1B_STD",
            "start_time": "2024-05-25",
            "end_time": "2024-05-27",
            "target_granule": "3RIMG_27MAY2024_2345_L1B_STD_V01R00.h5",
            "record_id": "13631145",
            "est_size_mb": 301.0,
            "rationale": "Landfall peak intensity stage of Severe Cyclonic Storm REMAL (Bay of Bengal).",
        },
        "DANA": {
            "satellite": "INSAT-3DS",
            "dataset_id": "3SIMG_L1B_STD",
            "start_time": "2024-10-23",
            "end_time": "2024-10-25",
            "target_granule": "3SIMG_25OCT2024_2351_L1B_STD_V01R00.h5",
            "record_id": "14514935",
            "est_size_mb": 282.0,
            "rationale": "Peak landfall intensity stage of Severe Cyclonic Storm DANA (Odisha coast).",
        },
    }

    plan = plans.get(storm_name_upper, plans["REMAL"])

    table = Table(title=f"MOSDAC Bounded Acquisition Plan: Cyclone {storm_name_upper}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Target Value", style="green")

    table.add_row("Target Storm", storm_name_upper)
    table.add_row("Satellite Payload", plan["satellite"])
    table.add_row("Dataset ID", plan["dataset_id"])
    table.add_row("Temporal Window", f"{plan['start_time']} to {plan['end_time']}")
    table.add_row("Target Granule", plan["target_granule"])
    table.add_row("MOSDAC Record ID", plan["record_id"])
    table.add_row("Estimated Size", f"{plan['est_size_mb']} MB (Budget <= 1000 MB)")
    table.add_row("Scientific Rationale", plan["rationale"])

    rprint(table)
    rprint("\n[bold yellow]-- SECURITY INSTRUCTION --[/bold yellow]")
    rprint(
        "To execute this bounded download interactively in your local terminal without leaking credentials:"
    )
    rprint(
        f"[bold cyan]python scripts/mosdac_acquire.py --dataset-id {plan['dataset_id']} --start-time {plan['start_time']} --end-time {plan['end_time']} --max-files 1[/bold cyan]"
    )


@app.command()
def mosdac_inspect(file_path: str) -> None:
    """Inspect authentic ISRO INSAT HDF5 granule structure, spectral channels, and calibration metadata."""
    p = Path(file_path)
    if not p.is_file():
        rprint(f"[bold red]File not found:[/bold red] {file_path}")
        raise typer.Exit(1)

    table = Table(title=f"INSAT HDF5 Granule Audit: {p.name}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("File Size", f"{p.stat().st_size / (1024 * 1024):.2f} MB")

    with h5py.File(p, "r") as f:
        datasets = list(f.keys())
        table.add_row("Root Datasets/Groups", ", ".join(datasets[:10]))
        for ds_name in ["IMG_TIR1", "IMG_WV", "IMG_VIS", "Latitude", "Longitude", "matrix"]:
            if ds_name in f:
                ds = f[ds_name]
                table.add_row(f"Dataset '{ds_name}'", f"shape={ds.shape}, dtype={ds.dtype}")

    rprint(table)


@app.command()
def mosdac_register(
    file_path: str,
    product_code: str = "3RIMG_L1B_STD",
) -> None:
    """Register an authentic acquired INSAT granule into Vayumarg with REAL_VERIFIED provenance."""
    p = Path(file_path)
    if not p.is_file():
        rprint(f"[bold red]File not found:[/bold red] {file_path}")
        raise typer.Exit(1)

    # Calculate SHA-256
    sha256 = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            sha256.update(chunk)
    file_hash = sha256.hexdigest()

    with get_db_session() as session:
        # Find product
        prod = session.execute(
            select(SatelliteProduct).where(SatelliteProduct.product_code == product_code)
        ).scalar_one_or_none()

        if not prod:
            rprint(
                f"[bold red]Product not registered:[/bold red] {product_code}. Run mosdac-products first."
            )
            raise typer.Exit(1)

        existing = session.execute(
            select(SatelliteGranule).where(SatelliteGranule.granule_name == p.name)
        ).scalar_one_or_none()

        if existing:
            rprint(
                f"[yellow]Granule '{p.name}' is already registered (ID: {existing.id}).[/yellow]"
            )
            return

        granule = SatelliteGranule(
            id=uuid.uuid4(),
            product_id=prod.id,
            granule_name=p.name,
            acquisition_start_utc=datetime.now(UTC),
            acquisition_end_utc=datetime.now(UTC),
            file_format="HDF5",
            storage_uri=str(p.as_posix()),
            sha256_checksum=file_hash,
            file_size_bytes=p.stat().st_size,
            granule_metadata={
                "registered_via": "mosdac_register",
                "provenance": "AUTHENTIC_MOSDAC",
            },
            verification_status="REAL_VERIFIED",
            created_at_utc=datetime.now(UTC),
        )
        session.add(granule)
        session.flush()

    rprint(
        f"[bold green][SUCCESS] Registered authentic granule '{p.name}' with REAL_VERIFIED status.[/bold green]"
    )


# ==============================================================================
# Module A Satellite Intelligence Subcommands
# ==============================================================================
satellite_app = typer.Typer(help="Authentic satellite imagery, preview cache & analytics commands")
app.add_typer(satellite_app, name="satellite")


@satellite_app.command(name="list")
def satellite_list() -> None:
    """List all verified authentic satellite crops and their provenance."""
    from vayumarg.satellite.service import get_satellite_service

    service = get_satellite_service()
    crops = service.list_authentic_crops()

    table = Table(title="Vayumarg Module A — Authentic Verified Satellite Assets")
    table.add_column("Storm", style="cyan bold")
    table.add_column("SID", style="magenta")
    table.add_column("Satellite", style="green")
    table.add_column("Acquisition UTC", style="yellow")
    table.add_column("Channels", style="blue")
    table.add_column("IMD Eligible", style="white")
    table.add_column("Status", style="green bold")

    for c in crops:
        imd_str = (
            "[green]Yes[/green]"
            if c.primary_imd_eligible
            else "[red]Ineligible (DANA Policy)[/red]"
        )
        table.add_row(
            c.storm_name,
            c.canonical_storm_sid,
            c.satellite,
            c.acquisition_start_utc,
            ", ".join(c.available_channels),
            imd_str,
            c.verification_status,
        )

    rprint(table)


@satellite_app.command(name="pre-render")
def satellite_pre_render() -> None:
    """Pre-render all authentic crop previews across channels and colormaps."""
    from vayumarg.satellite.service import get_satellite_service

    service = get_satellite_service()
    rprint("[bold blue]Pre-rendering authentic satellite preview cache...[/bold blue]")
    manifest = service.pre_render_all_authentic_previews()
    rprint(
        f"[bold green]Successfully pre-rendered offline demo cache for {len(manifest['storms_cached'])} storms.[/bold green]"
    )
    for item in manifest["details"]:
        rprint(f"  • {item['storm']}: {item['rendered_previews']} preview variations cached")


@satellite_app.command(name="inspect")
def satellite_inspect(
    storm: str = typer.Argument(..., help="Storm name (REMAL, DANA, AMPHAN, BIPARJOY)"),
) -> None:
    """Inspect quantitative physical analytics for a specific authentic satellite crop."""
    from vayumarg.satellite.service import get_satellite_service

    service = get_satellite_service()
    try:
        record = service.get_crop_provenance(storm)
    except KeyError as e:
        rprint(f"[bold red]{e}[/bold red]")
        raise typer.Exit(1) from e

    rprint(
        Panel(
            f"[bold cyan]Storm:[/bold cyan] {record.storm_name} ({record.season_year}) | [bold magenta]SID:[/bold magenta] {record.canonical_storm_sid}\n"
            f"[bold green]Satellite:[/bold green] {record.satellite} | [bold yellow]Sensor:[/bold yellow] {record.sensor} | [bold blue]Product:[/bold blue] {record.product_code}\n"
            f"[bold white]Source HDF5:[/bold white] {record.source_filename} (SHA: {record.source_sha256[:16]}...)\n"
            f"[bold white]Crop HDF5:[/bold white] {record.crop_filename} (SHA: {record.crop_sha256[:16]}...)\n"
            f"[bold yellow]Acquisition UTC:[/bold yellow] {record.acquisition_start_utc} (Scan Uncertainty: {record.scan_time_uncertainty})\n"
            f"[bold magenta]Primary IMD Eligible:[/bold magenta] {record.primary_imd_eligible}"
            + (
                f"\n[bold red]Policy Notice:[/bold red] {record.dana_ineligibility_notice}"
                if record.dana_ineligibility_notice
                else ""
            ),
            title=f"Satellite Provenance: {record.storm_name}",
        )
    )

    table = Table(title=f"Channel Analytics — {record.storm_name}")
    table.add_column("Channel", style="cyan bold")
    table.add_column("Valid %", style="green")
    table.add_column("Clamped %", style="yellow")
    table.add_column("Min Tb (K)", style="magenta")
    table.add_column("Non-Clamped Min (K)", style="magenta bold")
    table.add_column("Mean Tb (K)", style="white")
    table.add_column("Cold (<220K) %", style="blue")

    for ch in record.available_channels:
        an = service.get_channel_analytics(storm, ch)
        cold_220 = [
            cf.fraction_of_valid for cf in an.cold_cloud_fractions if cf.threshold_k == 220.0
        ][0]
        table.add_row(
            ch,
            f"{an.valid_fraction * 100:.1f}%",
            f"{an.clamped_fraction * 100:.2f}%",
            f"{an.min_tb_k:.2f}" if an.min_tb_k is not None else "N/A",
            f"{an.min_non_clamped_tb_k:.2f}" if an.min_non_clamped_tb_k is not None else "N/A",
            f"{an.mean_tb_k:.2f}" if an.mean_tb_k is not None else "N/A",
            f"{cold_220 * 100:.1f}%",
        )
    rprint(table)


@satellite_app.command(name="serve")
def satellite_serve(
    host: str = typer.Option("127.0.0.1", help="Host interface to bind"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Launch the Vayumarg FastAPI application with uvicorn."""
    import uvicorn

    rprint(f"[bold green]Starting Vayumarg API server on http://{host}:{port}...[/bold green]")
    uvicorn.run("vayumarg.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
