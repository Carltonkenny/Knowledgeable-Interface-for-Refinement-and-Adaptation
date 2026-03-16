import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjAxNDRkZGRmLTIxOWUtNGMyZC1iOGRlLWViMmFlZDZmNTk3ZCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2Nja3puamt6c2Z5cHNzZ2VjeXlhLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyZWIyMjRlYi0xYTVmLTQxMTItODY3YS1lZDE5ODRhZDA2ODciLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzczNTEzNTgwLCJpYXQiOjE3NzM1MDk5ODAsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2Vy_metadata\":{\"email\":\"testuser@example.com\",\"email_verified\":true,\"onboarding_completed\":true,\"onboarding_completed_at\":\"2026-03-14T11:03:14.796Z\",\"onboarding_profile\":{\"ai_frustration\":\"repeats\",\"audience\":\"technical\",\"frustration_detail\":\"\",\"primary_use\":\"coding\"},\"onboarding_profile_set_at\":\"2026-03-14T11:03:13.672Z\",\"phone_verified\":false,\"sub\":\"2eb224eb-1a5f-4112-867a-ed1984ad0687\",\"terms_accepted\":true,\"terms_accepted_at\":\"2026-03-14T11:01:57.765Z\"},\"role\":\"authenticated\",\"aal\":\"aal1\",\"amr\":[{\"method\":\"password\",\"timestamp\":1773486101}],\"session_id\":\"0cec32dd-3389-4a06-af4d-e344ee8ee7f8\",\"is_anonymous\":false}.RA4aSfoVONialQWa_sU1ReA7BNFssEcCqWlReXSyEkPJX_8JyZBObwVQernx7FEZMlRtmedvDKp-2g1F7GB4sA"

# The token I got from browser subagent result was slightly different in formatting.
# Let me use the EXACT string from the subagent result.
token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjAxNDRkZGRmLTIxOWUtNGMyZC1iOGRlLWViMmFlZDZmNTk3ZCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2Nja3puamt6c2Z5cHNzZ2VjeXlhLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyZWIyMjRlYi0xYTVmLTQxMTItODY3YS1lZDE5ODRhZDA2ODciLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzczNTEzNTgwLCJpYXQiOjE3NzM1MDk5ODAsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwib25ib2FyZGluZ19jb21wbGV0ZWQiOnRydWUsIm9uYm9hcmRpbmdfY29tcGxldGVkX2F0IjoiMjAyNi0wMy0xNFQxMTowMzoxNC43OTZaIiwib25ib2FyZGluZ19wcm9maWxlIjp7ImFpX2ZydXN0cmF0aW9uIjoicmVwZWF0cyIsImF1ZGllbmNlIjoidGVjaG5pY2FsIiwiZnJ1c3RyYXRpb25fZGV0YWlsIjoiIiwicHJpbWFyeV91c2UiOiJjb2RpbmcifSwib25ib2FyZGluZ19wcm9maWxlX3NldF9hdCI6IjIwMjYtMDMtMTRUMTE6MDM6MTMuNjcyWiIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiMmViMjI0ZWItMWE1Zi00MTEyLTg2N2EtZWQxOTg0YWQwNjg3IiwidGVybXNfYWNjZXB0ZWQiOnRydWUsInRlcm1zX2FjY2VwdGVkX2F0IjoiMjAyNi0wMy0xNFQxMTowMTo1Ny43NjVaIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NzM0ODYxMDF9XSwic2Vzc2lvbl9pZCI6IjBjZWMzMmRkLTMzODktNGEwNi1hZjRkLWUzNDRlZThlZTdmOCIsImlzX2Fub255bW91cyI6ZmFsc2V9.RA4aSfoVONialQWa_sU1ReA7BNFssEcCqWlReXSyEkPJX_8JyZBObwVQernx7FEZMlRtmedvDKp-2g1F7GB4sA"

print(f"URL: {SUPABASE_URL}")
print(f"Key starts with: {SUPABASE_KEY[:10]}...")
print(f"Secret starts with: {JWT_SECRET[:10]}...")

try:
    print("\n--- Testing Supabase API Verification ---")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    user_response = supabase.auth.get_user(token)
    print(f"Supabase API SUCCESS. User ID: {user_response.user.id}")
    
    print("\n--- Testing Local JWT Verification ---")
    # Note: Supabase tokens for self-hosted/local might use HS256 with the secret
    # Cloud tokens use ES256 with a public key usually, BUT the project secret should still work for verification?
    # Actually, Supabase Cloud JWTs ARE verifiable via HMAC-SHA256 if you have the JWT secret.
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=["HS256"], 
            options={"verify_aud": False, "verify_iss": False}
        )
        print("Local HS256 Verification SUCCESS!")
        print(f"Sub: {payload.get('sub')}")
    except Exception as e:
        print(f"Local HS256 Verification FAILED: {e}")

except Exception as e:
    print(f"\nCRITICAL ERROR: {type(e).__name__}: {str(e)}")
