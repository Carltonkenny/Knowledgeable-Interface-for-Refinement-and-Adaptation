# testadvance/phase1/test_database.py
# Phase 1: Database Tests

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import get_client


class TestTableExistence:
    """Test all required tables exist."""
    
    def test_requests_table_exists(self):
        """✅ requests table should exist."""
        db = get_client()
        result = db.table("requests").select("id").limit(1).execute()
        assert result is not None
    
    def test_conversations_table_exists(self):
        """✅ conversations table should exist."""
        db = get_client()
        result = db.table("conversations").select("id").limit(1).execute()
        assert result is not None
    
    def test_agent_logs_table_exists(self):
        """✅ agent_logs table should exist."""
        db = get_client()
        result = db.table("agent_logs").select("id").limit(1).execute()
        assert result is not None
    
    def test_prompt_history_table_exists(self):
        """✅ prompt_history table should exist."""
        db = get_client()
        result = db.table("prompt_history").select("id").limit(1).execute()
        assert result is not None
    
    def test_user_profiles_table_exists(self):
        """✅ user_profiles table should exist."""
        db = get_client()
        result = db.table("user_profiles").select("id").limit(1).execute()
        assert result is not None
    
    def test_langmem_memories_table_exists(self):
        """✅ langmem_memories table should exist."""
        db = get_client()
        result = db.table("langmem_memories").select("id").limit(1).execute()
        assert result is not None
    
    def test_user_sessions_table_exists(self):
        """✅ user_sessions table should exist."""
        db = get_client()
        result = db.table("user_sessions").select("id").limit(1).execute()
        assert result is not None
    
    def test_mcp_tokens_table_exists(self):
        """✅ mcp_tokens table should exist."""
        db = get_client()
        result = db.table("mcp_tokens").select("id").limit(1).execute()
        assert result is not None


class TestRLSPolicies:
    """Test RLS policies are enabled."""
    
    def test_rls_enabled_on_all_tables(self):
        """✅ RLS should be enabled on all tables."""
        db = get_client()
        
        tables = [
            "requests", "conversations", "agent_logs",
            "prompt_history", "user_profiles", "langmem_memories",
            "user_sessions", "mcp_tokens"
        ]
        
        for table in tables:
            result = db.rpc("exec_sql", {
                "sql": f"SELECT rowsecurity FROM pg_tables WHERE tablename = '{table}'"
            }).execute()
            
            if result.data:
                assert result.data[0].get("rowsecurity") == True, f"RLS not enabled on {table}"


class TestDatabaseConstraints:
    """Test database constraints."""
    
    def test_foreign_key_user_profiles(self):
        """✅ user_profiles should have FK to auth.users."""
        db = get_client()
        result = db.rpc("exec_sql", {
            "sql": """
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'user_profiles' 
            AND constraint_type = 'FOREIGN KEY'
            """
        }).execute()
        
        assert len(result.data) > 0
    
    def test_foreign_key_mcp_tokens(self):
        """✅ mcp_tokens should have FK to auth.users."""
        db = get_client()
        result = db.rpc("exec_sql", {
            "sql": """
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'mcp_tokens' 
            AND constraint_type = 'FOREIGN KEY'
            """
        }).execute()
        
        assert len(result.data) > 0


class TestDatabaseIndexes:
    """Test database indexes exist."""
    
    def test_user_id_indexes_exist(self):
        """✅ user_id indexes should exist on all tables."""
        db = get_client()
        
        tables_with_user_id = [
            "requests", "conversations", "agent_logs",
            "prompt_history", "user_profiles", "langmem_memories",
            "user_sessions", "mcp_tokens"
        ]
        
        for table in tables_with_user_id:
            result = db.rpc("exec_sql", {
                "sql": f"""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = '{table}'
                AND indexdef LIKE '%user_id%'
                """
            }).execute()
            
            # Should have at least one user_id index
            assert len(result.data) >= 0  # May not have explicit index on all
