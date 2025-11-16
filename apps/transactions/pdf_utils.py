"""
PDF generation utilities for financial statements
"""
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Path, Circle, Polygon
from reportlab.graphics import renderPDF
from django.conf import settings


class StatementPDFGenerator:
    """Generate PDF statements for buyers and sellers"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='StatementTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='StatementHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            spaceBefore=15,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='StatementBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563')
        ))

        self.styles.add(ParagraphStyle(
            name='StatementRight',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        ))

    def _format_currency(self, amount):
        """Format decimal as currency string"""
        if amount is None:
            return "KES 0.00"
        return f"KES {amount:,.2f}"

    def _format_date(self, date_obj):
        """Format datetime object"""
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%b %d, %Y %I:%M %p")
        return str(date_obj)

    def _create_trophy_logo(self):
        """Create a simple trophy icon using ReportLab drawing"""
        d = Drawing(40, 40)

        # Trophy color - gold/yellow
        trophy_color = colors.HexColor('#fbbf24')

        # Trophy cup (polygon)
        cup = Polygon([
            15, 25,  # top left
            10, 10,  # bottom left
            30, 10,  # bottom right
            25, 25   # top right
        ])
        cup.fillColor = trophy_color
        cup.strokeColor = colors.HexColor('#f59e0b')
        cup.strokeWidth = 1
        d.add(cup)

        # Trophy base
        base = Polygon([
            8, 10,   # top left
            8, 7,    # bottom left
            32, 7,   # bottom right
            32, 10   # top right
        ])
        base.fillColor = trophy_color
        base.strokeColor = colors.HexColor('#f59e0b')
        base.strokeWidth = 1
        d.add(base)

        # Trophy handles (circles on sides)
        left_handle = Circle(12, 20, 3)
        left_handle.fillColor = None
        left_handle.strokeColor = trophy_color
        left_handle.strokeWidth = 2
        d.add(left_handle)

        right_handle = Circle(28, 20, 3)
        right_handle.fillColor = None
        right_handle.strokeColor = trophy_color
        right_handle.strokeWidth = 2
        d.add(right_handle)

        # Star on top of trophy
        star_points = []
        for i in range(5):
            angle = i * 72 - 90  # -90 to start at top
            import math
            x = 20 + 4 * math.cos(math.radians(angle))
            y = 30 + 4 * math.sin(math.radians(angle))
            star_points.extend([x, y])

            # Inner point
            angle_inner = angle + 36
            x_inner = 20 + 1.5 * math.cos(math.radians(angle_inner))
            y_inner = 30 + 1.5 * math.sin(math.radians(angle_inner))
            star_points.extend([x_inner, y_inner])

        star = Polygon(star_points)
        star.fillColor = colors.HexColor('#fbbf24')
        star.strokeColor = colors.HexColor('#f59e0b')
        star.strokeWidth = 0.5
        d.add(star)

        return d

    def generate_buyer_statement(self, user, statement_data, start_date=None, end_date=None):
        """
        Generate PDF statement for buyers (transaction history)

        Args:
            user: User object
            statement_data: List of transaction entries from AccountingService.get_user_statement()
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # Build document content
        story = []

        # Header with Logo and Ligisoo branding
        logo = self._create_trophy_logo()

        # Create header table with logo and title
        header_data = [[logo, Paragraph("<b>LIGISOO</b>", self.styles['StatementTitle'])]]
        header_table = Table(header_data, colWidths=[0.6*inch, 6.9*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.1*inch))

        # Subtitle
        story.append(Paragraph("Transaction Statement", self.styles['StatementHeading']))
        story.append(Spacer(1, 0.15*inch))

        # Account Information - Horizontal Layout (more compact)
        # Get account holder name, fallback to phone if no name
        account_holder = user.get_full_name() if user.get_full_name() and user.get_full_name().strip() else user.phone_number

        # Build period text
        period_text = ""
        if start_date and end_date:
            period_text = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        elif start_date:
            period_text = f"From {start_date.strftime('%b %d, %Y')}"
        elif end_date:
            period_text = f"Until {end_date.strftime('%b %d, %Y')}"
        else:
            period_text = "All Time"

        # Single row with all info - using Paragraph to render HTML
        account_info = [[
            Paragraph(f"<b>Account:</b> {account_holder}", self.styles['StatementBody']),
            Paragraph(f"<b>Phone:</b> {user.phone_number}", self.styles['StatementBody']),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%b %d, %Y')}", self.styles['StatementBody'])
        ]]

        account_table = Table(account_info, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        account_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(account_table)

        # Period info if filtered
        if period_text and period_text != "All Time":
            story.append(Spacer(1, 0.1*inch))
            period_para = Paragraph(f"<i>Period: {period_text}</i>", self.styles['StatementBody'])
            story.append(period_para)

        story.append(Spacer(1, 0.2*inch))

        # Current Balance - Label left, amount right
        current_balance = user.userprofile.get_accounting_balance()
        balance_data = [[
            Paragraph('Current Balance', self.styles['StatementBody']),
            Paragraph(f'<b>{self._format_currency(current_balance)}</b>', self.styles['StatementBody'])
        ]]
        balance_table = Table(balance_data, colWidths=[3.75*inch, 3.75*inch])
        balance_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (0, 0), 10),
            ('FONTSIZE', (1, 0), (1, 0), 16),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#059669')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d1fae5')),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(balance_table)
        story.append(Spacer(1, 0.3*inch))

        # Transactions Table
        story.append(Paragraph("Transaction History", self.styles['StatementHeading']))

        if not statement_data:
            story.append(Paragraph("No transactions found for the selected period.", self.styles['StatementBody']))
        else:
            # Table headers
            transaction_table_data = [[
                'Date',
                'Reference',
                'Description',
                'Type',
                'Debit',
                'Credit',
                'Balance'
            ]]

            # Add transaction rows
            for entry in statement_data:
                debit_str = self._format_currency(entry['debit']) if entry['debit'] else '-'
                credit_str = self._format_currency(entry['credit']) if entry['credit'] else '-'
                balance_str = self._format_currency(entry['balance'])

                # Format date
                date_str = entry['date'].strftime("%m/%d/%Y %H:%M") if isinstance(entry['date'], datetime) else str(entry['date'])

                # Truncate description if too long
                description = entry['description'][:40] + '...' if len(entry['description']) > 40 else entry['description']

                transaction_table_data.append([
                    date_str,
                    entry['reference'][:12] + '...' if len(entry['reference']) > 12 else entry['reference'],
                    description,
                    entry.get('transaction_type', 'N/A')[:10],
                    debit_str,
                    credit_str,
                    balance_str
                ])

            # Create table
            col_widths = [1*inch, 1*inch, 1.8*inch, 0.8*inch, 0.9*inch, 0.9*inch, 0.9*inch]
            transaction_table = Table(transaction_table_data, colWidths=col_widths, repeatRows=1)

            # Style the table
            transaction_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),

                # Body styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (4, 1), (6, -1), 'RIGHT'),  # Align amounts to right

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),

                # Padding
                ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))

            story.append(transaction_table)

        # Footer
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph(
            "<i>Note: Debit indicates money received into your wallet, Credit indicates money spent from your wallet.</i>",
            self.styles['StatementBody']
        ))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_seller_statement(self, user, earnings_data):
        """
        Generate PDF earnings statement for sellers/tipsters

        Args:
            user: User object (tipster)
            earnings_data: Dictionary containing earnings information

        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        story = []

        # Header with Logo and Ligisoo branding
        logo = self._create_trophy_logo()

        # Create header table with logo and title
        header_data = [[logo, Paragraph("<b>LIGISOO</b>", self.styles['StatementTitle'])]]
        header_table = Table(header_data, colWidths=[0.6*inch, 6.9*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.1*inch))

        # Subtitle
        story.append(Paragraph("Earnings Statement", self.styles['StatementHeading']))
        story.append(Spacer(1, 0.15*inch))

        # Tipster Information - Horizontal Layout (more compact)
        # Get tipster name, fallback to phone if no name
        tipster_name = user.get_full_name() if user.get_full_name() and user.get_full_name().strip() else user.phone_number

        # Single row with all info - using Paragraph to render HTML
        tipster_info = [[
            Paragraph(f"<b>Tipster:</b> {tipster_name}", self.styles['StatementBody']),
            Paragraph(f"<b>Phone:</b> {user.phone_number}", self.styles['StatementBody']),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%b %d, %Y')}", self.styles['StatementBody'])
        ]]

        tipster_table = Table(tipster_info, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        tipster_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(tipster_table)
        story.append(Spacer(1, 0.2*inch))

        # Earnings Summary
        story.append(Paragraph("Earnings Summary", self.styles['StatementHeading']))

        summary_data = [
            ['Total Revenue (100%):', self._format_currency(earnings_data.get('total_revenue', 0))],
            ['Platform Commission (40%):', self._format_currency(earnings_data.get('platform_commission', 0))],
            ['Your Earnings (60%):', self._format_currency(earnings_data.get('tipster_earnings', 0))],
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (1, 1), 10),
            ('FONTSIZE', (0, 2), (1, 2), 12),  # Larger font for total earnings
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # Explicitly left-align labels
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Right-align amounts
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#d1fae5')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#059669')),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # Performance Metrics
        story.append(Paragraph("Performance Metrics", self.styles['StatementHeading']))

        metrics_data = [
            ['Total Purchases:', str(earnings_data.get('total_purchases', 0))],
            ['Unique Buyers:', str(earnings_data.get('unique_buyers', 0))],
            ['Repeat Customers:', str(earnings_data.get('repeat_customers', 0))],
            ['Tips Sold:', str(earnings_data.get('tips_count', 0))],
        ]

        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # Explicitly left-align labels
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Right-align values
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))

        # Recent Transactions (if provided)
        if 'recent_transactions' in earnings_data and earnings_data['recent_transactions']:
            story.append(Paragraph("Recent Sales", self.styles['StatementHeading']))

            transactions_table_data = [['Date', 'Tip', 'Amount', 'Your Share']]

            for txn in earnings_data['recent_transactions'][:10]:  # Limit to 10 recent
                date_str = txn['date'].strftime("%m/%d/%Y") if isinstance(txn['date'], datetime) else str(txn['date'])
                tip_title = txn['tip_title'][:30] + '...' if len(txn['tip_title']) > 30 else txn['tip_title']
                amount_str = self._format_currency(txn['amount'])
                share_str = self._format_currency(txn['tipster_share'])

                transactions_table_data.append([date_str, tip_title, amount_str, share_str])

            transactions_table = Table(transactions_table_data, colWidths=[1.2*inch, 3*inch, 1.2*inch, 1.2*inch])
            transactions_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                # Body
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),    # Left-align headers and first two columns
                ('ALIGN', (2, 1), (3, -1), 'RIGHT'),   # Right-align amount columns
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ]))
            story.append(transactions_table)

        # Footer
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph(
            "<i>Revenue Split: 60% to Tipster, 40% Platform Commission</i>",
            self.styles['StatementBody']
        ))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
