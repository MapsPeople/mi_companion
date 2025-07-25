#!/usr/bin/env python3
"""
QGIS Processing Command Line Interface
This script allows running QGIS processing algorithms from the command line.
"""

import argparse
import os
import sys

from qgis.analysis import QgsNativeAlgorithms
from qgis.core import (
    QgsApplication,
    QgsProcessingFeedback,
    QgsProcessingUtils,
)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run QGIS processing algorithms from command line"
    )
    parser.add_argument("algorithm", help="Algorithm name (e.g., 'qgis:buffer')")
    parser.add_argument("--params", help="Parameters in JSON format", default="{}")
    parser.add_argument("--list", action="store_true", help="List available algorithms")
    parser.add_argument("--qgis_prefix_path", help="QGIS installation prefix path")
    args = parser.parse_args()

    # Initialize QGIS application without GUI
    qgis_prefix = args.qgis_prefix_path or os.environ.get("QGIS_PREFIX_PATH")
    if not qgis_prefix:
        print(
            "Error: QGIS prefix path not specified. Use --qgis_prefix_path or set QGIS_PREFIX_PATH environment variable"
        )
        sys.exit(1)

    app = QgsApplication([], False)
    app.setPrefixPath(qgis_prefix, True)
    app.initQgis()

    # Add the processing framework
    sys.path.append(os.path.join(qgis_prefix, "python/plugins"))
    import processing
    from processing.core.Processing import Processing

    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    # Create a feedback object
    feedback = QgsProcessingFeedback()

    # List algorithms if requested
    if args.list:
        for alg in QgsApplication.processingRegistry().algorithms():
            print(f"{alg.id()} - {alg.displayName()}")
        sys.exit(0)

    # Run the specified algorithm
    try:
        import json

        params = json.loads(args.params)
        processing.run(args.algorithm, params, feedback=feedback)
        print("Algorithm execution completed successfully")
    except Exception as e:
        print(f"Error running algorithm: {e}")
        sys.exit(1)
    finally:
        # Clean up
        app.exitQgis()


if __name__ == "__main__":
    main()
