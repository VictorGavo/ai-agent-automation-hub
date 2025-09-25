#!/usr/bin/env python3
"""
Example usage of the DevBibleReader class

This script demonstrates how to use the DevBibleReader to manage
development guidelines for different agent task types.
"""

import sys
import os

# Add the parent directory to the path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dev_bible_reader import DevBibleReader, enforce_dev_bible_reading

def main():
    """Main example function demonstrating DevBibleReader usage."""
    
    # Initialize the reader with dev_bible path
    try:
        reader = DevBibleReader("dev_bible")
        print("✓ DevBibleReader initialized successfully")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    
    print("\n" + "="*60)
    print("DEVBIBLE READER DEMONSTRATION")
    print("="*60)
    
    # 1. Show available task types and their required reading
    print("\n1. TASK TYPES AND REQUIRED READING:")
    print("-" * 40)
    
    task_types = ["pre_task", "backend", "database", "testing", "documentation"]
    
    for task_type in task_types:
        try:
            files = reader.get_required_reading(task_type)
            print(f"\n{task_type.upper()}:")
            for i, file_path in enumerate(files, 1):
                print(f"  {i}. {file_path}")
        except ValueError as e:
            print(f"  Error: {e}")
    
    # 2. Validate agent preparation
    print("\n\n2. AGENT PREPARATION VALIDATION:")
    print("-" * 40)
    reader.validate_agent_prep("ExampleBackendAgent", "backend")
    
    # 3. Read a specific guideline
    print("\n3. READING SPECIFIC GUIDELINES:")
    print("-" * 40)
    
    sample_file = "core/_agent_quick_start.md"
    content = reader.read_guidelines(sample_file)
    
    if content:
        print(f"✓ Successfully read {sample_file}")
        print(f"  Content length: {len(content)} characters")
        print(f"  First 150 characters: {content[:150]}...")
    else:
        print(f"✗ Failed to read {sample_file}")
    
    # 4. Demonstrate enforce_dev_bible_reading helper
    print("\n\n4. COMPLETE GUIDELINES LOADING:")
    print("-" * 40)
    
    guidelines = enforce_dev_bible_reading("DemoAgent", "testing")
    
    print(f"✓ Loaded complete guidelines for testing tasks")
    print(f"  Total content length: {len(guidelines)} characters")
    print(f"  Guidelines ready for agent context")
    
    # 5. Show error handling
    print("\n\n5. ERROR HANDLING DEMONSTRATION:")
    print("-" * 40)
    
    try:
        # Try invalid task type
        reader.get_required_reading("invalid_task")
    except ValueError as e:
        print(f"✓ Proper error handling for invalid task type: {e}")
    
    # Try reading non-existent file
    content = reader.read_guidelines("non_existent_file.md")
    if content is None:
        print("✓ Proper handling of non-existent files (returns None)")
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())