#!/usr/bin/env python3
"""
Initialize feedback tables for the learning system.

Run this script once before starting the backend server to create the new feedback tables:
    python backend/init_feedback_tables.py

This will create the following new tables:
- outfit_ratings
- recommendation_feedback
- item_usage
- model_metrics
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.database import engine
from database import models

def init_feedback_tables():
    """Create feedback tables using SQLAlchemy ORM."""
    try:
        print("Initializing feedback tables...")
        
        # Create all tables that are defined in models but don't exist yet
        models.Base.metadata.create_all(bind=engine)
        
        print("✓ Successfully created feedback tables:")
        print("  - outfit_ratings")
        print("  - recommendation_feedback")
        print("  - item_usage")
        print("  - model_metrics")
        print("\nTables are ready! You can now start using the feedback endpoints.")
        
    except Exception as e:
        print(f"✗ Error initializing tables: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_feedback_tables()
