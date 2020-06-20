from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64

class Plantas(models.Model):
    _name = 'vivero.planta'
    
    @api.depends('pedido_ids')
    def _compute_monto_pedido(self):
        for rec in self:
            monto_pedido = 0
            if rec.pedido_ids:
                for pedido in rec.pedido_ids:
                    monto_pedido = monto_pedido + pedido.amount_total
            rec.monto_pedido = monto_pedido

    name = fields.Char("Nombre")
    price = fields.Float("Precio")
    pedido_ids = fields.One2many(comodel_name='vivero.pedido',inverse_name='plant_id',string='Pedidos')
    monto_pedido = fields.Float('Monto Pedido',compute=_compute_monto_pedido,store=True)

class Pedidos(models.Model):
    _name = 'vivero.pedido'

    def process_file(self):
        if not self.order_file:
            raise ValidationError('Debe ingresar el archivo')
        self.datos = base64.decodestring(self.order_file)

    def change_state(self):
        if self.state == 'confirmed':
            self.state = 'delivered'
        if self.state == 'draft':
            self.state = 'confirmed'

    @api.constrains('qty')
    def check_qty(self):
        if self.qty > 1000000:
            raise ValidationError('No hay stock')
        if self.qty <= 0:
            raise ValidationError('Solo cantidades positivas por favor')

    @api.onchange('qty')
    def onchange_qty(self):
        self.amount_total = self.qty * self.plant_id.price
    
    def write(self,vals):
        vals['last_modification'] = fields.Datetime.now()
        return super(Pedidos, self).write(vals)

    def unlink(self):
        if self.qty > 0:
            raise ValidationError('No se pueden borrar pedidos con\ncantidades mayor a 0')
        return super(Pedidos, self).unlink()

    partner_id = fields.Many2one('res.partner',string='Cliente',domain=[('customer_rank','>',0)],required=True)
    plant_id = fields.Many2one('vivero.planta',string='Planta')
    qty = fields.Integer('Cantidad')
    amount_total = fields.Float('Monto total')
    last_modification = fields.Datetime('Ultima modificacion')
    state = fields.Selection(selection=[('draft','Borrador'),('confirmed','Confirmado'),('delivered','Entregado')],\
            string="Estado",default="draft")
    order_file = fields.Binary('Archivo')
    datos = fields.Text('Contenidos')
