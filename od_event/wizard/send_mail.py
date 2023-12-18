import logging
import re
import werkzeug
from odoo.addons.base.models.res_partner import _tz_get
import os
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import base64
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import letter,landscape
from reportlab.pdfgen import canvas


emails_split = re.compile(r"[;,\n\r]+")

class SendMail(models.TransientModel):
    _name = 'event.send.mail'
    _inherit = ['mail.composer.mixin']
    _description = 'send mail Wizard'


    background_image = fields.Image('Background Image',readonly=True)
    attendee_name = fields.Many2one('event.registration',string='attendee name')
    attendee_id=fields.Many2many('event.registration',string='attendee')
    background_image = fields.Image("Background Image")
    x_coordinate=fields.Char()
    y_coordinate=fields.Char()
    event_id = fields.Many2one('event.event', string='event', required=True)
    #partner_id = fields.Many2many('res.partner',string='Recipients')
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

        attachment_data = self.background_image
        if attachment_data and self.x_coordinate and self.y_coordinate:
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
            pdf.drawString(int(self.x_coordinate), int(self.y_coordinate), f"{self.event_id.name}")

            pdf.save()

            # Seek to the beginning of the buffer
            pdf_buffer.seek(0)

            return pdf_buffer.read()
        elif(not(self.background_image)):
            raise UserError(_("No background image attachment found"))
        else:
            raise UserError(_("x or y coordinate not given"))
  
        
    @api.onchange('event_id')
    def get_attendees(self):
        if self.event_id:  
            registrations = self.env['event.registration'].search([('event_id', '=', self.event_id.id)])
            print(registrations)
            # Extract attendee IDs directly from the registrations
            attendee_ids = registrations.mapped('id')
            #used to update many2many fields with a list of IDs where 6 indicates the ids need to be updated and 0 indicates prev ids need to be cleared
            self.attendee_id = [(6, 0, attendee_ids)] 
        else:
            self.attendee_id = False
    def preview(self):
        pdf_buffer = BytesIO()
        # Create a new PDF document
        pdf = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))
        custom_page_size = (1000, 800)  
        pdf = canvas.Canvas(pdf_buffer, pagesize=custom_page_size)
        attachment_data = self.background_image
        if attachment_data and self.x_coordinate and self.y_coordinate:
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
            text_w= pdf.stringWidth(f"example name","Courier", 35)
            text_h=35
            text_x = (new_width - text_w) / 2
            text_y = (new_height - text_h) / 2

            pdf.drawString(text_x, text_y, f"example name")
            pdf.setFont("Courier-Bold", 25)
            pdf.drawString(int(self.x_coordinate), int(self.y_coordinate), f"example event")
            pdf.save()

            # Seek to the beginning of the buffer
            pdf_buffer.seek(0)

            pdf_content=pdf_buffer.read()
            save_name = os.path.join(os.path.expanduser("~"), "Downloads/", "example.pdf") #expand user is used to expand the initial path of the component
            with open(save_name, 'wb') as f:
                f.write(pdf_content)


        else:
            raise UserError(_("No background image attachment found or x and y coordinate given.."))


    def send_mail(self):
        self.ensure_one()
        
        # Ensure there are selected partners or additional emails
        if not self.attendee_id.ids and not self.emails:
            raise UserError(_("Please select at least one recipient or enter additional emails."))
        email_from = self.organizer_id.email_formatted
        event_name = self.event_id.name
        mail_template = self.env.ref('od_event.certificate_mail_template', raise_if_not_found=False)
        body = mail_template.body_html

        for attendee in self.attendee_id:
            attachment_data = self.get_attachment_data(attendee)
            body=body.replace('--event--',self.event_id.name)
            body=body.replace('--user--',self.user_id.name)



            mail_values = {
                'subject': f'Certificate for the event {event_name}',
                'email_to': attendee.email,
                'body_html':body,
                'email_from': email_from,
                'attachment_ids': [(0, 0, attachment_data)],    
            }
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()

    def close(self):
          return {'type': 'ir.actions.act_window_close'}


    

        
        