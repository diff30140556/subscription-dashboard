#!/usr/bin/env python3
"""
Database connection and utilities using asyncpg for PostgreSQL/Supabase.
Production-ready with connection pooling and proper error handling.
"""

import os
import asyncio
from typing import Optional, Any, Dict, List
import asyncpg
import pandas as pd
from contextlib import asynccontextmanager


class DatabaseManager:
    """Async PostgreSQL database manager with connection pooling."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._pool: Optional[asyncpg.Pool] = None
    
    async def create_pool(self, **kwargs) -> asyncpg.Pool:
        """Create connection pool with production settings."""
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
            
        if self._pool is None or self._pool._closed:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
                statement_cache_size=0,  # Disable prepared statements for Supabase/pgbouncer
                **kwargs
            )
        return self._pool
    
    async def close_pool(self):
        """Close the connection pool."""
        if self._pool and not self._pool._closed:
            await self._pool.close()
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool with automatic cleanup."""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            yield conn
    
    async def fetch_df(self, sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as pandas DataFrame.
        
        Args:
            sql: SQL query string with $1, $2, ... placeholders
            params: Optional list of parameters for the query
            
        Returns:
            pandas DataFrame with query results
            
        Raises:
            asyncpg.PostgresError: For database errors
            ValueError: For invalid SQL or parameters
        """
        if not sql or not isinstance(sql, str):
            raise ValueError("SQL query must be a non-empty string")
        
        params = params or []
        
        try:
            async with self.get_connection() as conn:
                # Execute query and fetch all rows
                rows = await conn.fetch(sql, *params)
                
                if not rows:
                    # Return empty DataFrame with proper structure if no results
                    return pd.DataFrame()
                
                # Convert asyncpg Records to list of dicts for pandas
                data = [dict(row) for row in rows]
                df = pd.DataFrame(data)
                
                return df
                
        except asyncpg.PostgresError as e:
            raise asyncpg.PostgresError(f"Database query failed: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create DataFrame: {e}")
    
    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> str:
        """
        Execute SQL command (INSERT, UPDATE, DELETE) and return status.
        
        Args:
            sql: SQL command string
            params: Optional list of parameters
            
        Returns:
            Command status string (e.g., "INSERT 0 1")
        """
        params = params or []
        
        try:
            async with self.get_connection() as conn:
                status = await conn.execute(sql, *params)
                return status
        except asyncpg.PostgresError as e:
            raise asyncpg.PostgresError(f"Database command failed: {e}")
    
    async def fetch_val(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """
        Execute SQL query and return single value.
        
        Args:
            sql: SQL query string
            params: Optional list of parameters
            
        Returns:
            Single value from query result
        """
        params = params or []
        
        try:
            async with self.get_connection() as conn:
                return await conn.fetchval(sql, *params)
        except asyncpg.PostgresError as e:
            raise asyncpg.PostgresError(f"Database query failed: {e}")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_connection():
    """Dependency for FastAPI routes to get database connection."""
    async with db_manager.get_connection() as conn:
        yield conn


async def fetch_df(sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
    """
    Convenience function to fetch DataFrame using global db_manager.
    
    Args:
        sql: SQL query string with $1, $2, ... placeholders
        params: Optional list of parameters for the query
        
    Returns:
        pandas DataFrame with query results
    """
    return await db_manager.fetch_df(sql, params)


async def health_check() -> Dict[str, Any]:
    """
    Check database connectivity and return health status.
    
    Returns:
        Dict with database health information
    """
    try:
        async with db_manager.get_connection() as conn:
            # Simple query to test connection
            result = await conn.fetchval("SELECT 1")
            version = await conn.fetchval("SELECT version()")
            
            return {
                "status": "healthy",
                "database": "connected",
                "test_query": result == 1,
                "postgres_version": version.split()[1] if version else "unknown"
            }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }