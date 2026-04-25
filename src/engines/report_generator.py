"""PDF report generator for evaluation results"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.colors import HexColor

from src.models.schemas import EvaluationResult, CriterionEvaluation
from src.config import SystemConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    PDF report generator for evaluation results.
    
    Generates comprehensive evaluation reports with:
    - Bidder information and final verdict
    - Summary statistics
    - Detailed criterion evaluations with evidence
    - Manual overrides with reviewer details
    - Complete audit trail
    
    Implements Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
    """
    
    def __init__(self):
        """Initialize report generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("Initialized ReportGenerator")
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#1f77b4'),
            spaceAfter=10,
            spaceBefore=15
        ))
        
        # Criterion header style
        self.styles.add(ParagraphStyle(
            name='CriterionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=10
        ))
    
    def generate_report(
        self,
        result: EvaluationResult,
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate PDF evaluation report for a bidder.
        
        Implements Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
        
        Args:
            result: Evaluation result to generate report for
            output_path: Optional file path to save report (if None, returns BytesIO)
            
        Returns:
            BytesIO buffer containing PDF report
        """
        logger.info(f"Generating report for bidder: {result.bidder_name}")
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        if output_path:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
        else:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
        
        # Build report content
        story = []
        
        # Add header
        story.extend(self._build_header(result))
        
        # Add verdict section
        story.extend(self._build_verdict_section(result))
        
        # Add summary section
        story.extend(self._build_summary_section(result))
        
        # Add criterion evaluations
        story.extend(self._build_evaluations_section(result))
        
        # Add manual overrides section if any
        overrides = self._get_manual_overrides(result)
        if overrides:
            story.extend(self._build_overrides_section(overrides))
        
        # Add footer
        story.extend(self._build_footer(result))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Report generated successfully for {result.bidder_name}")
        
        if not output_path:
            buffer.seek(0)
        
        return buffer
    
    def _build_header(self, result: EvaluationResult) -> List:
        """Build report header with title and metadata."""
        elements = []
        
        # Title
        elements.append(Paragraph(
            "Tender Evaluation Report",
            self.styles['CustomTitle']
        ))
        
        # Subtitle
        elements.append(Paragraph(
            f"{SystemConfig.NAME} v{SystemConfig.VERSION}",
            self.styles['CustomSubtitle']
        ))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Bidder information table
        bidder_data = [
            ['Bidder Name:', result.bidder_name],
            ['Bidder ID:', result.bidder_id],
            ['Evaluation Date:', result.timestamp.strftime('%Y-%m-%d %H:%M:%S')],
            ['System Version:', result.system_version]
        ]
        
        bidder_table = Table(bidder_data, colWidths=[2*inch, 4*inch])
        bidder_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(bidder_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_verdict_section(self, result: EvaluationResult) -> List:
        """Build final verdict section with visual emphasis."""
        elements = []
        
        elements.append(Paragraph("Final Verdict", self.styles['SectionHeader']))
        
        # Verdict box with color coding
        verdict_color = {
            "Eligible": HexColor('#d4edda'),
            "Not Eligible": HexColor('#f8d7da'),
            "Needs Review": HexColor('#fff3cd')
        }[result.final_verdict]
        
        verdict_text_color = {
            "Eligible": HexColor('#155724'),
            "Not Eligible": HexColor('#721c24'),
            "Needs Review": HexColor('#856404')
        }[result.final_verdict]
        
        verdict_data = [[result.final_verdict]]
        verdict_table = Table(verdict_data, colWidths=[6*inch])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), verdict_text_color),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 2, verdict_text_color),
        ]))
        
        elements.append(verdict_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_summary_section(self, result: EvaluationResult) -> List:
        """Build summary statistics section."""
        elements = []
        
        elements.append(Paragraph("Summary Statistics", self.styles['SectionHeader']))
        
        summary = result.summary
        
        # Summary table
        summary_data = [
            ['Metric', 'All Criteria', 'Mandatory Only'],
            ['Total Criteria', str(summary['total_criteria']), '-'],
            ['Satisfied', str(summary['satisfied']), str(summary['mandatory_satisfied'])],
            ['Not Satisfied', str(summary['not_satisfied']), str(summary['mandatory_not_satisfied'])],
            ['Needs Review', str(summary['needs_review']), str(summary['mandatory_needs_review'])]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.75*inch, 1.75*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f0f0f0')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_evaluations_section(self, result: EvaluationResult) -> List:
        """Build detailed criterion evaluations section."""
        elements = []
        
        elements.append(Paragraph("Detailed Criterion Evaluations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Group by category
        categories = {}
        for eval in result.criterion_evaluations:
            category = eval.criterion.category
            if category not in categories:
                categories[category] = []
            categories[category].append(eval)
        
        # Render each category
        for category in ["Financial", "Technical", "Compliance", "Documentation"]:
            if category in categories:
                elements.extend(self._build_category_section(category, categories[category]))
        
        return elements
    
    def _build_category_section(self, category: str, evaluations: List[CriterionEvaluation]) -> List:
        """Build section for a specific criterion category."""
        elements = []
        
        elements.append(Paragraph(f"{category} Criteria ({len(evaluations)})", self.styles['SectionHeader']))
        
        for eval in evaluations:
            elements.extend(self._build_criterion_evaluation(eval))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_criterion_evaluation(self, eval: CriterionEvaluation) -> List:
        """Build detailed evaluation for a single criterion."""
        elements = []
        
        criterion = eval.criterion
        decision = eval.decision
        evidence = eval.extracted_evidence
        
        # Criterion header
        header_text = f"{criterion.id} - {criterion.priority}"
        elements.append(Paragraph(header_text, self.styles['CriterionHeader']))
        
        # Criterion details
        details_text = f"<b>Description:</b> {criterion.description}<br/>"
        if criterion.threshold_value:
            details_text += f"<b>Threshold:</b> {criterion.threshold_value} {criterion.threshold_unit or ''}<br/>"
        details_text += f"<b>Source:</b> Page {criterion.source_page}"
        
        elements.append(Paragraph(details_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Decision and evidence table
        eval_data = [
            ['Verdict', decision.verdict],
            ['Rule Applied', decision.rule_applied],
            ['Confidence', f"{evidence.confidence:.2f}"],
            ['Evidence Page', str(evidence.source_page)]
        ]
        
        if decision.comparison:
            eval_data.append(['Comparison', decision.comparison])
        
        eval_table = Table(eval_data, colWidths=[1.5*inch, 4.5*inch])
        eval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f0f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(eval_table)
        
        # Rationale
        rationale_text = f"<b>Rationale:</b> {decision.rationale}"
        elements.append(Spacer(1, 0.05*inch))
        elements.append(Paragraph(rationale_text, self.styles['Normal']))
        
        elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _get_manual_overrides(self, result: EvaluationResult) -> List[Dict]:
        """Extract manual overrides from evaluation result."""
        overrides = []
        
        for eval in result.criterion_evaluations:
            if 'manual_override' in eval.explainability_record:
                override_data = eval.explainability_record['manual_override']
                override_data['criterion_id'] = eval.criterion.id
                override_data['criterion_description'] = eval.criterion.description
                overrides.append(override_data)
        
        return overrides
    
    def _build_overrides_section(self, overrides: List[Dict]) -> List:
        """Build manual overrides section."""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Manual Overrides", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph(
            f"The following {len(overrides)} criterion evaluation(s) were manually overridden by reviewers:",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        for override in overrides:
            override_elements = []
            
            # Override header
            override_elements.append(Paragraph(
                f"<b>{override['criterion_id']}</b>",
                self.styles['CriterionHeader']
            ))
            
            # Override details
            override_data = [
                ['Criterion', override['criterion_description']],
                ['Original Verdict', override['original_verdict']],
                ['New Verdict', override['new_verdict']],
                ['Reviewer', override['reviewer_id']],
                ['Timestamp', override['timestamp']],
                ['Justification', override['justification']]
            ]
            
            override_table = Table(override_data, colWidths=[1.5*inch, 4.5*inch])
            override_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#fff3cd')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            override_elements.append(override_table)
            override_elements.append(Spacer(1, 0.15*inch))
            
            # Keep override together on same page
            elements.append(KeepTogether(override_elements))
        
        return elements
    
    def _build_footer(self, result: EvaluationResult) -> List:
        """Build report footer with compliance statement."""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("---", self.styles['Normal']))
        
        footer_text = (
            f"<i>This report was generated by {SystemConfig.NAME} v{SystemConfig.VERSION} "
            f"on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            "All decisions are based on deterministic rule-based logic applied to AI-extracted evidence. "
            "This report is formatted for government compliance and archival purposes.</i>"
        )
        
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements
