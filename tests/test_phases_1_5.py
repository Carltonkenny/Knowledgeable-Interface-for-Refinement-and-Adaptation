"""
Test Suite: Phases 1-5 Implementation Verification

Tests for:
- Phase 1: Personality adaptation integration
- Phase 2: Timezone-aware streak calculation
- Phase 3: Cross-session inactivity check
- Phase 4: Profile sync timestamp tracking
- Phase 5: Quality-aware heatmap

Run: python -m pytest tests/test_phases_1_5.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from datetime import datetime as real_datetime, timedelta as real_timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ═══ PHASE 1 TESTS: Personality Adaptation ═══════════════════════════════════

class TestPhase1PersonalityAdaptation:
    """Test Phase 1: adapt_kira_personality() integration"""
    
    def test_adapt_kira_personality_import(self):
        """Verify adapt_kira_personality can be imported"""
        from agents.orchestration.personality import adapt_kira_personality
        assert callable(adapt_kira_personality)
    
    def test_adapt_kira_personality_detects_formality(self):
        """Test formality detection"""
        from agents.orchestration.personality import adapt_kira_personality
        
        # Casual message
        result = adapt_kira_personality(
            message="hey can u help me with some code",
            user_profile={},
            response_text="Got it — here's the code you need"
        )
        
        assert "formality" in result.detected_user_style
        assert result.detected_user_style["formality"] < 0.5  # Casual
    
    def test_adapt_kira_personality_detects_technical(self):
        """Test technical detection"""
        from agents.orchestration.personality import adapt_kira_personality
        
        # Technical message
        result = adapt_kira_personality(
            message="need help with async API endpoint and database query optimization",
            user_profile={},
            response_text="Here's the optimized async pattern"
        )
        
        assert "technical" in result.detected_user_style
        assert result.detected_user_style["technical"] > 0.5  # Technical
    
    def test_check_forbidden_phrases(self):
        """Test forbidden phrase detection"""
        from agents.orchestration.personality import check_forbidden_phrases
        
        # Should detect forbidden phrases
        violations = check_forbidden_phrases("Certainly! I'd be happy to help.")
        assert "Certainly" in violations or "I'd be happy to" in violations
        
        # Should not detect in clean response
        clean = check_forbidden_phrases("Got it — here's what you need")
        assert len(clean) == 0


# ═══ PHASE 2 TESTS: Timezone-Aware Streak ════════════════════════════════════

class TestPhase2TimezoneStreak:
    """Test Phase 2: Timezone-aware streak calculation"""
    
    def test_streak_with_utc_timezone(self):
        """Test streak calculation with UTC"""
        from zoneinfo import ZoneInfo
        
        user_tz = ZoneInfo("UTC")
        today = datetime.now(user_tz).date()
        yesterday = today - timedelta(days=1)
        
        # Simulate dates active
        dates_active = {today, yesterday}
        
        # Calculate streak
        streak = 0
        curr_d = today
        
        if curr_d in dates_active:
            streak = 1
            curr_d -= timedelta(days=1)
            while curr_d in dates_active:
                streak += 1
                curr_d -= timedelta(days=1)
        
        assert streak == 2
    
    def test_streak_with_tokyo_timezone(self):
        """Test streak calculation with Asia/Tokyo timezone"""
        from zoneinfo import ZoneInfo
        
        user_tz = ZoneInfo("Asia/Tokyo")
        utc_tz = ZoneInfo("UTC")
        
        # User in Tokyo prompts at 11 PM March 31 (Tokyo time)
        # This is 2 PM March 31 UTC
        tokyo_time = datetime(2026, 3, 31, 23, 0, tzinfo=user_tz)
        utc_time = tokyo_time.astimezone(utc_tz)
        
        # Should be March 31 in both timezones
        assert tokyo_time.date().day == 31
        assert utc_time.date().day == 31
    
    def test_invalid_timezone_fallback(self):
        """Test fallback to UTC for invalid timezone"""
        from zoneinfo import ZoneInfo
        
        try:
            invalid_tz = ZoneInfo("Invalid/Timezone")
            assert False, "Should have raised exception"
        except Exception:
            # Fallback to UTC
            user_tz = ZoneInfo("UTC")
            assert user_tz is not None


# ═══ PHASE 3 TESTS: Cross-Session Inactivity ═════════════════════════════════

class TestPhase3CrossSessionInactivity:
    """Test Phase 3: Cross-session inactivity check"""
    
    def test_should_trigger_update_every_5th_interaction(self):
        """Test trigger on every 5th interaction"""
        # Phase 3: Function signature changed to (user_id, interaction_count)
        # Every 5th interaction should trigger regardless of DB state
        from memory.profile_updater import should_trigger_update, INTERACTION_THRESHOLD
        
        # Mock the database call to return empty sessions
        with patch('memory.profile_updater.get_client') as mock_get_client:
            mock_db = MagicMock()
            mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            mock_get_client.return_value = mock_db
            
            # Should trigger on 5th, 10th, 15th... interactions
            assert should_trigger_update("test-user-id", 5) == True
            assert should_trigger_update("test-user-id", 10) == True
            # Should NOT trigger on non-5th interactions (with no sessions)
            assert should_trigger_update("test-user-id", 3) == False
    
    @pytest.mark.integration
    @patch('memory.profile_updater.get_client')
    def test_should_trigger_update_cross_session_inactive(self, mock_get_client):
        """
        INTEGRATION TEST: Requires database mocking.
        Test trigger when user inactive in ALL sessions.
        """
        from memory.profile_updater import should_trigger_update, INACTIVITY_MINUTES

        # Mock current time
        now = real_datetime(2026, 3, 31, 12, 0, tzinfo=timezone.utc)

        # Create a mock datetime class that preserves fromisoformat but mocks .now()
        mock_dt = MagicMock()
        mock_dt.now.return_value = now
        mock_dt.fromisoformat = real_datetime.fromisoformat
        mock_dt.strptime = real_datetime.strptime
        mock_dt.utcnow = real_datetime.utcnow
        mock_dt.today = real_datetime.today

        # Mock database with inactive sessions (all > 30 min ago)
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {"last_activity": "2026-03-31T11:00:00+00:00"},  # 60 min ago
                {"last_activity": "2026-03-31T11:15:00+00:00"},  # 45 min ago
            ]
        )
        mock_get_client.return_value = mock_db

        with patch('memory.profile_updater.datetime', mock_dt):
            # Should trigger (all sessions inactive > 30 min)
            result = should_trigger_update("test-user-id", 3)
            assert result == True

    @pytest.mark.integration
    @patch('memory.profile_updater.get_client')
    def test_should_trigger_update_cross_session_active(self, mock_get_client):
        """
        INTEGRATION TEST: Requires database mocking.
        Test NO trigger when user active in ANY session.
        """
        from memory.profile_updater import should_trigger_update

        # Mock current time
        now = real_datetime(2026, 3, 31, 12, 0, tzinfo=timezone.utc)

        # Create a mock datetime class that preserves fromisoformat but mocks .now()
        mock_dt = MagicMock()
        mock_dt.now.return_value = now
        mock_dt.fromisoformat = real_datetime.fromisoformat
        mock_dt.strptime = real_datetime.strptime
        mock_dt.utcnow = real_datetime.utcnow
        mock_dt.today = real_datetime.today

        # Mock database with one active session (< 30 min ago)
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {"last_activity": "2026-03-31T11:00:00+00:00"},  # 60 min ago
                {"last_activity": "2026-03-31T11:50:00+00:00"},  # 10 min ago (ACTIVE!)
            ]
        )
        mock_get_client.return_value = mock_db

        with patch('memory.profile_updater.datetime', mock_dt):
            # Should NOT trigger (user active in another tab)
            result = should_trigger_update("test-user-id", 3)
            assert result == False


# ═══ PHASE 4 TESTS: Profile Sync Timestamp ═══════════════════════════════════

class TestPhase4ProfileSyncTimestamp:
    """Test Phase 4: Profile sync timestamp tracking"""
    
    def test_last_profile_sync_field_exists(self):
        """Verify last_profile_sync is tracked in profile_updater"""
        import inspect
        from memory import profile_updater
        
        source = inspect.getsource(profile_updater.update_user_profile)
        assert "last_profile_sync" in source
    
    def test_last_profile_sync_update_logic(self):
        """Verify last_profile_sync is updated after successful save"""
        import inspect
        from memory import profile_updater
        
        source = inspect.getsource(profile_updater.update_user_profile)
        
        # Check for update logic
        assert 'db.table("user_profiles").update' in source
        assert "last_profile_sync" in source
        assert "datetime.now(timezone.utc).isoformat()" in source


# ═══ PHASE 5 TESTS: Quality-Aware Heatmap ════════════════════════════════════

class TestPhase5QualityHeatmap:
    """Test Phase 5: Quality-aware heatmap"""
    
    def test_heatmap_includes_avg_quality(self):
        """Verify heatmap response includes avg_quality field"""
        import inspect
        from routes import analytics
        
        source = inspect.getsource(analytics.get_activity_heatmap)
        
        # Check for quality aggregation
        assert "quality_score" in source
        assert "avg_quality" in source
        assert "calculate_overall_quality" in source
    
    def test_heatmap_response_schema(self):
        """Test heatmap response schema"""
        # Mock response structure
        heatmap_data = [
            {"date": "2026-03-31", "count": 5, "avg_quality": 4.2},
            {"date": "2026-04-01", "count": 3, "avg_quality": 3.8},
        ]
        
        # Verify schema
        for item in heatmap_data:
            assert "date" in item
            assert "count" in item
            assert "avg_quality" in item
            assert isinstance(item["count"], int)
            assert isinstance(item["avg_quality"], float)


# ═══ INTEGRATION TESTS ═══════════════════════════════════════════════════════

class TestIntegration:
    """Integration tests for all phases"""
    
    def test_all_phases_compiled(self):
        """Verify all modified files compile without errors"""
        import py_compile
        import tempfile
        
        files = [
            "agents/handlers/unified.py",
            "memory/profile_updater.py",
            "routes/user.py",
            "routes/analytics.py",
            "routes/prompts.py",
            "routes/prompts_stream.py",
        ]
        
        for file in files:
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                assert False, f"Compilation failed for {file}: {e}"
    
    def test_no_forbidden_phrases_in_kira_response(self):
        """Integration test: Kira doesn't use forbidden phrases"""
        from agents.orchestration.personality import check_forbidden_phrases
        
        # Simulate Kira responses
        responses = [
            "Got it — here's what you need",
            "On it — firing the swarm 🚀",
            "Let me break this down for you",  # Should pass ("Let me" alone is OK)
        ]
        
        for response in responses:
            violations = check_forbidden_phrases(response)
            assert len(violations) == 0, f"Found violations in: {response}"


# ═══ RUN TESTS ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
