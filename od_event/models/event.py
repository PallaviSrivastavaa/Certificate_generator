from odoo import models, fields,_

class EventEvent(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'mail.thread', 'mail.activity.mixin']
    
    event_id = fields.Many2one('event.event', string='event', required=True)
    partner_id = fields.Many2many(
        'res.partner', string='Recipients')

    def action_test(self):
        template = self.env.ref('od_event.certificate_mail_template', raise_if_not_found=False)

        local_context = dict(
            self.env.context,
            default_event_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_email_layout_xmlid='mail.mail_notification_light',
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _("Share a mail"),
            'view_mode': 'form',
            'res_model': 'event.send.mail',
            'target': 'new',
            'context': local_context,
        }
        


















        
        
