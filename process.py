#!/usr/bin/env python3
"""
Improved Argo NetCDF Parser - Dynamic File Processing
Receives any Argo file and automatically parses and inserts data
"""

from parser import UltimateArgoNetCDFParser
import os
import sys
from pathlib import Path

def process_argo_file(file_path, verify=True, verbose=True):
    """
    Process any Argo NetCDF file - automatically detects type and processes

    Args:
        file_path (str): Path to the NetCDF file
        verify (bool): Whether to verify data insertion after processing
        verbose (bool): Whether to print detailed progress information

    Returns:
        dict: Processing results with success status and details
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }

        # Initialize parser
        if verbose:
            print(f"🔄 Initializing parser...")

        parser = UltimateArgoNetCDFParser()

        # Process the file
        if verbose:
            print(f"📂 Processing file: {os.path.basename(file_path)}")
            print(f"📍 Full path: {file_path}")

        result = parser.process_argo_file(file_path)

        if verbose:
            print(f"✅ File processing completed")

        # Verify data insertion if requested
        verification_result = None
        if verify:
            if verbose:
                print(f"🔍 Verifying data insertion...")

            verification_result = parser.verify_data_insertion()

            if verbose:
                print(f"✅ Data verification completed")

        return {
            "success": True,
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "processing_result": result,
            "verification_result": verification_result,
            "parser": parser
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "file_name": os.path.basename(file_path) if os.path.exists(file_path) else "Unknown"
        }

def process_multiple_files(file_paths, verify=True, verbose=True):
    """
    Process multiple Argo NetCDF files

    Args:
        file_paths (list): List of file paths to process
        verify (bool): Whether to verify data insertion
        verbose (bool): Whether to print progress

    Returns:
        dict: Results for all files processed
    """
    results = {
        "total_files": len(file_paths),
        "successful": 0,
        "failed": 0,
        "results": []
    }

    if verbose:
        print(f"🚀 Processing {len(file_paths)} files...")

    for i, file_path in enumerate(file_paths, 1):
        if verbose:
            print(f"\n📁 [{i}/{len(file_paths)}] Processing: {os.path.basename(file_path)}")

        result = process_argo_file(file_path, verify=verify, verbose=verbose)
        results["results"].append(result)

        if result["success"]:
            results["successful"] += 1
            if verbose:
                print(f"✅ [{i}/{len(file_paths)}] Success: {os.path.basename(file_path)}")
        else:
            results["failed"] += 1
            if verbose:
                print(f"❌ [{i}/{len(file_paths)}] Failed: {os.path.basename(file_path)}")
                print(f"   Error: {result['error']}")

    if verbose:
        print(f"\n🎯 SUMMARY:")
        print(f"   Total: {results['total_files']}")
        print(f"   ✅ Successful: {results['successful']}")
        print(f"   ❌ Failed: {results['failed']}")

    return results

def process_directory(directory_path, pattern="*.nc", verify=True, verbose=True):
    """
    Process all NetCDF files in a directory

    Args:
        directory_path (str): Path to directory containing NetCDF files
        pattern (str): File pattern to match (default: "*.nc")
        verify (bool): Whether to verify data insertion
        verbose (bool): Whether to print progress

    Returns:
        dict: Processing results for all files found
    """
    try:
        # Find all matching files
        directory = Path(directory_path)
        if not directory.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}"
            }

        files = list(directory.glob(pattern))
        file_paths = [str(f) for f in files]

        if not file_paths:
            return {
                "success": False,
                "error": f"No files matching pattern '{pattern}' found in {directory_path}"
            }

        if verbose:
            print(f"📂 Found {len(file_paths)} files in {directory_path}")
            print(f"🔍 Pattern: {pattern}")

        # Process all files
        return process_multiple_files(file_paths, verify=verify, verbose=verbose)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "directory": directory_path
        }

def interactive_file_processor():
    """
    Interactive mode for processing files
    """
    print("🌊 ARGO NETCDF FILE PROCESSOR")
    print("=" * 50)

    while True:
        print("\nOptions:")
        print("1. Process single file")
        print("2. Process multiple files")
        print("3. Process directory")
        print("4. Exit")

        choice = input("\nChoose option (1-4): ").strip()

        if choice == "1":
            file_path = input("Enter file path: ").strip()
            result = process_argo_file(file_path)

            if result["success"]:
                print(f"✅ Successfully processed: {result['file_name']}")
            else:
                print(f"❌ Failed to process: {result['error']}")

        elif choice == "2":
            print("Enter file paths (one per line, empty line to finish):")
            file_paths = []
            while True:
                path = input().strip()
                if not path:
                    break
                file_paths.append(path)

            if file_paths:
                results = process_multiple_files(file_paths)
                print(f"\n✅ Processed {results['successful']}/{results['total_files']} files successfully")

        elif choice == "3":
            directory = input("Enter directory path: ").strip()
            pattern = input("Enter file pattern (default: *.nc): ").strip() or "*.nc"

            results = process_directory(directory, pattern)
            if results.get("success", True):
                print(f"\n✅ Processed {results['successful']}/{results['total_files']} files successfully")
            else:
                print(f"❌ Error: {results['error']}")

        elif choice == "4":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")

# Command line interface
def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage examples:")
        print("  python argo_processor.py <file_path>")
        print("  python argo_processor.py <file1> <file2> <file3>")
        print("  python argo_processor.py --directory <dir_path>")
        print("  python argo_processor.py --interactive")
        return

    if sys.argv[1] == "--interactive":
        interactive_file_processor()
        return

    if sys.argv[1] == "--directory":
        if len(sys.argv) < 3:
            print("❌ Please provide directory path")
            return

        directory_path = sys.argv[2]
        pattern = sys.argv[3] if len(sys.argv) > 3 else "*.nc"

        results = process_directory(directory_path, pattern)
        if results.get("success", True):
            print(f"✅ Successfully processed {results['successful']}/{results['total_files']} files")
        else:
            print(f"❌ Error: {results['error']}")
        return

    # Process files provided as arguments
    file_paths = sys.argv[1:]

    if len(file_paths) == 1:
        # Single file
        result = process_argo_file(file_paths[0])
        if result["success"]:
            print(f"✅ Successfully processed: {result['file_name']}")
        else:
            print(f"❌ Failed: {result['error']}")
    else:
        # Multiple files
        results = process_multiple_files(file_paths)
        print(f"✅ Processed {results['successful']}/{results['total_files']} files successfully")

if __name__ == "__main__":
    main()

# Example usage functions
def example_usage():
    """Examples of how to use the new interface"""

    # Example 1: Process single file
    result = process_argo_file('1900122_Rtraj.nc')
    if result["success"]:
        print("File processed successfully!")

    # Example 2: Process multiple files
    files = [
        '1900122_Rtraj.nc',
        '13859_prof.nc',
        '13859_meta.nc'
    ]
    results = process_multiple_files(files)

    # Example 3: Process all NetCDF files in a directory
    results = process_directory('./argo_data/', pattern="*.nc")

    # Example 4: Quiet processing (no verbose output)
    result = process_argo_file('1900122_Rtraj.nc', verify=True, verbose=False)
