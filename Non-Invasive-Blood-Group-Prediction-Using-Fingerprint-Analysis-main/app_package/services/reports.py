from io import BytesIO
import csv
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, Reference


class ReportGenerator:
    
    @staticmethod
    def generate_predictions_pdf(predictions_data, stats_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#334155'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        title = Paragraph("Blood Group Predictions Report", title_style)
        elements.append(title)
        
        # Report metadata
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        metadata = Paragraph(f"<i>Generated on: {report_date}</i>", styles['Normal'])
        elements.append(metadata)
        elements.append(Spacer(1, 20))
        
        # Summary Statistics
        elements.append(Paragraph("Summary Statistics", heading_style))
        summary_data = [
            ['Metric', 'Value'],
            ['Total Predictions', str(stats_data.get('total_predictions', 0))],
            ['Average Confidence', f"{stats_data.get('avg_confidence', 0):.2f}%"],
            ['Total Users', str(stats_data.get('total_users', 0))],
            ['Date Range', stats_data.get('date_range', 'All Time')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 30))
        
        # Recent Predictions Table
        elements.append(Paragraph("Recent Predictions", heading_style))
        
        if predictions_data:
            pred_table_data = [['Date', 'Blood Type', 'Confidence', 'User', '# Prints']]
            
            for pred in predictions_data[:20]:  # Limit to 20 most recent
                pred_table_data.append([
                    pred.get('timestamp', 'N/A'),
                    pred.get('blood_type', 'N/A'),
                    f"{pred.get('confidence', 0):.1f}%",
                    pred.get('user', 'Anonymous'),
                    str(pred.get('num_prints', 0))
                ])
            
            pred_table = Table(pred_table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.8*inch, 0.9*inch])
            pred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
            ]))
            
            elements.append(pred_table)
        else:
            elements.append(Paragraph("<i>No predictions found.</i>", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_accuracy_excel(predictions_data, stats_data, blood_group_dist):
        """Generate Excel report for accuracy analysis"""
        buffer = BytesIO()
        wb = Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Summary Sheet
        ws_summary = wb.create_sheet("Summary")
        ws_summary.merge_cells('A1:D1')
        title_cell = ws_summary['A1']
        title_cell.value = "Blood Group Prediction - Accuracy Analysis"
        title_cell.font = Font(size=16, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_summary.row_dimensions[1].height = 30
        
        # Metadata
        ws_summary['A3'] = "Report Generated:"
        ws_summary['B3'] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        ws_summary['A4'] = "Report Type:"
        ws_summary['B4'] = "Accuracy Analysis"
        
        # Key Metrics
        ws_summary['A6'] = "Key Metrics"
        ws_summary['A6'].font = Font(size=14, bold=True)
        
        metrics = [
            ['Metric', 'Value'],
            ['Total Predictions', stats_data.get('total_predictions', 0)],
            ['Average Confidence Score', f"{stats_data.get('avg_confidence', 0):.2f}%"],
            ['Highest Confidence', f"{stats_data.get('max_confidence', 0):.2f}%"],
            ['Lowest Confidence', f"{stats_data.get('min_confidence', 0):.2f}%"],
            ['Total Users', stats_data.get('total_users', 0)],
        ]
        
        for idx, row in enumerate(metrics, start=7):
            ws_summary[f'A{idx}'] = row[0]
            ws_summary[f'B{idx}'] = row[1]
            if idx == 7:
                ws_summary[f'A{idx}'].font = Font(bold=True)
                ws_summary[f'B{idx}'].font = Font(bold=True)
                ws_summary[f'A{idx}'].fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
                ws_summary[f'B{idx}'].fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
        
        # Set column widths
        ws_summary.column_dimensions['A'].width = 25
        ws_summary.column_dimensions['B'].width = 20
        
        # Blood Group Distribution Sheet
        ws_dist = wb.create_sheet("Blood Group Distribution")
        ws_dist['A1'] = "Blood Group"
        ws_dist['B1'] = "Count"
        ws_dist['C1'] = "Percentage"
        
        for cell in ['A1', 'B1', 'C1']:
            ws_dist[cell].font = Font(bold=True, color="FFFFFF")
            ws_dist[cell].fill = PatternFill(start_color="8B5CF6", end_color="8B5CF6", fill_type="solid")
            ws_dist[cell].alignment = Alignment(horizontal="center")
        
        total = sum(blood_group_dist.values()) if blood_group_dist else 1
        row = 2
        for blood_type, count in sorted(blood_group_dist.items()):
            ws_dist[f'A{row}'] = blood_type
            ws_dist[f'B{row}'] = count
            ws_dist[f'C{row}'] = f"{(count/total*100):.1f}%"
            row += 1
        
        ws_dist.column_dimensions['A'].width = 15
        ws_dist.column_dimensions['B'].width = 12
        ws_dist.column_dimensions['C'].width = 15
        
        # Add chart
        if blood_group_dist:
            chart = PieChart()
            chart.title = "Blood Group Distribution"
            labels = Reference(ws_dist, min_col=1, min_row=2, max_row=row-1)
            data = Reference(ws_dist, min_col=2, min_row=1, max_row=row-1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(labels)
            ws_dist.add_chart(chart, "E2")
        
        # Detailed Predictions Sheet
        ws_detail = wb.create_sheet("Detailed Predictions")
        headers = ['Timestamp', 'Blood Type', 'Confidence (%)', 'User', '# Fingerprints']
        
        for col, header in enumerate(headers, start=1):
            cell = ws_detail.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        for idx, pred in enumerate(predictions_data, start=2):
            ws_detail.cell(row=idx, column=1, value=pred.get('timestamp', 'N/A'))
            ws_detail.cell(row=idx, column=2, value=pred.get('blood_type', 'N/A'))
            ws_detail.cell(row=idx, column=3, value=float(pred.get('confidence', 0)))
            ws_detail.cell(row=idx, column=4, value=pred.get('user', 'Anonymous'))
            ws_detail.cell(row=idx, column=5, value=pred.get('num_prints', 0))
        
        # Set column widths
        ws_detail.column_dimensions['A'].width = 20
        ws_detail.column_dimensions['B'].width = 15
        ws_detail.column_dimensions['C'].width = 15
        ws_detail.column_dimensions['D'].width = 20
        ws_detail.column_dimensions['E'].width = 15
        
        # Save to buffer
        wb.save(buffer)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_donors_csv(donors_data):
        """Generate CSV report for donors"""
        buffer = BytesIO()
        
        # Write CSV data
        output = csv.writer(buffer)
        
        # Header
        output.writerow(['Donor ID', 'Name', 'Blood Group', 'Phone', 'Email', 'City', 
                        'Pincode', 'Address', 'Active', 'Last Updated'])
        
        # Data rows
        for donor in donors_data:
            output.writerow([
                donor.get('id', ''),
                donor.get('name', ''),
                donor.get('blood_group', ''),
                donor.get('phone', ''),
                donor.get('email', ''),
                donor.get('city', ''),
                donor.get('pincode', ''),
                donor.get('address', ''),
                'Yes' if donor.get('is_active', False) else 'No',
                donor.get('last_updated', '')
            ])
        
        # Get the CSV string
        csv_string = buffer.getvalue().decode('utf-8')
        
        # Create a new buffer with the string
        result_buffer = BytesIO()
        result_buffer.write(csv_string.encode('utf-8-sig'))  # UTF-8 with BOM for Excel compatibility
        result_buffer.seek(0)
        
        return result_buffer
    
    @staticmethod
    def generate_system_performance_pdf(stats_data, predictions_data):
        """Generate PDF report for system performance"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#334155'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        title = Paragraph("System Performance Report", title_style)
        elements.append(title)
        
        # Report metadata
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        metadata = Paragraph(f"<i>Comprehensive Analysis - Generated on: {report_date}</i>", styles['Normal'])
        elements.append(metadata)
        elements.append(Spacer(1, 20))
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        summary_text = f"""
        This report provides a comprehensive analysis of the Blood Group Prediction System's performance.
        The system has processed <b>{stats_data.get('total_predictions', 0)}</b> predictions with an average 
        confidence score of <b>{stats_data.get('avg_confidence', 0):.2f}%</b>. The system maintains 
        <b>{stats_data.get('total_donors', 0)}</b> registered donors and <b>{stats_data.get('total_blood_banks', 0)}</b> 
        active blood banks in the network.
        """
        elements.append(Paragraph(summary_text, styles['BodyText']))
        elements.append(Spacer(1, 20))
        
        # Performance Metrics
        elements.append(Paragraph("Performance Metrics", heading_style))
        metrics_data = [
            ['Metric', 'Value', 'Status'],
            ['Average Processing Time', f"{stats_data.get('processing_time', 2.5):.2f}s", 'Excellent'],
            ['System Uptime', f"{stats_data.get('uptime', 99.7):.1f}%", 'Excellent'],
            ['Average Confidence Score', f"{stats_data.get('avg_confidence', 0):.2f}%", 'Good'],
            ['Total Predictions', str(stats_data.get('total_predictions', 0)), 'Active'],
            ['Active Users', str(stats_data.get('total_users', 0)), 'Growing'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecfdf5')]),
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, 30))
        
        # Usage Statistics
        elements.append(Paragraph("Usage Statistics", heading_style))
        usage_data = [
            ['Category', 'Count'],
            ['Total Predictions', str(stats_data.get('total_predictions', 0))],
            ['Registered Donors', str(stats_data.get('total_donors', 0))],
            ['Active Blood Banks', str(stats_data.get('total_blood_banks', 0))],
            ['Active Emergency Requests', str(stats_data.get('active_emergencies', 0))],
            ['Total Users', str(stats_data.get('total_users', 0))],
        ]
        
        usage_table = Table(usage_data, colWidths=[3*inch, 2*inch])
        usage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ec4899')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fdf2f8')]),
        ]))
        
        elements.append(usage_table)
        elements.append(Spacer(1, 20))
        
        # Recommendations
        elements.append(Paragraph("Recommendations", heading_style))
        recommendations = """
        <bullet>•</bullet> Continue monitoring system performance to maintain high uptime<br/>
        <bullet>•</bullet> Consider expanding blood donor network in underserved areas<br/>
        <bullet>•</bullet> Regular model retraining to improve prediction accuracy<br/>
        <bullet>•</bullet> Implement automated alerts for critical blood shortages<br/>
        <bullet>•</bullet> Enhance user engagement through mobile notifications
        """
        elements.append(Paragraph(recommendations, styles['BodyText']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
