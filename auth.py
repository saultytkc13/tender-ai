import os
from supabase import create_client, Client

# ── Supabase clients ──────────────────────────────────────────
def get_supabase_client() -> Client:
    """Regular client — used only for auth (login/register)"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

def get_admin_client() -> Client:
    """Service role client — used for all DB operations (bypasses RLS)"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    return create_client(url, key)


# ── Auth operations ───────────────────────────────────────────
def register_user(email, password):
    """Register a new user with Supabase Auth"""
    try:
        supabase = get_supabase_client()
        result = supabase.auth.sign_up({"email": email, "password": password})
        if result.user:
            return {"success": True, "user": result.user}
        return {"success": False, "error": "Registration failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(email, password):
    """Login user and return session"""
    try:
        supabase = get_supabase_client()
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if result.user:
            return {"success": True, "user": result.user, "session": result.session}
        return {"success": False, "error": "Invalid email or password"}
    except Exception as e:
        return {"success": False, "error": "Invalid email or password"}


# ── Company profile operations ────────────────────────────────
def get_company_profile(user_id):
    """Fetch company profile for a user"""
    try:
        admin = get_admin_client()
        result = admin.table("company_profiles") \
                      .select("*") \
                      .eq("user_id", user_id) \
                      .execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return None

def save_company_profile(user_id, data):
    """Create or update company profile"""
    try:
        admin = get_admin_client()

        # Check if profile already exists
        existing = admin.table("company_profiles") \
                        .select("id") \
                        .eq("user_id", user_id) \
                        .execute()

        profile_data = {
            "user_id": user_id,
            "company_name": data.get("company_name", ""),
            "registration_number": data.get("registration_number", ""),
            "pan_number": data.get("pan_number", ""),
            "turnover": float(data.get("turnover", 0) or 0),
            "experience": int(data.get("experience", 0) or 0),
            "domain": data.get("domain", ""),
            "sub_domains": data.get("sub_domains", []),
            "employee_count": int(data.get("employee_count", 0) or 0),
            "certifications": data.get("certifications", ""),
            "address": data.get("address", ""),
            "phone": data.get("phone", ""),
            "company_email": data.get("company_email", ""),
        }

        if existing.data:
            # Update
            admin.table("company_profiles") \
                 .update(profile_data) \
                 .eq("user_id", user_id) \
                 .execute()
        else:
            # Insert
            admin.table("company_profiles") \
                 .insert(profile_data) \
                 .execute()

        return {"success": True}
    except Exception as e:
        print(f"Error saving profile: {e}")
        return {"success": False, "error": str(e)}


# ── Tender history operations ─────────────────────────────────
def save_tender_analysis(user_id, data):
    """Save a tender analysis result to history"""
    try:
        admin = get_admin_client()

        record = {
            "user_id": user_id,
            "project_name": data.get("project_name", "Unknown Project"),
            "project_value": float(data.get("project_value", 0) or 0),
            "location": data.get("location", ""),
            "deadline": data.get("deadline", ""),
            "required_turnover": float(data.get("required_turnover", 0) or 0),
            "required_experience": int(data.get("required_experience", 0) or 0),
            "eligibility_score": int(data.get("eligibility_score", 0) or 0),
            "difficulty_score": int(data.get("difficulty_score", 0) or 0),
            "summary": data.get("summary", ""),
            "recommendations": data.get("recommendations", []),
        }

        admin.table("tender_history").insert(record).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return {"success": False, "error": str(e)}

def get_tender_history(user_id):
    """Fetch all past tender analyses for a user"""
    try:
        admin = get_admin_client()
        result = admin.table("tender_history") \
                      .select("*") \
                      .eq("user_id", user_id) \
                      .order("created_at", desc=True) \
                      .execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

def get_dashboard_stats(user_id):
    """Get stats for the dashboard"""
    try:
        history = get_tender_history(user_id)

        total_analyzed = len(history)
        avg_score = 0
        last_tender = None

        if history:
            scores = [h["eligibility_score"] for h in history if h.get("eligibility_score")]
            avg_score = round(sum(scores) / len(scores)) if scores else 0
            last_tender = history[0]  # most recent (already sorted desc)

        return {
            "total_analyzed": total_analyzed,
            "avg_score": avg_score,
            "last_tender": last_tender,
            "recent_history": history[:5]  # last 5 only for dashboard
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {
            "total_analyzed": 0,
            "avg_score": 0,
            "last_tender": None,
            "recent_history": []
        }