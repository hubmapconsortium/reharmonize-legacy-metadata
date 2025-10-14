"""
Command-line interface for the metadata transformer using Click.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from metadata_transformer.exceptions import MetadataTransformerError
from metadata_transformer.field_mapper import FieldMappings
from metadata_transformer.output_generator import OutputGenerator
from metadata_transformer.patch_applier import Patches
from metadata_transformer.processing_log_provider import ProcessingLogProvider
from metadata_transformer.schema_applier import Schema
from metadata_transformer.transformer import MetadataTransformer
from metadata_transformer.value_mapper import ValueMappings


@click.command()
@click.option(
    "--field-mapping-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
    help="JSON field mapping file",
)
@click.option(
    "--value-mapping-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Directory containing JSON value mapping files",
)
@click.option(
    "--target-schema-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to target schema JSON file",
)
@click.option(
    "--patch-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing JSON patch files for conditional patching (optional)",
)
@click.option(
    "--patch-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Single JSON patch file for conditional patching (optional)",
)
@click.option(
    "--input-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing legacy metadata files (for bulk processing)",
)
@click.option(
    "--input-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Single legacy metadata file to process",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Directory where transformed files will be written",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(
    field_mapping_file: Path,
    value_mapping_dir: Path,
    target_schema_file: Path,
    patch_dir: Optional[Path],
    patch_file: Optional[Path],
    input_dir: Optional[Path],
    input_file: Optional[Path],
    output_dir: Path,
    verbose: bool,
) -> None:
    """
    Transform legacy metadata objects into new schema-compliant structures.

    This tool processes legacy metadata files through a 5-phase transformation:
    0. Conditional patching - Apply patches based on metadata conditions (optional)
    1. Field mapping - Transform legacy field names to target schema field names
    2. Value mapping - Transform legacy field values to target schema values
    3. Schema compliance - Ensure output conforms to target schema
    4. Output generation - Write transformed data with comprehensive logging

    Either --input-dir (for bulk processing) or --input-file (for single file)
    must be specified, but not both.
    """
    # Validate input arguments
    if not input_dir and not input_file:
        click.echo(
            "Error: Either --input-dir or --input-file must be specified", err=True
        )
        sys.exit(1)

    if input_dir and input_file:
        click.echo(
            "Error: --input-dir and --input-file are mutually exclusive", err=True
        )
        sys.exit(1)

    try:
        # Initialize components
        if verbose:
            click.echo("Initializing metadata transformer components...")

        field_mappings = FieldMappings()
        value_mappings = ValueMappings()
        schema = Schema()
        patches = Patches()
        output_generator = OutputGenerator()

        # Load mappings and schema
        if verbose:
            click.echo(f"Loading field mappings from: {field_mapping_file}")
        try:
            field_mappings.load_field_mapping_file(field_mapping_file)
            if verbose:
                click.echo(
                    f"Loaded {len(field_mappings.get_all_mappings())} field mappings"
                )
        except Exception as e:
            click.echo(f"Warning: Error loading field mappings: {e}", err=True)

        if verbose:
            click.echo(f"Loading value mappings from: {value_mapping_dir}")
        try:
            json_files = list(value_mapping_dir.glob("*.json"))
            if verbose:
                click.echo(f"Found {len(json_files)} value mapping files")
            value_mappings.load_value_mappings(value_mapping_dir)
            total_fields = len(value_mappings.get_all_mappings())
            total_mappings = sum(
                len(mappings) for mappings in value_mappings.get_all_mappings().values()
            )
            if verbose:
                click.echo(
                    f"Loaded value mappings for {total_fields} fields with {total_mappings} total mappings"
                )
        except Exception as e:
            click.echo(f"Warning: Error loading value mappings: {e}", err=True)

        if verbose:
            click.echo(f"Loading target schema from: {target_schema_file}")
        try:
            schema.load_schema(target_schema_file)
            schema_fields = schema.get_schema_fields()
            required_fields = schema.get_required_fields()
            if verbose:
                click.echo(
                    f"Loaded schema with {len(schema_fields)} fields ({len(required_fields)} required)"
                )
        except Exception as e:
            click.echo(f"Warning: Error loading schema: {e}", err=True)

        # Load patches from directory if provided
        if patch_dir:
            if verbose:
                click.echo(f"Loading patches from directory: {patch_dir}")
            try:
                patches.load_patches(patch_dir)
                patches_count = patches.get_loaded_patches_count()
                if verbose:
                    click.echo(f"Loaded {patches_count} patches from directory")
            except Exception as e:
                click.echo(
                    f"Warning: Error loading patches from directory: {e}", err=True
                )

        # Load patches from file if provided
        if patch_file:
            if verbose:
                click.echo(f"Loading patches from file: {patch_file}")
            try:
                patches.load_patch_file(patch_file)
                patches_count = patches.get_loaded_patches_count()
                if verbose:
                    click.echo(f"Loaded {patches_count} total patches")
            except Exception as e:
                click.echo(f"Warning: Error loading patches from file: {e}", err=True)

        if not patch_dir and not patch_file and verbose:
            click.echo("No patches specified - skipping conditional patching")

        # Initialize log provider
        log_provider = ProcessingLogProvider()

        # Initialize transformer
        transformer = MetadataTransformer(
            patches, field_mappings, value_mappings, schema, log_provider
        )

        # Process files
        if input_file:
            # Single file processing
            _process_single_file(
                transformer, output_generator, input_file, output_dir, verbose
            )
        elif input_dir:
            # Bulk processing
            _process_bulk_files(
                transformer, output_generator, input_dir, output_dir, verbose
            )

        click.echo("✅ Metadata transformation completed successfully!")

    except MetadataTransformerError as e:
        click.echo(f"❌ Transformation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


def _process_single_file(
    transformer: MetadataTransformer,
    output_generator: OutputGenerator,
    input_file: Path,
    output_dir: Path,
    verbose: bool,
) -> None:
    """Process a single legacy metadata file."""
    if verbose:
        click.echo(f"Processing single file: {input_file}")

    # Transform the file
    result = transformer.transform_metadata_file(input_file)

    # Write output
    output_file = output_generator.write_output_file(result, input_file, output_dir)

    # Print summary
    metadata_objects = result.get("migrated_metadata", [])
    object_count = len(metadata_objects) if isinstance(metadata_objects, list) else 1
    log_entries = len(result.get("processing_log", []))

    click.echo(f"📄 Processed: {input_file.name}")
    click.echo(f"📊 Objects transformed: {object_count}")
    click.echo(f"📝 Log entries: {log_entries}")
    click.echo(f"💾 Output written to: {output_file}")


def _process_bulk_files(
    transformer: MetadataTransformer,
    output_generator: OutputGenerator,
    input_dir: Path,
    output_dir: Path,
    verbose: bool,
) -> None:
    """Process all JSON files in a directory."""
    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        click.echo(f"❌ No JSON files found in: {input_dir}", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"Processing {len(json_files)} files from: {input_dir}")

    processed_files: List[Dict[str, Any]] = []

    with click.progressbar(json_files, label="Processing files") as files:
        for input_file in files:
            try:
                # Transform the file
                result = transformer.transform_metadata_file(input_file)

                # Write output
                output_file = output_generator.write_output_file(
                    result, input_file, output_dir
                )

                # Track results
                metadata_objects = result.get("migrated_metadata", [])
                object_count = (
                    len(metadata_objects) if isinstance(metadata_objects, list) else 1
                )

                processed_files.append(
                    {
                        "input_file": str(input_file),
                        "output_file": str(output_file),
                        "status": "success",
                        "objects_processed": object_count,
                        "log_entries": len(result.get("processing_log", [])),
                    }
                )

            except Exception as e:
                processed_files.append(
                    {
                        "input_file": str(input_file),
                        "output_file": None,
                        "status": "failed",
                        "error": str(e),
                        "objects_processed": 0,
                        "log_entries": 0,
                    }
                )

                if verbose:
                    click.echo(f"❌ Failed to process {input_file.name}: {e}")

    # Print summary
    successful = len([f for f in processed_files if f["status"] == "success"])
    failed = len(processed_files) - successful
    total_objects = sum(f["objects_processed"] for f in processed_files)

    click.echo("\n📊 Bulk Processing Summary:")
    click.echo(f"   Files processed: {len(processed_files)}")
    click.echo(f"   Successful: {successful}")
    click.echo(f"   Failed: {failed}")
    click.echo(f"   Total objects transformed: {total_objects}")


if __name__ == "__main__":
    main()
