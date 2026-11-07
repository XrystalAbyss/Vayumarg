"""Interactive secure acquisition script for ISRO MOSDAC satellite imagery.

Prompts user for MOSDAC credentials in the terminal (via getpass) without saving them,
executes the official MOSDAC acquisition client in a temporary isolated environment,
and registers acquired authentic HDF5 granules in Vayumarg with REAL_VERIFIED provenance.
Supports exact granule selection via --granule-id.
"""

import argparse
import getpass
import os
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table

from vayumarg.core.logging import get_logger
from vayumarg.ingestion.mosdac_client import MOSDACSearchClient, SecureMOSDACDownloader

console = Console()
logger = get_logger("vayumarg.mosdac_acquire")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vayumarg Secure MOSDAC Satellite Data Acquisition Tool"
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="3RIMG_L1B_STD",
        help="MOSDAC dataset ID (e.g., 3RIMG_L1B_STD, 3SIMG_L1B_STD)",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        default="2024-05-26",
        help="Acquisition start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-time",
        type=str,
        default="2024-05-26",
        help="Acquisition end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--granule-id",
        type=str,
        default=None,
        help="Exact MOSDAC granule ID (numeric record ID e.g. 13623453 or HDF5 identifier)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=1,
        help="Maximum number of files to acquire (budget constraint <= 3)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/satellite/insat_real",
        help="Target directory for downloaded granules",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="MOSDAC username or email (optional override, otherwise prompted)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip interactive Y/N confirmation prompt",
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Search MOSDAC catalog only without authenticating or downloading",
    )

    args = parser.parse_args()

    console.print(
        "[bold cyan]============================================================[/bold cyan]"
    )
    console.print(
        "[bold cyan]      VAYUMARG SECURE MOSDAC SATELLITE ACQUISITION         [/bold cyan]"
    )
    console.print(
        "[bold cyan]============================================================[/bold cyan]\n"
    )

    # Enforce count=1 when targeting exact granule
    if args.granule_id:
        args.max_files = 1

    # 1. Unauthenticated Catalog Search & Verification
    client = MOSDACSearchClient()
    console.print(
        f"[bold yellow]Querying MOSDAC catalog for {args.dataset_id} ({args.start_time} to {args.end_time})...[/bold yellow]"
    )
    try:
        summary = client.search(
            dataset_id=args.dataset_id,
            start_time=args.start_time,
            end_time=args.end_time,
            count=args.max_files if not args.granule_id else None,
            granule_id=args.granule_id,
        )
    except Exception as e:
        console.print(f"[bold red]Catalog search failed:[/bold red] {e}")
        sys.exit(1)

    table = Table(title=f"MOSDAC Catalog Search: {args.dataset_id}")
    table.add_column("Filename / Identifier", style="cyan")
    table.add_column("Record ID (gId)", style="green")
    table.add_column("Product Timestamp", style="magenta")

    for entry in summary.entries:
        table.add_row(entry.identifier, entry.record_id, entry.product_date_utc)

    console.print(table)
    console.print(
        f"[green]Matching granules verified:[/green] {summary.total_results:,} ({summary.total_size_mb:.2f} MB)"
    )

    if args.search_only:
        console.print(
            "\n[bold green][SUCCESS] Search-only mode completed. No credentials required or written.[/bold green]"
        )
        sys.exit(0)

    # 2. Pre-Download Verification and Plan Summary
    selected_entry = summary.entries[0] if summary.entries else None
    if not selected_entry:
        console.print("[bold red]No valid candidate granules found. Aborting.[/bold red]")
        sys.exit(1)

    out_path = Path(args.output_dir).resolve()
    total_b, used_b, free_b = shutil.disk_usage(out_path.anchor or "C:\\")
    free_gb = free_b / (1024**3)

    plan_table = Table(title="Proposed Authenticated Acquisition Plan")
    plan_table.add_column("Property", style="cyan")
    plan_table.add_column("Value", style="green")

    plan_table.add_row("Selected Granule Identifier", selected_entry.identifier)
    plan_table.add_row("MOSDAC Record ID (gId)", selected_entry.record_id)
    plan_table.add_row("Product Timestamp (UTC)", selected_entry.product_date_utc)
    plan_table.add_row(
        "Estimated Download Size", f"~{summary.total_size_mb:.1f} MB (Budget < 1000 MB)"
    )
    plan_table.add_row("Local Destination Path", str(out_path))
    plan_table.add_row("Drive Free Capacity", f"{free_gb:.1f} GB")

    console.print("\n", plan_table)

    # Explicit Affirmative Terminal Confirmation
    if not args.yes:
        confirm = (
            input("\nProceed with authenticated acquisition of this granule? [y/N]: ")
            .strip()
            .lower()
        )
        if confirm not in ("y", "yes"):
            console.print(
                "[yellow]Download cancelled by operator. No credentials requested.[/yellow]"
            )
            sys.exit(0)

    # 3. Secure Credential Retrieval
    username = (
        args.username
        or os.getenv("MOSDAC_USERNAME")
        or input("\nEnter MOSDAC Username / Email: ").strip()
    )
    if not username:
        console.print("[bold red]Username cannot be empty. Aborting.[/bold red]")
        sys.exit(1)

    password = os.getenv("MOSDAC_PASSWORD")
    if not password:
        password = getpass.getpass("Enter MOSDAC Password (input hidden): ")
    if not password:
        console.print("[bold red]Password cannot be empty. Aborting.[/bold red]")
        sys.exit(1)

    # 4. Execution
    downloader = SecureMOSDACDownloader()
    console.print(
        f"\n[bold green]Initiating bounded download of granule '{selected_entry.identifier}'...[/bold green]"
    )
    try:
        acquired = downloader.execute_bounded_download(
            username=username,
            password=password,
            dataset_id=args.dataset_id,
            start_time=args.start_time,
            end_time=args.end_time,
            download_target_dir=out_path,
            max_files=1,
            granule_id=selected_entry.record_id,
        )
        console.print(
            f"\n[bold green][SUCCESS] Acquisition completed! {len(acquired)} file(s) saved.[/bold green]"
        )
        for f in acquired:
            console.print(f" - [cyan]{f}[/cyan] ({f.stat().st_size / (1024 * 1024):.2f} MB)")
    except PermissionError as pe:
        console.print(f"\n[bold red]Authentication Error:[/bold red] {pe}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Acquisition Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
