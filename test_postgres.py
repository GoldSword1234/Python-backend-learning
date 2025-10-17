#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script

This script tests the database connection and provides detailed feedback.
Run this to diagnose any connection issues.
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_psycopg2_connection():
    """Test raw psycopg2 connection."""
    try:
        import psycopg2
        
        # Get connection details from environment
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        database = os.getenv('DATABASE_NAME', 'backend_api_db')
        user = os.getenv('DATABASE_USER', 'postgres')
        password = os.getenv('DATABASE_PASSWORD', 'postgres')
        
        print("🔍 Testing PostgreSQL connection with psycopg2...")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Database: {database}")
        print(f"   User: {user}")
        print(f"   Password: {'*' * len(password)}")
        
        # Attempt connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ Raw psycopg2 connection: SUCCESS")
        print(f"   PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print("❌ Raw psycopg2 connection: FAILED")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print("❌ Raw psycopg2 connection: UNEXPECTED ERROR")
        print(f"   Error: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    try:
        from sqlalchemy import create_engine, text
        
        # Build connection URL
        database_url = os.getenv(
            "DATABASE_URL", 
            f"postgresql://{os.getenv('DATABASE_USER', 'postgres')}:"
            f"{os.getenv('DATABASE_PASSWORD', 'postgres')}@"
            f"{os.getenv('DATABASE_HOST', 'localhost')}:"
            f"{os.getenv('DATABASE_PORT', '5432')}/"
            f"{os.getenv('DATABASE_NAME', 'backend_api_db')}"
        )
        
        print("\n🔍 Testing SQLAlchemy connection...")
        print(f"   Connection URL: {database_url.replace(os.getenv('DATABASE_PASSWORD', 'postgresql'), '*' * len(os.getenv('DATABASE_PASSWORD', 'postgresql')))}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user, version();"))
            row = result.fetchone()
            
            print("✅ SQLAlchemy connection: SUCCESS")
            print(f"   Current database: {row[0]}")
            print(f"   Current user: {row[1]}")
            print(f"   PostgreSQL version: {row[2]}")
            
        return True
        
    except Exception as e:
        print("❌ SQLAlchemy connection: FAILED")
        print(f"   Error: {e}")
        return False

def test_app_database_connection():
    """Test the app's database configuration."""
    try:
        print("\n🔍 Testing app database configuration...")
        
        from app.database import engine, get_db, Base
        from app.models import User
        from sqlalchemy import text
        
        # Test engine connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test;"))
            test_val = result.fetchone()[0]
            
            if test_val == 1:
                print("✅ App database engine: SUCCESS")
            else:
                print("❌ App database engine: UNEXPECTED RESULT")
                return False
        
        # Test session creation
        db = next(get_db())
        print("✅ App database session: SUCCESS")
        
        # Test model query
        user_count = db.query(User).count()
        print(f"✅ App model query: SUCCESS (found {user_count} users)")
        
        db.close()
        return True
        
    except Exception as e:
        print("❌ App database connection: FAILED")
        print(f"   Error: {e}")
        return False

def check_database_exists():
    """Check if the database exists."""
    try:
        import psycopg2
        
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        user = os.getenv('DATABASE_USER', 'postgres')
        password = os.getenv('DATABASE_PASSWORD', 'postgres')
        
        print("\n🔍 Checking if database exists...")
        
        # Connect to postgres database to check if our target database exists
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',  # Connect to default postgres database
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (os.getenv('DATABASE_NAME', 'backend_api_db'),))
        exists = cursor.fetchone()
        
        if exists:
            print(f"✅ Database '{os.getenv('DATABASE_NAME', 'backend_api_db')}' exists")
        else:
            print(f"❌ Database '{os.getenv('DATABASE_NAME', 'backend_api_db')}' does not exist")
            print("   You may need to create it first:")
            print(f"   CREATE DATABASE {os.getenv('DATABASE_NAME', 'backend_api_db')};")
        
        cursor.close()
        conn.close()
        return bool(exists)
        
    except Exception as e:
        print("❌ Database existence check: FAILED")
        print(f"   Error: {e}")
        return False

def check_table_exists():
    """Check if the users table exists."""
    try:
        import psycopg2
        
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        database = os.getenv('DATABASE_NAME', 'backend_api_db')
        user = os.getenv('DATABASE_USER', 'postgres')
        password = os.getenv('DATABASE_PASSWORD', 'postgres')
        
        print("\n🔍 Checking if users table exists...")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✅ Users table exists")
            
            # Get table info
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print("   Table structure:")
            for col_name, data_type, is_nullable in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"     {col_name}: {data_type} {nullable}")
                
        else:
            print("❌ Users table does not exist")
            print("   Run migrations to create it: alembic upgrade head")
        
        cursor.close()
        conn.close()
        return exists
        
    except Exception as e:
        print("❌ Table existence check: FAILED")
        print(f"   Error: {e}")
        return False

def main():
    """Run all database tests."""
    print("🚀 PostgreSQL Connection Test")
    print("=" * 50)
    
    # Test 1: Raw psycopg2 connection
    psycopg2_ok = test_psycopg2_connection()
    
    if not psycopg2_ok:
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check your .env file settings")
        print("   3. Verify the database user exists")
        print("   4. Check if password is correct")
        print("   5. Ensure the database exists")
        return
    
    # Test 2: Check database exists
    db_exists = check_database_exists()
    
    # Test 3: SQLAlchemy connection
    sqlalchemy_ok = test_sqlalchemy_connection()
    
    # Test 4: App database connection
    app_ok = test_app_database_connection()
    
    # Test 5: Check table exists
    table_exists = check_table_exists()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Raw psycopg2 connection: {'✅ PASS' if psycopg2_ok else '❌ FAIL'}")
    print(f"Database exists: {'✅ PASS' if db_exists else '❌ FAIL'}")
    print(f"SQLAlchemy connection: {'✅ PASS' if sqlalchemy_ok else '❌ FAIL'}")
    print(f"App database connection: {'✅ PASS' if app_ok else '❌ FAIL'}")
    print(f"Users table exists: {'✅ PASS' if table_exists else '❌ FAIL'}")
    
    if all([psycopg2_ok, db_exists, sqlalchemy_ok, app_ok, table_exists]):
        print("\n🎉 All tests passed! Your PostgreSQL connection is working perfectly!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()