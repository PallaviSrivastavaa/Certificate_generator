import logging
import re
import werkzeug
from odoo.addons.base.models.res_partner import _tz_get

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import base64
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import letter,landscape
from reportlab.pdfgen import canvas
from pdf2image import convert_from_bytes

emails_split = re.compile(r"[;,\n\r]+")

class SendMail(models.TransientModel):
    _name = 'event.send.mail'
    _inherit = ['mail.composer.mixin']
    _description = 'send mail Wizard'


    background_image = fields.Image('Background Image',readonly=True)
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
        'res.users', string='Responsible', 
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True,
        default=lambda self: self.env.company,
        required=False)
    organizer_id = fields.Many2one(
        'res.partner', string='Organizer', 
        default=lambda self: self.env.company.partner_id,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
  
    @api.depends('template_id.email_from')
    def _compute_email_from(self):
        if self.template_id.email_from:
            self.email_from = self.template_id.email_from
        else:
            self.email_from = self.env.user.email_formatted
   
        
       
    def get_attachment_data(self,partner):
        pdf_content = self.generate_pdf_with_image(partner)
        return {
            'name': 'Certificate.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'event.send.mail',

        }
    
    
    def generate_pdf_with_image(self, partner):
        # Create a BytesIO object to store the PDF content
        pdf_buffer = BytesIO()

        # Create a new PDF document
        pdf = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))
        custom_page_size = (1000, 800)  

        pdf = canvas.Canvas(pdf_buffer, pagesize=custom_page_size)


        background_image = self.env.context.get('default_background_image', False)
        attachment_data = self.background_image
        if attachment_data:
            # Decode the base64-encoded data
            image_data = base64.b64decode(attachment_data)
           
            # Create a BytesIO object from the binary image data
            image_buffer = BytesIO(image_data)

            # Create a PIL Image object from the BytesIO object
            image = Image.open(image_buffer)

            original_width, original_height = image.size

            # Calculate the scaling factors for width and height
            scaling_factor_width = custom_page_size[0] / original_width
            scaling_factor_height = custom_page_size[1] / original_height

            # Use the smaller scaling factor to maintain the aspect ratio
            scaling_factor = min(scaling_factor_width, scaling_factor_height)

            
            new_width = int(original_width * scaling_factor)
            new_height = int(original_height * scaling_factor)

            # Resize the image using the calculated dimensions
            resized_image = image.resize((new_width, new_height), Image.ANTIALIAS) #ANTIALIAS is a high-quality resampling filter that smoothens the resized image.

            
            pdf_buffer = BytesIO()

           
            pdf = canvas.Canvas(pdf_buffer, pagesize=custom_page_size)

            pdf.drawInlineImage(resized_image, 0, 0, width=custom_page_size[0], height=custom_page_size[1])
            #pdf.setFont("Helvetica", 35)
            pdf.setFont("Courier", 35)
            text_w= pdf.stringWidth(f"{partner.name}","Courier", 35)
            text_h=35
            text_x = (new_width - text_w) / 2
            text_y = (new_height - text_h) / 2

            pdf.drawString(text_x, text_y, f"{partner.name}")
            pdf.setFont("Courier-Bold", 25)
            pdf.drawString(450, 280, f"{self.event_id.name}")

            pdf.save()

            # Seek to the beginning of the buffer
            pdf_buffer.seek(0)

            return pdf_buffer.read()
        else:
            raise UserError(_("No background image attachment found."))
        
    @api.onchange('event_id')
    def get_attendees(self):
            if self.event_id:
             
                registrations = self.env['event.registration'].search([('event_id', '=', self.event_id.id)])
                partner_ids = registrations.mapped('partner_id')
                self.partner_id = partner_ids
                print(partner_ids)
                print(self.event_id)
            else:
                self.partner_id = False
       

        

    def send_mail(self):
        self.ensure_one()
        # Ensure there are selected partners or additional emails
        if not self.partner_id.ids and not self.emails:
            raise UserError(_("Please select at least one recipient or enter additional emails."))

        email_from = self.organizer_id.email_formatted
        event_name = self.event_id.name

        mail_template = self.env.ref('od_event.certificate_mail_template', raise_if_not_found=False)

        for partner in self.partner_id:
            attachment_data = self.get_attachment_data(partner)

            mail_values = {
                'subject': f'Certificate for the event {event_name}',
                'email_to': partner.email,
                'email_from': email_from,
                'attachment_ids': [(0, 0, attachment_data)],
            }
            mail_template.send_mail(self.id, force_send=True, email_values=mail_values)

        return {'type': 'ir.actions.act_window_close'}


    '''
    def preview_image(self, partner):
        # Create a BytesIO object to store the PDF content
        pdf_buffer = BytesIO()

        # Create a new PDF document
        pdf = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))
        custom_page_size = (1000, 800)  

        pdf = canvas.Canvas(pdf_buffer, pagesize=custom_page_size)


   
        attachment_data = self.background_image
        if attachment_data:
            # Decode the base64-encoded data
            image_data = base64.b64decode(attachment_data)
           
            # Create a BytesIO object from the binary image data
            image_buffer = BytesIO(image_data)

            # Create a PIL Image object from the BytesIO object
            image = Image.open(image_buffer)

            original_width, original_height = image.size

            # Calculate the scaling factors for width and height
            scaling_factor_width = custom_page_size[0] / original_width
            scaling_factor_height = custom_page_size[1] / original_height

            # Use the smaller scaling factor to maintain the aspect ratio
            scaling_factor = min(scaling_factor_width, scaling_factor_height)

            
            new_width = int(original_width * scaling_factor)
            new_height = int(original_height * scaling_factor)

            # Resize the image using the calculated dimensions
            resized_image = image.resize((new_width, new_height), Image.ANTIALIAS) #ANTIALIAS is a high-quality resampling filter that smoothens the resized image.

            
            pdf_buffer = BytesIO()

           
            pdf = canvas.Canvas(pdf_buffer, pagesize=custom_page_size)

            pdf.drawInlineImage(resized_image, 0, 0, width=custom_page_size[0], height=custom_page_size[1])
            #pdf.setFont("Helvetica", 35)
            pdf.setFont("Courier", 35)
            text_w= pdf.stringWidth(f"{partner.name}","Courier", 35)
            text_h=35
            text_x = (new_width - text_w) / 2
            text_y = (new_height - text_h) / 2
            
          
           
           
            pdf.drawString(text_x, text_y, f"{partner.name}")
            pdf.setFont("Courier", 25)
            pdf.drawString(450, 280, f"{self.event_id.name}")

            pdf.save()
            pdf_image = convert_from_bytes(pdf_buffer.read())
            pdf_image.show()
            # Seek to the beginning of the buffer
            pdf_buffer.seek(0)

            
        else:
            raise UserError(_("No background image attachment found."))
        '''
        