import os
import json
import pdfplumber
from groq import Groq

# ── Groq client ───────────────────────────────────────────────
def get_groq_client():
    return Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ── PDF text extraction ───────────────────────────────────────
def extract_text_from_pdf(pdf_file):
    """Extract all text from an uploaded PDF file"""
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


# ── Main analysis function ────────────────────────────────────
def analyze_tender(pdf_text, company_profile):
    """Send tender text + company profile to Groq and get structured analysis"""

    client = get_groq_client()

    prompt = f"""
You are an expert tender analyst. Analyze the following tender document against the company profile provided.

COMPANY PROFILE:
- Company Name: {company_profile.get('company_name', 'N/A')}
- Domain: {company_profile.get('domain', 'N/A')}
- Sub Domains: {', '.join(company_profile.get('sub_domains', []) or [])}
- Annual Turnover: ₹{company_profile.get('turnover', 0)} Lakhs
- Years of Experience: {company_profile.get('experience', 0)} years
- Employee Count: {company_profile.get('employee_count', 0)}
- Certifications: {company_profile.get('certifications', 'None')}

TENDER DOCUMENT:
{pdf_text[:6000]}

INSTRUCTIONS:
Analyze this tender and return ONLY a valid JSON object with exactly these fields. No explanation, no markdown, no extra text — just the raw JSON.

{{
  "project_name": "full project name from tender",
  "project_value": numeric value in lakhs (number only, no symbols),
  "location": "project location",
  "deadline": "submission deadline date",
  "required_turnover": numeric minimum turnover required in lakhs,
  "required_experience": numeric years of experience required,
  "required_certifications": "certifications mentioned in tender",
  "tender_domain": "primary domain of this tender",
  "eligibility_score": integer 0-100 representing how eligible this company is,
  "difficulty_score": integer 1-10 representing tender difficulty,
  "domain_match": "Strong Match" or "Partial Match" or "No Match",
  "domain_match_reason": "brief reason for domain match assessment",
  "summary": "2-3 sentence plain English summary of what this tender is about",
  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        return {"success": True, "data": result}

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {raw}")
        return {"success": False, "error": "AI returned invalid response. Please try again."}
    except Exception as e:
        print(f"Groq API error: {e}")
        return {"success": False, "error": str(e)}