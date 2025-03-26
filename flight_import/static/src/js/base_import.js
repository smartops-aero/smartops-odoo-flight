odoo.define('flight_import.import', function (require) {
    "use strict";
    
    var DataImport = require('base_import.import').DataImport;
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;
    
    // Extend DataImport for flight.flight model
    DataImport.include({
        events: _.extend({}, DataImport.prototype.events, {
            'change select.flight_import_transformation': function (e) {
                this.transformation_type = $(e.currentTarget).val();
                
                // First, update the transformation type on the server
                this._rpc({
                    model: 'base_import.import',
                    method: 'write',
                    args: [[this.id], {transformation_type: this.transformation_type}],
                }).then(() => {
                    // Then, if transformation is active, update preview
                    if (this.transformation_type !== 'none') {
                        // Show loading indicator
                        $.blockUI({message: qweb.render('base_import.progressDialog', {
                            task: _t('Preparing transformation preview')
                        })});
                        $(document.body).addClass('o_ui_blocked');
                        
                        // Call the transformation preview method once
                        this._rpc({
                            model: 'base_import.import',
                            method: 'update_transformation_preview',
                            args: [[this.id]],
                        }).then(() => {
                            // Remove loading indicator
                            $(document.body).removeClass('o_ui_blocked');
                            $.unblockUI();
                            
                            // Reload preview
                            this.settings_changed();
                        }).guardedCatch(() => {
                            $(document.body).removeClass('o_ui_blocked');
                            $.unblockUI();
                        });
                    } else {
                        this.settings_changed();
                    }
                });
            },
            
            'change .flight_import_base_pilot': function (e) {
                const pilotId = parseInt($(e.currentTarget).val(), 10);
                this._rpc({
                    model: 'base_import.import',
                    method: 'write',
                    args: [[this.id], {base_pilot_id: pilotId || false}],
                }).then(() => {
                    if (this.transformation_type !== 'none') {
                        this.settings_changed();
                    }
                });
            }
        }),
        
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.transformation_type = 'none';
        },
        
        start: function () {
            const self = this;
            return this._super().then(function () {
                // Only show flight-specific options for flight.flight model
                if (self.res_model === 'flight.flight') {
                    self._add_flight_specific_options();
                }
            });
        },
        
        _add_flight_specific_options: function() {
            // Add flight-specific options to the advanced section
            const $advancedSection = this.$('.oe_import_debug_option');
            
            // Add transformation option
            const $transformationSection = $('<div>', {
                class: 'mt-3 flight_import_section'
            }).append($('<h4>', {text: _t('Flight Data Import')}));
            
            // Add base pilot selection
            const $basePilotDiv = $('<div>', {class: 'mb-3'})
                .append($('<label>', {
                    class: 'mb-1 d-block',
                    text: _t('Base Pilot')
                }))
                .append($('<div>', {
                    class: 'text-muted small mb-1',
                    text: _t('Default pilot to use for imported flights')
                }));
            
            // We'll fetch pilots with a separate RPC call
            this._rpc({
                model: 'res.partner',
                method: 'search_read',
                args: [[['is_company', '=', false]], ['id', 'name']],
                kwargs: {limit: 100}  // Limit to 100 partners to avoid performance issues
            }).then(partners => {
                const $select = $('<select>', {
                    class: 'flight_import_base_pilot form-select'
                }).append($('<option>', {
                    value: '',
                    text: _t('Select a pilot...')
                }));
                
                // Add partners to select
                _.each(partners, partner => {
                    $select.append($('<option>', {
                        value: partner.id,
                        text: partner.name
                    }));
                });
                
                $basePilotDiv.append($select);
            });
            
            // Add transformation selection
            const $transformationDiv = $('<div>', {class: 'mb-3'})
                .append($('<label>', {
                    class: 'mb-1 d-block',
                    text: _t('Transformation')
                }))
                .append($('<div>', {
                    class: 'text-muted small mb-1',
                    text: _t('Convert from different flight log formats')
                }));
            
            const $transformationSelect = $('<select>', {
                class: 'flight_import_transformation form-select'
            })
            .append($('<option>', {
                value: 'none',
                text: _t('No Transformation')
            }))
            .append($('<option>', {
                value: 'crewlounge',
                text: _t('CrewLounge Format')
            }));
            
            $transformationDiv.append($transformationSelect);
            
            $transformationSection.append($basePilotDiv).append($transformationDiv);
            $advancedSection.append($transformationSection);
        },
        
        onpreview_success: function (event, from, to, result) {
            this._super(event, from, to, result);
            
            // If this is flight.flight model and we have transformation info
            if (this.res_model === 'flight.flight' && result.transformation_type) {
                // Set transformation type
                this.$('select.flight_import_transformation').val(result.transformation_type);
                
                // Set base pilot if available
                if (result.base_pilot_id) {
                    this.$('select.flight_import_base_pilot').val(result.base_pilot_id.id);
                }
                
                // If transformation is active, add a notice
                if (result.transformation_type !== 'none') {
                    const $notice = $('<div>', {
                        class: 'alert alert-info mt-3',
                        text: _t('Data will be transformed from ') + this.$('select.flight_import_transformation option:selected').text() + _t(' format.')
                    });
                    
                    // Remove any existing notices
                    this.$('.flight_import_transform_notice').remove();
                    this.$('.oe_import_box').append($notice.addClass('flight_import_transform_notice'));
                } else {
                    this.$('.flight_import_transform_notice').remove();
                }
            }
        },
        
        import_options: function () {
            var options = this._super();
            
            // Add flight-specific options
            if (this.res_model === 'flight.flight') {
                options.transformation_type = this.transformation_type;
                
                const basePilotId = parseInt(this.$('select.flight_import_base_pilot').val(), 10);
                if (basePilotId) {
                    options.base_pilot_id = basePilotId;
                }
            }
            
            return options;
        }
    });
    
    });