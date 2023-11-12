import logging
import re
import werkzeug
from odoo.addons.base.models.res_partner import _tz_get

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import os
import base64
from PIL import Image, ImageDraw, ImageFont,ImageOps
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

emails_split = re.compile(r"[;,\n\r]+")

class SendMail(models.TransientModel):
    _name = 'event.send.mail'
    _inherit = ['mail.composer.mixin']
    _description = 'send mail Wizard'


    background_image = fields.Image("Background Image")
    name = fields.Char(string='Event')
    background_image = fields.Image("Background Image")
    event_id = fields.Many2one('event.event', string='event', required=True)
    partner_id = fields.Many2many('res.partner',string='Recipients')
    emails = fields.Text(string='Additional emails', help="This list of emails of recipients will not be converted in contacts.\
        #Emails must be separated by commas, semicolons or newline.")
    mail_server_id = fields.Many2one('ir.mail_server', 'Outgoing mail server')
    email_from = fields.Char(
        'From', compute='_compute_email_from', readonly=False, store=True)
    user_id = fields.Many2one(
        'res.users', string='Responsible', tracking=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True,
        default=lambda self: self.env.company,
        required=False)
    organizer_id = fields.Many2one(
        'res.partner', string='Organizer', tracking=True,
        default=lambda self: self.env.company.partner_id,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    @api.model
    def _get_default_author(self):
        print(self.env.user.partner_id)
        return self.env.user.partner_id
    author_id = fields.Many2one(
        'res.partner', 'Author', index=True,
        ondelete='set null', default=_get_default_author)

  

    @api.depends('template_id.email_from')
    def _compute_email_from(self):
        if self.template_id.email_from:
            self.email_from = self.template_id.email_from
        else:
            self.email_from = self.env.user.email_formatted
    
    
    
    def send_mail(self):
        self.ensure_one()
        # Ensure there are selected partners or additional emails
        if not self.partner_id.ids and not self.emails:
            raise UserError(_("Please select at least one recipient or enter additional emails."))
    

        # Get the email addresses from the selected partners
        partner_emails = [partner.email for partner in self.partner_id if partner.email]
        # Split and format additional emails
        additional_emails = []
        for email in emails_split.split(self.emails or ''):
            email_formatted = tools.email_split_and_format(email)
            if email_formatted:
                additional_emails.extend(email_formatted)
        # Combine all email addresses
        all_emails = partner_emails + additional_emails
        email_from = self.organizer_id.email_formatted
        event_name = self.event_id.name

        mail_template = self.env.ref('od_event.certificate_mail_template', raise_if_not_found=False)

        for email in all_emails:
            attachment_data = self.get_attachment_data()        
            mail_values = {
                'subject': f'Certificate for the event {event_name}',
                'email_to': email,
                'email_from': email_from,
                #'body_html': 'Your HTML Body',
                'attachment_ids': [(0, 0, attachment_data)],
                 
            }    
            mail_template.send_mail(self.id, force_send=True, email_values=mail_values)
        return {'type': 'ir.actions.act_window_close'}

    def get_attachment_data(self):
        pdf_content = self.generate_pdf_with_image()
        return {
            'name': 'Certificate.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'event.send.mail',
        }

    def generate_pdf_with_image(self):
        # Create a BytesIO object to store the PDF content
            pdf_buffer = BytesIO()

            # Create a new PDF document
            pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

            # Retrieve the attachment data from the field (replace 'your_attachment_field' with the actual field name)
            attachment_data = self.background_image
            if attachment_data:
                # Decode the base64-encoded data
                image_data = base64.b64decode(attachment_data)
                
                # Create a BytesIO object from the binary image data
                image_buffer = BytesIO(image_data)
                
                # Create a PIL Image object from the BytesIO object
                image = Image.open(image_buffer)

                # Draw the image on the PDF canvas
                pdf.drawInlineImage(image, 0, 0, width=letter[0], height=letter[1])

                # Add your logic to draw on the PDF and include attendee data
                pdf.setFont("Helvetica", 12)
                pdf.drawString(100, 750, f"Certificate for the event {self.event_id.name}")

                # Example: Adding attendee data
                y_position = 500
                for partner in self.partner_id:
                    pdf.drawString(100, y_position, f"Attendee: {partner.name}")
                    y_position -= 20

                # Save the PDF content
                pdf.save()

                # Seek to the beginning of the buffer
                pdf_buffer.seek(0)

                return pdf_buffer.read()
            else:
                raise UserError(_("No background image attachment found."))