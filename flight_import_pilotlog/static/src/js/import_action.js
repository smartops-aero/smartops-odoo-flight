odoo.define('flight_import_pilotlog.import', function (require) {
    "use strict";
    
    const DataImport = require('base_import.import').DataImport;
    const core = require('web.core');
    const qweb = core.qweb;
    const _t = core._t;
    const session = require('web.session');
    
    // Extend DataImport for flight models
    DataImport.include({
        events: _.extend({}, DataImport.prototype.events, {
            'change select.flight_import_transformer': function (e) {
                const transformerId = parseInt($(e.currentTarget).val(), 10) || false;
                
                // Update the transformer_id on the server
                this._rpc({
                    model: 'base_import.import',
                    method: 'write',
                    args: [[this.id], {transformer_id: transformerId}],
                }).then(() => {
                    // If a transformer is selected, call the preview method
                    if (transformerId) {
                        this._showLoadingIndicator(_t('Preparing transformation preview'));
                        
                        // Call the transformation preview method
                        this._rpc({
                            model: 'base_import.import',
                            method: 'update_transformation_preview',
                            args: [[this.id]],
                        }).then((result) => {
                            this._hideLoadingIndicator();
                            
                            if (result && result.status === 'success') {
                                // Use the standard settings_changed to refresh the preview
                                this.settings_changed();
                            } else {
                                this.do_warn(_t("Transformation Error"), 
                                            result && result.message || _t("Failed to transform data"));
                            }
                        }).guardedCatch((error) => {
                            this._hideLoadingIndicator();
                            this.do_warn(_t("Transformation Error"), 
                                        _t("An error occurred during transformation"));
                        });
                    } else {
                        // No transformation, just update the preview normally
                        this.settings_changed();
                    }
                }).guardedCatch((error) => {
                    this.do_warn(_t("Update Error"), 
                                _t("Failed to update transformer"));
                });
            },
            
            'change .flight_import_base_pilot': function (e) {
                const pilotId = parseInt($(e.currentTarget).val(), 10) || false;
                
                this._rpc({
                    model: 'base_import.import',
                    method: 'write',
                    args: [[this.id], {base_pilot_id: pilotId}],
                }).then(() => {
                    if (this.transformer_id) {
                        // If transformation is active, regenerate the preview
                        this._regenerateTransformationPreview();
                    }
                }).guardedCatch((error) => {
                    this.do_warn(_t("Update Error"), 
                                _t("Failed to update base pilot"));
                });
            }
        }),
        
        /**
         * Helper method to show loading indicator
         */
        _showLoadingIndicator: function(message) {
            $.blockUI({message: qweb.render('base_import.progressDialog', {
                task: message
            })});
            $(document.body).addClass('o_ui_blocked');
        },
        
        /**
         * Helper method to hide loading indicator
         */
        _hideLoadingIndicator: function() {
            $(document.body).removeClass('o_ui_blocked');
            $.unblockUI();
        },
        
        /**
         * Helper method to regenerate transformation preview
         */
        _regenerateTransformationPreview: function() {
            this._showLoadingIndicator(_t('Updating transformation preview'));
            
            this._rpc({
                model: 'base_import.import',
                method: 'update_transformation_preview',
                args: [[this.id]],
            }).then((result) => {
                this._hideLoadingIndicator();
                
                if (result && result.status === 'success') {
                    this.settings_changed();
                } else {
                    this.do_warn(_t("Transformation Error"), 
                                result && result.message || _t("Failed to update transformation"));
                }
            }).guardedCatch((error) => {
                this._hideLoadingIndicator();
                this.do_warn(_t("Transformation Error"), 
                            _t("An error occurred during transformation update"));
            });
        },
        
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.transformer_id = false;
        },
        
        start: function () {
            const self = this;
            return this._super().then(function () {
                // Only show flight-specific options for flight models
                if (['flight.flight', 'flight.aircraft'].includes(self.res_model)) {
                    self._addFlightImportOptions();
                }
            });
        },
        
        _addFlightImportOptions: function() {
            const self = this;
            // Add flight-specific options to the advanced section
            const $advancedSection = this.$('.oe_import_debug_option');
            
            // Add import options section
            const $importSection = $('<div>', {
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
            
            // Fetch pilots with a separate RPC call
            this._rpc({
                model: 'res.partner',
                method: 'search_read',
                args: [[['is_company', '=', false]], ['id', 'display_name']],
                kwargs: {limit: 100}
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
                        text: partner.display_name
                    }));
                });
                
                $basePilotDiv.append($select);
            });
            
            // Add transformer selection
            const $transformerDiv = $('<div>', {class: 'mb-3'})
                .append($('<label>', {
                    class: 'mb-1 d-block',
                    text: _t('Data Transformer')
                }))
                .append($('<div>', {
                    class: 'text-muted small mb-1',
                    text: _t('Convert from different flight log formats')
                }));
            
            // Create transformer select with empty option
            const $transformerSelect = $('<select>', {
                class: 'flight_import_transformer form-select'
            }).append($('<option>', {
                value: '',
                text: _t('No Transformation')
            }));
            
            // Fetch available transformers for this model
            this._rpc({
                model: 'flight.import.pilotlog.transformer',
                method: 'search_read',
                args: [[['model_id.model', '=', this.res_model], ['active', '=', true]], ['id', 'name']],
            }).then(transformers => {
                // Add transformers to select
                _.each(transformers, transformer => {
                    $transformerSelect.append($('<option>', {
                        value: transformer.id,
                        text: transformer.name
                    }));
                });
                
                $transformerDiv.append($transformerSelect);
            });
            
            $importSection.append($basePilotDiv).append($transformerDiv);
            $advancedSection.append($importSection);
        },
        
        onpreview_success: function (event, from, to, result) {
            this._super(event, from, to, result);
            
            // If this is a flight model and we have transformer info
            if (['flight.flight', 'flight.aircraft'].includes(this.res_model)) {
                // Set transformer if available
                if (result.transformer_id) {
                    this.$('select.flight_import_transformer').val(result.transformer_id.id);
                    this.transformer_id = result.transformer_id.id;
                }
                
                // Set base pilot if available
                if (result.base_pilot_id) {
                    this.$('select.flight_import_base_pilot').val(result.base_pilot_id.id);
                }
                
                // If transformation is active, add a notice
                if (result.is_transformed) {
                    const transformerName = this.$('select.flight_import_transformer option:selected').text();
                    const $notice = $('<div>', {
                        class: 'alert alert-info mt-3',
                        text: _t('Data will be transformed using ') + transformerName
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
            const options = this._super();
            
            // Add flight-specific options
            if (['flight.flight', 'flight.aircraft'].includes(this.res_model)) {
                // Add base pilot if selected
                const basePilotId = parseInt(this.$('select.flight_import_base_pilot').val(), 10);
                if (basePilotId) {
                    options.base_pilot_id = basePilotId;
                }
            }
            
            return options;
        }
    });
});
