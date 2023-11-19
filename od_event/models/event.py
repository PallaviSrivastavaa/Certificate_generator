from odoo import models, fields,_,api

class EventCertificate(models.Model):
    _inherit = 'event.event'
    
    event_id = fields.Many2one('event.event', string='event', required=True)
    partner_id = fields.Many2many(
        'res.partner', string='Recipients')
    
    att_name = fields.Char(
        string='Attendee Name', index='trigram',
        compute='_compute_name', readonly=False, store=True, tracking=10)
    email = fields.Char(string='Email', compute='_compute_email', readonly=False, store=True, tracking=11)
    phone = fields.Char(string='Phone', compute='_compute_phone', readonly=False, store=True, tracking=12)
    mobile = fields.Char(string='Mobile.view.form<', compute='_compute_mobile', readonly=False, store=True, tracking=13)
    email = fields.Char( string='Email')
    name=fields.Char(string='name')
   
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
    background_image=fields.Image('background image')



    @api.depends('partner_id')
    def _compute_name(self):
        for registration in self:
            if not registration.name and registration.partner_id:
                registration.name = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['name']
                ).get('name') or False

    @api.depends('partner_id')
    def _compute_email(self):
        for registration in self:
            if not registration.email and registration.partner_id:
                registration.email = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['email']
                ).get('email') or False

    @api.depends('partner_id')
    def _compute_phone(self):
        for registration in self:
            if not registration.phone and registration.partner_id:
                registration.phone = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['phone']
                ).get('phone') or False

    @api.depends('partner_id')
    def _compute_mobile(self):
        for registration in self:
            if not registration.mobile and registration.partner_id:
                registration.mobile = registration._synchronize_partner_values(
                    registration.partner_id,
                    fnames=['mobile']
                ).get('mobile') or False


    def _synchronize_partner_values(self, partner, fnames=None):
        if fnames is None:
            fnames = ['name', 'email', 'phone', 'mobile']
        if partner:
            contact_id = partner.address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                return dict((fname, contact[fname]) for fname in fnames if contact[fname])
        return {}


    def action_test(self):
        template = self.env.ref('od_event.certificate_mail_template', raise_if_not_found=False)
        
        local_context = dict(
            self.env.context,
            default_event_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_email_layout_xmlid='mail.mail_notification_light',
            default_mailing_domain=repr([('event_id', 'in', self.ids),('state', '!=', 'cancel')]),
            default_background_image =self.background_image or False,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _("Share a mail"),
            'view_mode': 'form',
            'res_model': 'event.send.mail',
            'target': 'new',
            'context': local_context,
        }
        


















        
        
