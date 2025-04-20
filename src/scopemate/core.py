#!/usr/bin/env python3
"""scopemate - CLI Tool for Purpose/Scope/Outcome planning (Legacy module)

This is a legacy module maintained for backward compatibility.
All functionality has been moved to more specialized modules.
"""
import sys

def interactive_builder():
    """
    Legacy function that redirects to the new implementation.
    
    This is kept for backward compatibility. New code should use TaskEngine directly.
    """
    from .engine import interactive_builder as new_builder
    new_builder()

if __name__ == "__main__":
    try:
        interactive_builder()
    except KeyboardInterrupt:
        print("\nOperation cancelled. Progress saved in checkpoint.")
        sys.exit(1) 