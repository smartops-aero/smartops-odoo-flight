odoo.define('flight_import.import', function (require) {
    "use strict";
    
    var DataImport = require('base_import.import').DataImport;
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;
    var session = require('web.session');
    
    // Extend DataImport for flight.flight model
    DataImport.include({
        events: _.extend({}, DataImport.prototype.events, {
            'change select.flight_import_transformation': function (e) {
                this.transformation_type = $(e.currentTarget).val();
                console.log("Transformation type changed to:", this.transformation_type);
                
                // First, update the transformation_type on the server
                this._rpc({
                    model: 'base_import.import',
                    method: 'write',
                    args: [[this.id], {transformation_type: this.transformation_type}],
                }).then(() => {
                    console.log("Transformation type updated on server");
                    
                    // Then, if a transformation is selected, call the preview method
                    if (this.transformation_type !== 'none') {
                        console.log("Showing loading indicator for transformation");
                        // Show loading indicator
                        $.blockUI({message: qweb.render('base_import.progressDialog', {
                            task: _t('Preparing transformation preview')
                        })});
                        $(document.body).addClass('o_ui_blocked');
                        
                        // Call the transformation preview method
                        this._rpc({
                            model: 'base_import.import',
                            method: 'update_transformation_preview',
                            args: [[this.id]],
                        }).then((result) => {
                            console.log("Transformation preview update result:", result);
                            
                            // Always ensure we unblock the UI in case of success
                            $(document.body).removeClass('o_ui_blocked');
                            $.unblockUI();
                            
                            if (result && result.status === 'success') {
                                console.log("Transformation successful, triggering settings_changed");
                                // Use the standard settings_changed to refresh the preview
                                this.settings_changed();
                            } else {
                                console.error("Transformation error:", result);
                                this.do_warn(_t("Transformation Error"), 
                                            result && result.message || _t("Failed to transform data"));
                            }
                        }).guardedCatch((error) => {
                            console.error("Transformation error:", error);
                            $(document.body).removeClass('o_ui_blocked');
                            $.unblockUI();
                            this.do_warn(_t("Transformation Error"), 
                                        _t("An error occurred during transformation"));
                        });
                    } else {
                        console.log("No transformation, updating preview normally");
                        // No transformation, just update the preview normally
                        this.settings_changed();
                    }
                }).guardedCatch((error) => {
                    console.error("Error updating transformation type:", error);
                    this.do_warn(_t("Update Error"), 
                                _t("Failed to update transformation type"));
                });
            },
            
            'change .flight_import_base_pilot': function (e) {
                const pilotId = parseInt($(e.currentTarget).val(), 10);
                console.log("Base pilot changed to:", pilotId);
                
                this._rpc({
                    model: 'base_import.import',
                    method: 'write',
                    args: [[this.id], {base_pilot_id: pilotId || false}],
                }).then(() => {
                    console.log("Base pilot updated on server");
                    
                    if (this.transformation_type !== 'none') {
                        console.log("Regenerating transformation preview");
                        // If transformation is active, regenerate the preview
                        this._regenerateTransformationPreview();
                    }
                }).guardedCatch((error) => {
                    console.error("Error updating base pilot:", error);
                    this.do_warn(_t("Update Error"), 
                                _t("Failed to update base pilot"));
                });
            }
        }),
        
        /**
         * Helper method to regenerate transformation preview
         */
        _regenerateTransformationPreview: function() {
            console.log("Regenerating transformation preview");
            
            $.blockUI({message: qweb.render('base_import.progressDialog', {
                task: _t('Updating transformation preview')
            })});
            $(document.body).addClass('o_ui_blocked');
            
            this._rpc({
                model: 'base_import.import',
                method: 'update_transformation_preview',
                args: [[this.id]],
            }).then((result) => {
                console.log("Regenerate transformation result:", result);
                
                // Always ensure we unblock the UI
                $(document.body).removeClass('o_ui_blocked');
                $.unblockUI();
                
                if (result && result.status === 'success') {
                    console.log("Regeneration successful, triggering settings_changed");
                    this.settings_changed();
                } else {
                    console.error("Regeneration error:", result);
                    this.do_warn(_t("Transformation Error"), 
                                result && result.message || _t("Failed to update transformation"));
                }
            }).guardedCatch((error) => {
                console.error("Regeneration error:", error);
                $(document.body).removeClass('o_ui_blocked');
                $.unblockUI();
                this.do_warn(_t("Transformation Error"), 
                            _t("An error occurred during transformation update"));
            });
        },
        
        /**
         * Directly refresh the preview without changing the loading message
         * This avoids the double loading indicator issue
         */
        _refreshPreview: function() {
            var self = this;
            
            // Prepare the UI without changing the loading indicator
            this.$buttons.filter('.o_import_import, .o_import_validate').addClass('d-none');
            this.$form.addClass('oe_import_with_file');
            this.$form.removeClass('oe_import_preview_error oe_import_error');
            this.$form.toggleClass(
                'oe_import_noheaders',
                !this.$('input.oe_import_has_header').prop('checked'));
            
            this.$('input.oe_import_file').val('');
            this.$('.oe_import_options_cell,.oe_import_options_header').addClass('d-none');
            
            this._cleanComments();
            
            // Call parse_preview without changing the loading indicator
            this._rpc({
                model: 'base_import.import',
                method: 'parse_preview',
                args: [this.id, this.import_options()],
                kwargs: {context: session.user_context},
            }).then(function (result) {
                var signal = result.error ? 'preview_failed' : 'preview_succeeded';
                self[signal](result);
                $(document.body).removeClass('o_ui_blocked');
                $.unblockUI();
            });
        },
        
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
        
        onpreviewing: function () {
            // If transformation is in progress, skip showing the default loading indicator
            if (this.is_transformation_in_progress) {
                return;
            }
            
            // Original implementation
            var self = this;
            this.$buttons.filter('.o_import_import, .o_import_validate').addClass('d-none');
            this.$form.addClass('oe_import_with_file');
            this.$form.removeClass('oe_import_preview_error oe_import_error');
            this.$form.toggleClass(
                'oe_import_noheaders',
                !this.$('input.oe_import_has_header').prop('checked'));

            // Clear the input value to allow onchange to be triggered
            // if the file is the same (for all browsers)
            this.$('input.oe_import_file').val('');
            this.$('.oe_import_options_cell,.oe_import_options_header').addClass('d-none');

            this._cleanComments();

            // Block UI during loading file.
            $.blockUI({message: qweb.render('base_import.progressDialog', {
                task: _t('Loading file...')
            })});
            $(document.body).addClass('o_ui_blocked');

            this._rpc({
                model: 'base_import.import',
                method: 'parse_preview',
                args: [this.id, this.import_options()],
                kwargs: {context: session.user_context},
            }).then(function (result) {
                var signal = result.error ? 'preview_failed' : 'preview_succeeded';
                self[signal](result);
                $(document.body).removeClass('o_ui_blocked');
                $.unblockUI();
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
            
            // Fetch pilots with a separate RPC call
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
                this.transformation_type = result.transformation_type;
                
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