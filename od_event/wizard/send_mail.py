import logging
import re
import werkzeug

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

emails_split = re.compile(r"[;,\n\r]+")

class SendMail(models.TransientModel):
    _name = 'event.send.mail'
    _inherit = ['mail.composer.mixin','event.registration']
    _description = 'send mail Wizard'

    event_id = fields.Many2one('event.event', string='event', required=True)
    partner_id = fields.Many2many(
        'res.partner', string='Recipients')
   
   

    emails = fields.Text(string='Additional emails', help="This list of emails of recipients will not be converted in contacts.\
        #Emails must be separated by commas, semicolons or newline.")
    

    @api.model
    def _get_default_author(self):
        return self.env.user.partner_id
    email_from = fields.Char(
        'From', compute='_compute_email_from', readonly=False, store=True)
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
     print("blue")
       