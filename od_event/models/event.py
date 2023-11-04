from odoo import models, fields

class EventEvent(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'mail.thread', 'mail.activity.mixin']
    

    def action_test(self):
        template_id= self.env.ref("od_event.certificate_mail_template").id
        self.env['mail.template'].browse(template_id).send_mail(self.id,force_send=True)
        


















        
        
