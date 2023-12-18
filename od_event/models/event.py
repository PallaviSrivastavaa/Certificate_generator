from odoo import models, fields,_
from reportlab.lib import fonts

class EventCertificate(models.Model):
    _inherit = 'event.event'
    
    event_id = fields.Many2one('event.event', string='event', required=True)
    partner_id = fields.Many2many(
        'res.partner', string='Recipients')
    email = fields.Char( string='Email')
    name=fields.Char(string='name')

    #font_family = fields.Selection(selection='_get_font_choices', string='Font Family')

    x_coordinate=fields.Char()
    y_coordinate=fields.Char()
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

    '''def _get_font_choices(self):
        font_list = fonts.getFonts()
        return [(font, font) for font in font_list]
    '''

    def action_test(self):
        template = self.env.ref('od_event.certificate_mail_template', raise_if_not_found=False)
        print(self.id)
        local_context = dict(
            self.env.context,
            default_event_id=self.id,
            default_event_name=self.event_id.name,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_email_layout_xmlid='mail.mail_notification_light',
            default_mailing_domain=repr([('event_id', 'in', self.ids),('state', '!=', 'cancel')]),
            default_background_image =self.background_image or False,
            default_x_coordinate=self.x_coordinate or False,
            default_y_coordinate=self.y_coordinate or False,

        )
        return {
            'type': 'ir.actions.act_window',
            'name': _("Share a mail"),
            'view_mode': 'form',
            'res_model': 'event.send.mail',
            'target': 'new',
            'context': local_context,
        }
        


















        
        
