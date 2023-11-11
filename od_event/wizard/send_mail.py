import logging
import re
import werkzeug
from odoo.addons.base.models.res_partner import _tz_get

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

emails_split = re.compile(r"[;,\n\r]+")

class SendMail(models.TransientModel):
    _name = 'event.send.mail'
    _inherit = ['mail.composer.mixin']
    _description = 'send mail Wizard'

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
        print(email_from)
        mail_template = self.env.ref('od_event.certificate_mail_template', )
        for email in all_emails:        
            mail_values = {
                'subject': 'Your Subject',
                'email_to': email,
                'email_from': email_from,
                'body_html': 'Your HTML Body',
                
            }    
            mail_template.send_mail(self.id, force_send=True, email_values=mail_values)
        return {'type': 'ir.actions.act_window_close'}



       