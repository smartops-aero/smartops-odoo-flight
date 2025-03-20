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
    
    # Dynamic time fields
    pic_duration = fields.Float(
        string='PIC',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    sic_duration = fields.Float(
        string='SIC',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    dual_duration = fields.Float(
        string='DUAL',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    picus_duration = fields.Float(
        string='PICUS',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    instructor_duration = fields.Float(
        string='INSTRUCTOR',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    examiner_duration = fields.Float(
        string='EXAMINER',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    night_duration = fields.Float(
        string='NIGHT',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    xc_duration = fields.Float(
        string='CROSS-COUNTRY',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    ifr_duration = fields.Float(
        string='IFR',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    hood_duration = fields.Float(
        string='HOOD',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    imc_duration = fields.Float(
        string='IMC',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    relief_duration = fields.Float(
        string='RELIEF',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    safety_duration = fields.Float(
        string='SAFETY',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    air_duration = fields.Float(
        string='AIR',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    total_duration = fields.Float(
        string='TOTAL',
        compute='_compute_time_durations',
        inverse='_inverse_time_durations',
    )
    
    # Event counts
    to_day_count = fields.Integer(
        string='TO DAY',
        compute='_compute_event_counts',
        inverse='_inverse_event_counts',
    )
    
    to_night_count = fields.Integer(
        string='TO NIGHT',
        compute='_compute_event_counts',
        inverse='_inverse_event_counts',
    )
    
    remark = fields.Text(
        string='Remark',
        compute='_compute_remark',
        inverse='_inverse_remark',
    )
    
    # Map field names to code values for time durations
    _time_field_mapping = {
        'pic_duration': 'PIC',
        'sic_duration': 'SIC',
        'dual_duration': 'DUAL',
        'picus_duration': 'PICUS',
        'instructor_duration': 'INSTR',
        'examiner_duration': 'EXAM',
        'night_duration': 'NIGHT',
        'xc_duration': 'XC',
        'ifr_duration': 'IFR',
        'hood_duration': 'HOOD',
        'imc_duration': 'IMC',
        'relief_duration': 'RELIEF',
        'safety_duration': 'SAFETY',
        'air_duration': 'AIR',
        'total_duration': 'TOTAL',
    }
    
    # Map field names to code values for event counts
    _event_field_mapping = {
        'to_day_count': 'TO_DAY',
        'to_night_count': 'TO_NIGHT',
    }
    
    @api.depends('flight_id', 'partner_id')
    def _compute_time_durations(self):
        """Generic method to compute all time durations"""
        PilotTime = self.env['flight.pilot.time']
        
        # Get all time codes at once
        code_map = {}
        for code in self.env['flight.pilot.time.code'].search([]):
            code_map[code.code] = code.id
        
        for record in self:
            # First set all to zero
            for field_name in self._time_field_mapping:
                setattr(record, field_name, 0)
            
            # Get all time records for this flight/pilot pair at once
            time_records = PilotTime.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
            ])
            
            # Set values for existing records
            for time_record in time_records:
                for field_name, code in self._time_field_mapping.items():
                    if time_record.code_id.code == code:
                        setattr(record, field_name, time_record.duration)
    
    def _inverse_time_durations(self):
        """Generic method to handle setting all time durations"""
        PilotTime = self.env['flight.pilot.time']
        
        # Get all time codes at once
        code_map = {}
        for code in self.env['flight.pilot.time.code'].search([]):
            code_map[code.code] = code.id
        
        for record in self:
            # Handle all time fields
            for field_name, code in self._time_field_mapping.items():
                duration = getattr(record, field_name)
                code_id = code_map.get(code)
                
                if not code_id:
                    continue
                
                time_record = PilotTime.search([
                    ('flight_id', '=', record.flight_id.id),
                    ('partner_id', '=', record.partner_id.id),
                    ('code_id', '=', code_id)
                ], limit=1)
                
                if duration > 0:
                    if time_record:
                        time_record.duration = duration
                    else:
                        PilotTime.create({
                            'flight_id': record.flight_id.id,
                            'partner_id': record.partner_id.id,
                            'code_id': code_id,
                            'duration': duration
                        })
                elif time_record:
                    time_record.unlink()
    
    @api.depends('flight_id', 'partner_id')
    def _compute_event_counts(self):
        """Generic method to compute all event counts"""
        PilotEvent = self.env['flight.pilot.event']
        
        # Get all event codes at once
        code_map = {}
        for code in self.env['flight.pilot.event.code'].search([]):
            code_map[code.code] = code.id
        
        for record in self:
            # First set all to zero
            for field_name in self._event_field_mapping:
                setattr(record, field_name, 0)
            
            # Get all event records for this flight/pilot pair at once
            event_records = PilotEvent.search([
                ('flight_id', '=', record.flight_id.id),
                ('partner_id', '=', record.partner_id.id),
            ])
            
            # Set values for existing records
            for event_record in event_records:
                for field_name, code in self._event_field_mapping.items():
                    if event_record.event_code_id.code == code:
                        setattr(record, field_name, event_record.count)
    
    def _inverse_event_counts(self):
        """Generic method to handle setting all event counts"""
        PilotEvent = self.env['flight.pilot.event']
        
        # Get all event codes at once
        code_map = {}
        for code in self.env['flight.pilot.event.code'].search([]):
            code_map[code.code] = code.id
        
        for record in self:
            # Handle all event fields
            for field_name, code in self._event_field_mapping.items():
                count = getattr(record, field_name)
                code_id = code_map.get(code)
                
                if not code_id:
                    continue
                
                event_record = PilotEvent.search([
                    ('flight_id', '=', record.flight_id.id),
                    ('partner_id', '=', record.partner_id.id),
                    ('event_code_id', '=', code_id)
                ], limit=1)
                
                if count > 0:
                    if event_record:
                        event_record.count = count
                    else:
                        PilotEvent.create({
                            'flight_id': record.flight_id.id,
                            'partner_id': record.partner_id.id,
                            'event_code_id': code_id,
                            'count': count
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