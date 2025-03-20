from odoo import api, fields, models

class FlightPilotLog(models.TransientModel):
    _name = 'flight.pilot.log.editor'
    _description = 'Pilot Log Editor'
    
    flight_id = fields.Many2one('flight.flight', string='Flight', required=True)
    partner_id = fields.Many2one('res.partner', string='Pilot', required=True)
    
    # Related fields from flight
    date = fields.Date(related='flight_id.date', readonly=True)
    departure_id = fields.Many2one(related='flight_id.departure_id', readonly=True)
    arrival_id = fields.Many2one(related='flight_id.arrival_id', readonly=True)
    aircraft_id = fields.Many2one(related='flight_id.aircraft_id', readonly=True)
    
    # Computed fields with inverse methods for editing
    pic_duration = fields.Float(
        string='PIC',
        compute='_compute_durations',
        inverse='_inverse_pic_duration',
    )
    
    sic_duration = fields.Float(
        string='SIC',
        compute='_compute_durations',
        inverse='_inverse_sic_duration',
    )
    
    to_day_count = fields.Integer(
        string='TO DAY',
        compute='_compute_event_counts',
        inverse='_inverse_to_day_count',
    )
    
    to_night_count = fields.Integer(
        string='TO NIGHT',
        compute='_compute_event_counts',
        inverse='_inverse_to_night_count',
    )
    
    remark = fields.Text(
        string='Remark',
        compute='_compute_remark',
        inverse='_inverse_remark',
    )
    
    @api.depends('flight_id', 'partner_id')
    def _compute_durations(self):
        PilotTime = self.env['flight.pilot.time']
        pic_code = self.env['flight.pilot.time.code'].search([('code', '=', 'PIC')], limit=1)
        sic_code = self.env['flight.pilot.time.code'].search([('code', '=', 'SIC')], limit=1)
        
        for record in self:
            pic_time = PilotTime.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('code_id', '=', pic_code.id)
            ], limit=1)
            record.pic_duration = pic_time.duration if pic_time else 0
            
            sic_time = PilotTime.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('code_id', '=', sic_code.id)
            ], limit=1)
            record.sic_duration = sic_time.duration if sic_time else 0
    
    def _inverse_pic_duration(self):
        PilotTime = self.env['flight.pilot.time']
        pic_code = self.env['flight.pilot.time.code'].search([('code', '=', 'PIC')], limit=1)
        
        for record in self:
            time_record = PilotTime.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('code_id', '=', pic_code.id)
            ], limit=1)
            
            if record.pic_duration > 0:
                if time_record:
                    time_record.duration = record.pic_duration
                else:
                    PilotTime.create({
                        'flight_id': record.flight_id.id,
                        'partner_id': record.partner_id.id,
                        'code_id': pic_code.id,
                        'duration': record.pic_duration
                    })
            elif time_record:
                time_record.unlink()
    
    def _inverse_sic_duration(self):
        PilotTime = self.env['flight.pilot.time']
        sic_code = self.env['flight.pilot.time.code'].search([('code', '=', 'SIC')], limit=1)
        
        for record in self:
            time_record = PilotTime.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('code_id', '=', sic_code.id)
            ], limit=1)
            
            if record.sic_duration > 0:
                if time_record:
                    time_record.duration = record.sic_duration
                else:
                    PilotTime.create({
                        'flight_id': record.flight_id.id,
                        'partner_id': record.partner_id.id,
                        'code_id': sic_code.id,
                        'duration': record.sic_duration
                    })
            elif time_record:
                time_record.unlink()
    
    @api.depends('flight_id', 'partner_id')
    def _compute_event_counts(self):
        PilotEvent = self.env['flight.pilot.event']
        to_day_code = self.env['flight.pilot.event.code'].search([('code', '=', 'TO_DAY')], limit=1)
        to_night_code = self.env['flight.pilot.event.code'].search([('code', '=', 'TO_NIGHT')], limit=1)
        
        for record in self:
            day_event = PilotEvent.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('event_code_id', '=', to_day_code.id)
            ], limit=1)
            record.to_day_count = day_event.count if day_event else 0
            
            night_event = PilotEvent.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('event_code_id', '=', to_night_code.id)
            ], limit=1)
            record.to_night_count = night_event.count if night_event else 0
    
    def _inverse_to_day_count(self):
        PilotEvent = self.env['flight.pilot.event']
        to_day_code = self.env['flight.pilot.event.code'].search([('code', '=', 'TO_DAY')], limit=1)
        
        for record in self:
            event_record = PilotEvent.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('event_code_id', '=', to_day_code.id)
            ], limit=1)
            
            if record.to_day_count > 0:
                if event_record:
                    event_record.count = record.to_day_count
                else:
                    PilotEvent.create({
                        'flight_id': record.flight_id.id,
                        'partner_id': record.partner_id.id,
                        'event_code_id': to_day_code.id,
                        'count': record.to_day_count
                    })
            elif event_record:
                event_record.unlink()
    
    def _inverse_to_night_count(self):
        PilotEvent = self.env['flight.pilot.event']
        to_night_code = self.env['flight.pilot.event.code'].search([('code', '=', 'TO_NIGHT')], limit=1)
        
        for record in self:
            event_record = PilotEvent.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('event_code_id', '=', to_night_code.id)
            ], limit=1)
            
            if record.to_night_count > 0:
                if event_record:
                    event_record.count = record.to_night_count
                else:
                    PilotEvent.create({
                        'flight_id': record.flight_id.id,
                        'partner_id': record.partner_id.id,
                        'event_code_id': to_night_code.id,
                        'count': record.to_night_count
                    })
            elif event_record:
                event_record.unlink()
    
    @api.depends('flight_id', 'partner_id')
    def _compute_remark(self):
        PilotRemark = self.env['flight.pilot.remark']
        
        for record in self:
            remark_record = PilotRemark.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id)
            ], limit=1)
            record.remark = remark_record.remark if remark_record else False
    
    def _inverse_remark(self):
        PilotRemark = self.env['flight.pilot.remark']
        
        for record in self:
            remark_record = PilotRemark.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id)
            ], limit=1)
            
            if record.remark:
                if remark_record:
                    remark_record.remark = record.remark
                else:
                    PilotRemark.create({
                        'flight_id': record.flight_id.id,
                        'partner_id': record.partner_id.id,
                        'remark': record.remark
                    })
            elif remark_record:
                remark_record.unlink()
    
    @api.model
    def load_pilot_logs(self):
        """Action method to load all pilot logs"""
        # Delete existing transient records for this user
        self.search([]).unlink()
        
        # Create transient records for all flight/pilot combinations
        self._cr.execute("""
            SELECT DISTINCT flight_id, partner_id
            FROM (
                SELECT flight_id, partner_id FROM flight_pilot_event
                UNION
                SELECT flight_id, partner_id FROM flight_pilot_time
                UNION
                SELECT flight_id, partner_id FROM flight_pilot_remark
            ) AS logs
        """)
        
        records = []
        for flight_id, partner_id in self._cr.fetchall():
            record = self.create({
                'flight_id': flight_id,
                'partner_id': partner_id,
            })
            records.append(record.id)
            
        # Return action to view the records
        action = self.env.ref('flight_pilotlog.action_flight_pilot_log').read()[0]
        action.update({
            'domain': [('id', 'in', records)],
            'context': {'create': False},
        })
        return action
