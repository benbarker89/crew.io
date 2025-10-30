"""
Barker v ESHT - LLM Analysis Tools
Issue mapping and quote extraction using local LLM capabilities
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class IssueMapper:
    """Maps evidence to legal issues using LLM analysis"""

    def __init__(self, supabase_client, config):
        """Initialize issue mapper

        Args:
            supabase_client: SupabaseClient instance
            config: Configuration object
        """
        self.supabase = supabase_client
        self.config = config

    def analyze_evidence(self, evidence_id: str) -> Dict[str, Any]:
        """Analyze evidence and map to issues

        Args:
            evidence_id: Evidence UUID

        Returns:
            Analysis result with issue mappings
        """
        logger.info(f"Analyzing evidence {evidence_id} for issue mapping")

        try:
            # Get evidence from database
            evidence = self.supabase.query_evidence({'id': evidence_id})
            if not evidence:
                logger.error(f"Evidence {evidence_id} not found")
                return {'error': 'Evidence not found'}

            evidence_record = evidence[0]

            # Get all issues
            issues = self.supabase.query_issues()

            # Build analysis prompt
            prompt = self._build_issue_mapping_prompt(evidence_record, issues)

            # Run LLM analysis (placeholder - would use actual LLM API)
            analysis = self._run_llm_analysis(prompt)

            # Parse and structure results
            result = {
                'evidence_id': evidence_id,
                'exhibit_code': evidence_record.get('exhibit_code'),
                'mapped_issues': analysis.get('issues', []),
                'confidence_scores': analysis.get('confidence', {}),
                'key_points': analysis.get('key_points', []),
                'timestamp': json.dumps(evidence_record.get('created_at'), default=str)
            }

            logger.info(f"Mapped evidence to {len(result['mapped_issues'])} issues")
            return result

        except Exception as e:
            logger.error(f"Error analyzing evidence: {e}")
            return {'error': str(e)}

    def batch_analyze(self, evidence_ids: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple evidence items

        Args:
            evidence_ids: List of evidence UUIDs

        Returns:
            List of analysis results
        """
        results = []
        for evidence_id in evidence_ids:
            result = self.analyze_evidence(evidence_id)
            results.append(result)

        return results

    def export_to_json(self, output_path: str):
        """Export all issue mappings to JSON

        Args:
            output_path: Output file path
        """
        # Get all evidence with exhibit codes
        all_evidence = self.supabase.query_evidence()
        evidence_with_codes = [e for e in all_evidence if e.get('exhibit_code')]

        # Analyze all
        results = self.batch_analyze([e['id'] for e in evidence_with_codes])

        # Export to JSON
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Exported {len(results)} issue mappings to {output_file}")

    def _build_issue_mapping_prompt(self, evidence: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
        """Build LLM prompt for issue mapping

        Args:
            evidence: Evidence record
            issues: List of issue records

        Returns:
            Formatted prompt
        """
        issue_list = '\n'.join([
            f"- {i.get('issue_code')}: {i.get('title')} ({i.get('category')})"
            for i in issues
        ])

        prompt = f"""
Analyze the following evidence and determine which legal issues it relates to.

EVIDENCE:
- Exhibit Code: {evidence.get('exhibit_code')}
- Document Type: {evidence.get('document_type')}
- Notes: {evidence.get('notes', 'None')}

AVAILABLE ISSUES:
{issue_list}

Please identify:
1. Which issues this evidence supports or relates to
2. The strength of the relationship (High/Medium/Low confidence)
3. Key points from the evidence that support each issue

Respond in JSON format:
{{
  "issues": ["issue_code1", "issue_code2"],
  "confidence": {{"issue_code1": "High", "issue_code2": "Medium"}},
  "key_points": ["Point 1", "Point 2"]
}}
"""
        return prompt

    def _run_llm_analysis(self, prompt: str) -> Dict[str, Any]:
        """Run LLM analysis on prompt

        Args:
            prompt: Analysis prompt

        Returns:
            LLM response as dictionary
        """
        # Placeholder implementation
        # In production, this would call an actual LLM API
        # For now, return a structured placeholder

        logger.info("Running LLM analysis (placeholder)")

        return {
            'issues': ['ISS-001', 'ISS-002'],
            'confidence': {
                'ISS-001': 'High',
                'ISS-002': 'Medium'
            },
            'key_points': [
                'Evidence shows delay in treatment',
                'Lack of proper documentation'
            ]
        }


class QuoteExtractor:
    """Extracts key quotes from evidence documents"""

    def __init__(self, drive_client, supabase_client, config):
        """Initialize quote extractor

        Args:
            drive_client: GoogleDriveClient instance
            supabase_client: SupabaseClient instance
            config: Configuration object
        """
        self.drive = drive_client
        self.supabase = supabase_client
        self.config = config

    def extract_quotes(self, evidence_id: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract key quotes from evidence

        Args:
            evidence_id: Evidence UUID
            context: Optional context for quote extraction

        Returns:
            List of extracted quotes with metadata
        """
        logger.info(f"Extracting quotes from evidence {evidence_id}")

        try:
            # Get evidence
            evidence = self.supabase.query_evidence({'id': evidence_id})
            if not evidence:
                logger.error(f"Evidence {evidence_id} not found")
                return []

            evidence_record = evidence[0]

            # Download document (placeholder - would actually extract text)
            # For now, use notes field
            text = evidence_record.get('notes', '')

            # Build extraction prompt
            prompt = self._build_extraction_prompt(text, context)

            # Run LLM extraction
            quotes = self._run_extraction(prompt)

            # Format results
            results = []
            for i, quote in enumerate(quotes):
                results.append({
                    'quote_id': f"Q{i+1}",
                    'evidence_id': evidence_id,
                    'exhibit_code': evidence_record.get('exhibit_code'),
                    'text': quote.get('text'),
                    'page': quote.get('page', 1),
                    'context': quote.get('context'),
                    'relevance': quote.get('relevance', 'High')
                })

            logger.info(f"Extracted {len(results)} quotes")
            return results

        except Exception as e:
            logger.error(f"Error extracting quotes: {e}")
            return []

    def batch_extract(self, evidence_ids: List[str], context: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Extract quotes from multiple evidence items

        Args:
            evidence_ids: List of evidence UUIDs
            context: Optional context

        Returns:
            Dictionary mapping evidence_id to quotes
        """
        results = {}
        for evidence_id in evidence_ids:
            quotes = self.extract_quotes(evidence_id, context)
            results[evidence_id] = quotes

        return results

    def _build_extraction_prompt(self, text: str, context: Optional[str]) -> str:
        """Build quote extraction prompt

        Args:
            text: Document text
            context: Optional context

        Returns:
            Formatted prompt
        """
        context_str = f"\nContext: {context}" if context else ""

        prompt = f"""
Extract the most relevant and impactful quotes from the following document.
Focus on quotes that are legally significant or factually important.{context_str}

DOCUMENT TEXT:
{text[:5000]}

For each quote, provide:
1. The exact quote text
2. Page number (if available)
3. Brief context explaining why it's important
4. Relevance rating (High/Medium/Low)

Respond in JSON format:
[
  {{
    "text": "Quote text",
    "page": 1,
    "context": "Why this is important",
    "relevance": "High"
  }}
]
"""
        return prompt

    def _run_extraction(self, prompt: str) -> List[Dict[str, Any]]:
        """Run LLM quote extraction

        Args:
            prompt: Extraction prompt

        Returns:
            List of extracted quotes
        """
        # Placeholder implementation
        logger.info("Running quote extraction (placeholder)")

        return [
            {
                'text': 'Patient presented with severe symptoms at 14:30',
                'page': 3,
                'context': 'Establishes timeline of events',
                'relevance': 'High'
            },
            {
                'text': 'No documentation of consent was found',
                'page': 7,
                'context': 'Evidence of procedural failure',
                'relevance': 'High'
            }
        ]
