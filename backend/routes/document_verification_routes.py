from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging
import json
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["document-verification"])

def extract_json(response_text: str, model_name: str) -> Dict:
    """Extract JSON from model response with multiple fallback methods"""
    import re
    
    result = None
    try:
        # Method 1: Try direct JSON parse
        result = json.loads(response_text)
        logger.info(f"✅ {model_name}: Parsed JSON directly")
    except json.JSONDecodeError as e:
        logger.warning(f"{model_name}: Direct parse failed: {e}")
        # Method 2: Extract from code blocks
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
            logger.info(f"{model_name}: Extracted from ```json block")
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
            logger.info(f"{model_name}: Extracted from ``` block")
        
        # Try parsing again
        try:
            result = json.loads(response_text)
            logger.info(f"✅ {model_name}: Parsed after extraction")
        except json.JSONDecodeError as e2:
            logger.warning(f"{model_name}: Second parse failed: {e2}")
            # Method 3: Regex to find JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    logger.info(f"✅ {model_name}: Parsed via regex")
                except:
                    pass
    
    if not result:
        logger.error(f"{model_name}: Failed to parse. First 300 chars: {response_text[:300]}")
        # Return minimal valid structure
        return {
            "verdict": "SUSPICIOUS",
            "fraud_probability": 50,
            "confidence_score": 30,
            "analysis_details": {},
            "red_flags": [f"{model_name} failed to provide proper analysis"],
            "authenticity_indicators": []
        }
    
    # Ensure required fields
    return {
        "verdict": result.get('verdict', 'SUSPICIOUS'),
        "fraud_probability": result.get('fraud_probability', 50),
        "confidence_score": result.get('confidence_score', 50),
        "analysis_details": result.get('analysis_details', {}),
        "red_flags": result.get('red_flags', []),
        "authenticity_indicators": result.get('authenticity_indicators', [])
    }

class VerificationResult(BaseModel):
    verdict: str  # "AUTHENTIC", "SUSPICIOUS", "LIKELY_FAKE"
    confidence_score: float  # 0-100
    fraud_probability: float  # 0-100
    analysis_details: Dict
    red_flags: List[str]
    authenticity_indicators: List[str]
    recommendations: str

class DocumentVerificationRequest(BaseModel):
    document_base64: str
    document_type: str = "general"  # bank_statement, passport, invoice, etc
    additional_context: str = ""

@router.post("/document-verification/analyze")
async def verify_document(request: DocumentVerificationRequest):
    """
    Deep document verification using AI vision model for fraud detection
    """
    try:
        logger.info(f"Starting document verification: {request.document_type}")
        
        # Multi-model verification for cross-validation (3 vision-capable models)
        primary_model = "openai/gpt-4o"  # GPT-4o with vision
        secondary_model = "anthropic/claude-3.5-sonnet"  # Claude 3.5 Sonnet with vision
        tertiary_model = "google/gemini-2.0-flash-exp:free"  # Gemini Flash with vision
        
        # Create comprehensive analysis prompt
        analysis_prompt = f"""You are an expert forensic document analyst specializing in fraud detection and authenticity verification.

TASK: Analyze the provided document image for authenticity and detect any signs of forgery, manipulation, or AI generation.

DOCUMENT TYPE: {request.document_type}
ADDITIONAL CONTEXT: {request.additional_context or "None provided"}

ANALYSIS CRITERIA (examine ALL):

1. **Visual Authenticity**
   - Image quality and resolution consistency
   - Compression artifacts or unnatural smoothness (AI generation signs)
   - Lighting and shadow consistency
   - Text rendering quality (pixelation, anti-aliasing)

2. **Document Structure**
   - Layout matches standard templates for this document type
   - Proper margins, spacing, alignment
   - Correct logo placement and sizing
   - Official seals, watermarks, security features present

3. **Typography Analysis**
   - Font consistency throughout document
   - Professional typography vs amateur editing
   - Kerning and spacing irregularities
   - Text alignment issues

4. **Content Verification**
   - Logical consistency of information
   - Date formats and chronology
   - Mathematical calculations (for financial docs)
   - Proper terminology and language
   - Signatures authenticity

5. **Metadata & Technical**
   - Signs of image editing (clone stamp, content-aware fill)
   - Color inconsistencies or banding
   - JPEG artifacts in unusual patterns
   - Resolution mismatches between elements

6. **Red Flags for Fraud**
   - Obvious copy-paste editing
   - Misaligned or overlapping elements
   - Inconsistent date/number formats
   - Suspicious amounts or values
   - Generic or template-like appearance
   - Signs of AI image generation (over-smoothing, unrealistic textures)

7. **Bank Statement Specific** (if applicable)
   - Transaction patterns naturalness
   - Running balance calculations
   - Bank logo and branding authenticity
   - Account number format validity
   - Statement period consistency

RESPOND WITH STRUCTURED JSON ONLY (no markdown, no code blocks):
{{
  "verdict": "AUTHENTIC|SUSPICIOUS|LIKELY_FAKE",
  "confidence_score": 0-100,
  "fraud_probability": 0-100,
  "analysis_details": {{
    "visual_quality": {{"score": 0-100, "findings": ["..."]}},
    "document_structure": {{"score": 0-100, "findings": ["..."]}},
    "typography": {{"score": 0-100, "findings": ["..."]}},
    "content_consistency": {{"score": 0-100, "findings": ["..."]}},
    "technical_analysis": {{"score": 0-100, "findings": ["..."]}},
    "ai_generation_signs": {{"likelihood": 0-100, "indicators": ["..."]}}
  }},
  "red_flags": ["List of suspicious findings"],
  "authenticity_indicators": ["List of positive indicators"],
  "detailed_assessment": "Comprehensive narrative explanation"
}}

Be EXTREMELY thorough and critical. False negatives (missing fraud) are more dangerous than false positives."""

        # PRIMARY MODEL ANALYSIS (GPT-4o)
        logger.info(f"Running PRIMARY analysis with {primary_model}...")
        primary_messages = [
            {
                "role": "system",
                "content": "You are a forensic document analyst. Respond ONLY with valid JSON - no markdown formatting, no code blocks."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{request.document_base64}"
                        }
                    }
                ]
            }
        ]
        
        primary_response = await openrouter_service.chat_completion(
            messages=primary_messages,
            model=primary_model,
            temperature=0.1
        )
        
        primary_text = primary_response['choices'][0]['message']['content']
        logger.info(f"Primary model response: {len(primary_text)} chars")
        primary_result = extract_json(primary_text, "PRIMARY")
        
        # SECONDARY MODEL ANALYSIS (Claude 3.5 Sonnet)
        logger.info(f"Running SECONDARY analysis with {secondary_model}...")
        secondary_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": request.document_base64
                        }
                    }
                ]
            }
        ]
        
        secondary_response = await openrouter_service.chat_completion(
            messages=secondary_messages,
            model=secondary_model,
            temperature=0.1
        )
        
        secondary_text = secondary_response['choices'][0]['message']['content']
        logger.info(f"Secondary model response: {len(secondary_text)} chars")
        secondary_result = extract_json(secondary_text, "SECONDARY")
        
        # TERTIARY MODEL ANALYSIS (Gemini Vision)
        logger.info(f"Running TERTIARY analysis with {tertiary_model}...")
        tertiary_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{request.document_base64}"
                        }
                    }
                ]
            }
        ]
        
        tertiary_response = await openrouter_service.chat_completion(
            messages=tertiary_messages,
            model=tertiary_model,
            temperature=0.1
        )
        
        tertiary_text = tertiary_response['choices'][0]['message']['content']
        logger.info(f"Tertiary model response: {len(tertiary_text)} chars")
        tertiary_result = extract_json(tertiary_text, "TERTIARY")
        
        # CONSENSUS ANALYSIS - Combine all 3 models
        logger.info("Creating consensus from 3 models...")
        
        # Average fraud probabilities with equal weight
        fraud_probs = [
            primary_result['fraud_probability'],
            secondary_result['fraud_probability'],
            tertiary_result['fraud_probability']
        ]
        avg_fraud_prob = sum(fraud_probs) / 3
        
        # Calculate disagreement (for confidence adjustment)
        max_fraud = max(fraud_probs)
        min_fraud = min(fraud_probs)
        disagreement = max_fraud - min_fraud
        
        # If models disagree significantly (>30%), be conservative
        if disagreement > 30:
            avg_fraud_prob = min(avg_fraud_prob + 10, 100)
            logger.warning(f"Models disagree by {disagreement}%, increasing fraud probability")
        
        # Determine final verdict based on consensus
        if avg_fraud_prob >= 70:
            final_verdict = "LIKELY_FAKE"
        elif avg_fraud_prob >= 40:
            final_verdict = "SUSPICIOUS"
        else:
            final_verdict = "AUTHENTIC"
        
        # Combine red flags from ALL models (unique)
        all_red_flags = list(set(
            primary_result.get('red_flags', []) + 
            secondary_result.get('red_flags', []) +
            tertiary_result.get('red_flags', [])
        ))
        
        # Combine authenticity indicators from ALL models (unique)
        all_authenticity = list(set(
            primary_result.get('authenticity_indicators', []) + 
            secondary_result.get('authenticity_indicators', []) +
            tertiary_result.get('authenticity_indicators', [])
        ))
        
        # Build comprehensive consensus result
        final_result = {
            "verdict": final_verdict,
            "confidence_score": round(100 - disagreement, 1),  # Lower if models disagree
            "fraud_probability": round(avg_fraud_prob, 1),
            "multi_model_analysis": {
                "primary_model": {
                    "name": "GPT-4o",
                    "verdict": primary_result.get('verdict'),
                    "fraud_probability": primary_result.get('fraud_probability')
                },
                "secondary_model": {
                    "name": "Claude 3.5 Sonnet",
                    "verdict": secondary_result.get('verdict'),
                    "fraud_probability": secondary_result.get('fraud_probability')
                },
                "tertiary_model": {
                    "name": "Gemini Vision",
                    "verdict": tertiary_result.get('verdict'),
                    "fraud_probability": tertiary_result.get('fraud_probability')
                },
                "agreement_level": round(100 - disagreement, 1),
                "models_used": 3
            },
            "analysis_details": primary_result.get('analysis_details', {}),  # Use primary as base
            "red_flags": all_red_flags,
            "authenticity_indicators": all_authenticity,
            "recommendations": generate_recommendations(final_verdict, avg_fraud_prob, all_red_flags)
        }
        
        logger.info(f"✅ Consensus complete: {final_verdict} ({avg_fraud_prob:.1f}% fraud, {100-disagreement:.1f}% agreement)")
        
        return final_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Response text (first 500 chars): {response_text[:500] if 'response_text' in locals() else 'N/A'}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse AI analysis. Please try again."
        )
    except Exception as e:
        logger.error(f"Document verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )

def generate_recommendations(verdict: str, fraud_prob: float, red_flags: List[str]) -> str:
    """Generate actionable recommendations based on verification results"""
    
    if verdict == "LIKELY_FAKE":
        return f"""⚠️ CRITICAL: This document shows high probability ({fraud_prob:.1f}%) of being fraudulent.

RECOMMENDED ACTIONS:
1. **DO NOT ACCEPT** this document for official purposes
2. Request original physical document for in-person verification
3. Contact issuing organization directly to verify authenticity
4. Consider reporting to fraud prevention authorities
5. Obtain alternative documentation from verified sources

DETECTED ISSUES: {len(red_flags)} major red flags identified including potential forgery indicators.

This document should be treated as UNTRUSTWORTHY until proven otherwise."""
    
    elif verdict == "SUSPICIOUS":
        return f"""⚠️ WARNING: This document shows moderate probability ({fraud_prob:.1f}%) of authenticity issues.

RECOMMENDED ACTIONS:
1. Request additional supporting documentation
2. Verify information through independent channels
3. Contact document issuer for confirmation
4. Compare with known authentic samples
5. Consider professional forensic analysis if high-value transaction

DETECTED CONCERNS: {len(red_flags)} potential issues require further investigation.

Proceed with caution and additional verification steps."""
    
    else:
        return f"""✅ ACCEPTABLE: This document appears authentic with low fraud probability ({fraud_prob:.1f}%).

RECOMMENDED ACTIONS:
1. Standard acceptance procedures can proceed
2. Maintain digital copy for records
3. Verify key information points independently (standard practice)
4. Compare against any other provided documentation

Note: This automated analysis provides high confidence in authenticity, but human review of critical documents is always recommended for high-value transactions."""


@router.post("/document-verification/batch")
async def verify_documents_batch(documents: List[DocumentVerificationRequest]):
    """
    Batch verification of multiple documents
    """
    try:
        results = []
        
        for idx, doc_request in enumerate(documents):
            logger.info(f"Processing document {idx + 1}/{len(documents)}")
            result = await verify_document(doc_request)
            results.append({
                "document_index": idx,
                "result": result
            })
        
        # Summary statistics
        total_authentic = sum(1 for r in results if r['result']['verdict'] == 'AUTHENTIC')
        total_suspicious = sum(1 for r in results if r['result']['verdict'] == 'SUSPICIOUS')
        total_fake = sum(1 for r in results if r['result']['verdict'] == 'LIKELY_FAKE')
        
        avg_fraud_prob = sum(r['result']['fraud_probability'] for r in results) / len(results)
        
        return {
            "results": results,
            "summary": {
                "total_documents": len(documents),
                "authentic": total_authentic,
                "suspicious": total_suspicious,
                "likely_fake": total_fake,
                "average_fraud_probability": round(avg_fraud_prob, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Batch verification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch verification failed: {str(e)}"
        )
