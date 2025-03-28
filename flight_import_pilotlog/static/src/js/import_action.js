odoo.define("flight_import_pilotlog.import", function (require) {
  "use strict";

  // Core Odoo Dependencies
  const DataImport = require("base_import.import").DataImport;
  const core = require("web.core");
  const qweb = core.qweb;
  const _t = core._t;
  const session = require("web.session");

  // Field Widget Dependencies
  const relationalFields = require("web.relational_fields");
  const Domain = require('web.Domain'); // Utility for handling domains

  // List of specific models this customization applies to
  const FLIGHT_MODELS = [
      "flight.flight",
      "flight.aircraft",
      "flight.aircraft.model",
      "flight.aircraft.make",
  ];

  // Extend the base DataImport widget
  DataImport.include({
      // Extend existing events or add new ones specific to this customization
      events: _.extend({}, DataImport.prototype.events, {
          // Event handler for changes in the Transformer dropdown
          "change select.flight_import_transformer": function (e) {
              const transformerId = parseInt($(e.currentTarget).val(), 10) || false;
              this.transformer_id = transformerId; // Store locally for reference

              // Update the backend record with the selected transformer ID
              this._rpc({
                  model: "base_import.import",
                  method: "write",
                  args: [[this.id], { transformer_id: transformerId }],
              })
              .then(() => {
                  // If a transformer is selected, regenerate the preview to apply it
                  if (transformerId) {
                      this._regenerateTransformationPreview();
                  } else {
                      // If transformer is removed, refresh preview with original data
                      this.settings_changed();
                  }
              })
              .guardedCatch((error) => {
                  // Handle errors during the update process
                  this.do_warn(
                      _t("Update Error"),
                      _t("Failed to update transformer")
                  );
              });
          },
          // Note: Changes to the 'base_pilot_id' field are handled by a direct
          // listener attached to the Many2one widget instance (_onPilotChanged).
      }),

      /**
       * Helper method to display a loading indicator.
       * @param {string} message The message to display while loading.
       */
      _showLoadingIndicator: function (message) {
          // Check if blockUI is available (might not be during teardown)
          if (!$.blockUI) { return; }
          // Use Odoo's standard progress dialog rendering
          $.blockUI({
              message: qweb.render("base_import.progressDialog", { task: message }),
          });
          // Add class to body to potentially style other elements during blocking
          $(document.body).addClass("o_ui_blocked");
      },

      /**
       * Helper method to hide the loading indicator.
       */
      _hideLoadingIndicator: function () {
           // Check if unblockUI is available
          if (!$.unblockUI) { return; }
          // Remove blocking class from body
          $(document.body).removeClass("o_ui_blocked");
          // Unblock the UI
          $.unblockUI();
      },

      /**
       * Helper method to trigger a regeneration of the data preview,
       * specifically when a transformation might need to be reapplied.
       * Returns the promise from the RPC call.
       */
      _regenerateTransformationPreview: function () {
          this._showLoadingIndicator(_t("Updating transformation preview"));
          return this._rpc({
              model: "base_import.import",
              method: "update_transformation_preview", // Server method to apply transformation
              args: [[this.id]], // ID of the import record
          })
          .then((result) => {
              this._hideLoadingIndicator();
              // Check server response status
              if (result && result.status === "success") {
                  // Trigger standard preview refresh using settings_changed
                  this.settings_changed();
              } else {
                  // Display transformation error from server or a generic message
                  this.do_warn(
                      _t("Transformation Error"),
                      (result && result.message) || _t("Failed to update transformation")
                  );
              }
          })
          .guardedCatch((error) => {
              // Handle RPC errors during transformation preview
              this._hideLoadingIndicator();
              this.do_warn(
                  _t("Transformation Error"),
                  _t("An error occurred during transformation update")
              );
          });
      },

      /**
       * Initialization method for the widget extension.
       * @override
       */
      init: function (parent, action) {
          this._super.apply(this, arguments); // Call parent init
          this.transformer_id = false; // Initialize local tracker for selected transformer
          this.pilotWidget = null; // Placeholder for the Many2one widget instance
          this.pilotRecordState = null; // Placeholder for the simulated record state object
      },

      /**
       * Start method, called after the widget is attached to the DOM.
       * Adds custom flight options if the model matches.
       * @override
       */
      start: async function () {
          // Use await to ensure parent start completes and handle potential async operations
          await this._super(...arguments);
          // Check if the current model is one we want to customize
          if (FLIGHT_MODELS.includes(this.res_model)) {
              // Add the custom UI elements (this method is async due to widget rendering)
              await this._addFlightImportOptions();
          }
      },

      /**
       * Adds custom UI elements (Pilot selection, Transformer selection)
       * to the import screen's advanced options section.
       * This function is async because widget rendering (appendTo) is async.
       */
      _addFlightImportOptions: async function () {
          const self = this; // Store 'this' context if needed in nested closures (though not used here)
          // Target the standard section for advanced/debug options
          const $advancedSection = this.$(".oe_import_debug_option");

          // Create a container for our custom flight import options
          const $importSection = $("<div>", {
              class: "mt-3 flight_import_section", // Add margin and custom class
          }).append($("<h4>", { text: _t("Flight Data Import") })); // Section heading

          // --- Base Pilot Selection (using Many2one widget) ---
          // Only add pilot selection for the 'flight.flight' model
          if (this.res_model === "flight.flight") {
              const uniqueId = _.uniqueId('o_field_input_'); // Generate unique ID for label/input linking
              // Use Bootstrap grid for layout
              const $basePilotDiv = $("<div>", { class: "row mb-3 align-items-center" });
              const $labelCol = $("<div>", { class: "col-md-3 col-form-label" }).append(
                  $("<label>", { class: "fw-normal", text: _t("Base Pilot"), for: uniqueId }) // Label for the field
              );
              const $widgetCol = $("<div>", { class: "col-md-9" }); // Column for the widget and description
              const $description = $("<div>", {
                  class: "text-muted small mb-1", // Help text styling
                  text: _t("Default pilot (res.partner) to use for imported flights."),
              });

              // 1. Define the structure of the fields involved in our simulated record state.
              // This tells the widget about the field it's managing.
              const fields = {
                  base_pilot_id: {
                      type: "many2one", // Field type
                      relation: "res.partner", // Target model for the relation (CRITICAL for search)
                      string: _t("Base Pilot"), // Label used internally
                      domain: [["is_company", "=", false]], // Static domain to filter partners (CRITICAL for search filtering)
                      // context: {}, // Optional: Add context if needed for searches or default_get on relation
                  }
              };

              // 2. Define fieldsInfo (simulates view-specific field information).
              // Often redundant for basic cases but required by some widget logic.
              const fieldsInfo = {
                  // Use a dummy view type key (e.g., 'import_options')
                  import_options: {
                      base_pilot_id: { // Information specific to the 'base_pilot_id' field in this "view"
                          name: 'base_pilot_id',
                          type: 'many2one',
                          relation: 'res.partner',
                          domain: [['is_company', '=', false]], // Can repeat domain here
                          string: _t("Base Pilot"),
                          // Modifiers like readonly, invisible, options etc. could be added here if needed
                          // e.g., options: { no_quick_create: true }
                      }
                  }
              };

              // 3. Create the simulated record state object (`pilotRecordState`).
              // This object provides the context, data, and field definitions the widget expects.
              // IMPORTANT: Use 'function' or method shorthand, NOT arrow functions for methods
              // that need 'this' to refer to pilotRecordState itself.
              this.pilotRecordState = {
                  // --- Core properties ---
                  id: `import_${this.id}_options`, // A unique virtual ID for this state object
                  res_id: this.id, // The ID of the actual base_import.import record
                  model: 'base_import.import', // The model name of the actual record
                  data: { base_pilot_id: false }, // Initial data state (empty M2O field)
                  fields: fields, // The field definitions we created above
                  fieldsInfo: fieldsInfo, // The view-specific field info

                  // --- Methods expected by the widget ---
                  /** Returns context for field operations. */
                  getContext: function(options = {}) {
                      // 'this' here refers to pilotRecordState
                      // Start with user context; can be expanded later if needed.
                      return { ...session.user_context };
                  },
                  /** Returns the user context. */
                  getUserContext: function() {
                      // 'this' here refers to pilotRecordState
                      return session.user_context || {};
                  },
                  /** Returns the domain for the specified field. CRITICAL for filtering searches. */
                  getDomain: function(options = {}) {
                      // 'this' here refers to pilotRecordState
                      const fieldName = options.fieldName || 'base_pilot_id'; // Default to our field
                      let domain = [];
                      // Access 'this.fields' correctly
                      if (this.fields && this.fields[fieldName] && this.fields[fieldName].domain) {
                          // Parse the domain (handles string/array) using the correct context
                          domain = Domain.prototype.stringToArray(this.fields[fieldName].domain, this.getContext());
                      }
                      return domain;
                  },

                  // --- Basic State Management properties/methods ---
                  _changes: null, // Placeholder for tracking unsaved changes (if needed)
                  isDirty: function() { return !!this._changes; }, // Basic check if changes exist
                  isVirtual: function() { return false; }, // Indicates this isn't for a *new* unsaved record

                  // --- Placeholder methods sometimes checked by widgets (for attrs evaluation etc.) ---
                  evaluateBooleanExpr: function(expr) { return false; },
                  evaluateCondition: function(condition) { return false; },
              };

              // 4. Instantiate the Many2one widget instance.
              this.pilotWidget = new relationalFields.FieldMany2One(
                  this, // Parent widget (the DataImport instance)
                  "base_pilot_id", // The name of the field this widget manages
                  this.pilotRecordState, // The simulated record state object
                  {
                      mode: "edit", // Widget should be editable
                      viewType: "import_options", // Match the key used in fieldsInfo
                      attrs: { // Attributes passed to the widget
                          can_create: false, // Disable the "Create and Edit..." option
                          can_write: false,  // Disable the "Edit" option (external link icon)
                          options: { // Options passed down to the underlying Select2/SelectWoo implementation
                              placeholder: _t("Select a pilot..."), // Placeholder text
                          },
                          id: uniqueId, // Link the widget's input to the label's 'for'
                      },
                  }
              );

              // 5. Attach an event listener directly to the widget instance.
              // This listens for the 'field_changed' event emitted by the widget itself.
              this.pilotWidget.on("field_changed", this, this._onPilotChanged);

              // 6. Append the description and render the widget into the DOM.
              $widgetCol.append($description);
              // appendTo is async, so we await its completion.
              await this.pilotWidget.appendTo($widgetCol);

              // Add the label and widget columns to the row div
              $basePilotDiv.append($labelCol, $widgetCol);
              // Add the pilot selection row to our custom section
              $importSection.append($basePilotDiv);
          } // End of pilot selection block

          // --- Transformer Selection (Standard HTML Select) ---
          const transformerUniqueId = _.uniqueId('transformer_select_');
          const $transformerDiv = $("<div>", { class: "row mb-3 align-items-center" });
          const $labelColTransformer = $("<div>", { class: "col-md-3 col-form-label" }).append(
              $("<label>", { class: "fw-normal", text: _t("Data Transformer"), for: transformerUniqueId })
          );
          const $widgetColTransformer = $("<div>", { class: "col-md-9" });
          const $descriptionTransformer = $("<div>", {
              class: "text-muted small mb-1",
              text: _t("Optional: Select a format to transform the imported data."),
          });
          // Standard HTML select element
          const $transformerSelect = $("<select>", {
              class: "flight_import_transformer form-select", // Class for styling and event binding
              name: "transformer_id", // Standard name attribute
              id: transformerUniqueId, // Link to label
          }).append(
              // Add a default "no transformation" option
              $("<option>", { value: "", text: _t("No Transformation") })
          );

          // Fetch available transformers via RPC
          this._rpc({
              model: "flight.import.pilotlog.transformer",
              method: "search_read",
              args: [
                  // Domain to find active transformers relevant to the current import model
                  [["model_id.model", "=", this.res_model], ["active", "=", true]],
                  // Fields to fetch
                  ["id", "name"],
              ],
          }).then((transformers) => {
              // Populate the select dropdown with fetched transformers
              _.each(transformers, (transformer) => {
                  $transformerSelect.append(
                      $("<option>", { value: transformer.id, text: transformer.name })
                  );
              });
              // If a transformer was previously selected (e.g., from preview data), restore it
              if (this.transformer_id) {
                  $transformerSelect.val(this.transformer_id);
              }
          }); // Note: Error handling for this RPC could be added if needed

          // Assemble the transformer section UI
          $widgetColTransformer.append($descriptionTransformer);
          $widgetColTransformer.append($transformerSelect);
          $transformerDiv.append($labelColTransformer, $widgetColTransformer);
          // Add the transformer row to our custom section
          $importSection.append($transformerDiv);

          // Finally, append our entire custom section to the standard advanced options area
          $advancedSection.append($importSection);
      }, // End of _addFlightImportOptions

      /**
       * Event handler called when the 'field_changed' event is triggered by pilotWidget.
       * @param {OdooEvent} ev The event object. ev.data contains change details.
       */
      _onPilotChanged: function (ev) {
          // --- DEBUGGING: Log the entire event data structure ---
          console.log("Pilot Changed Event Data:", ev.data);

          // --- Revised Value Extraction ---
          // Odoo widget events often put changes under ev.data.changes[fieldName]
          let newPilotValue = false; // Default to false
          if (ev.data.changes && typeof ev.data.changes.base_pilot_id !== 'undefined') {
               // If the key exists in changes (even if its value is false/null)
               newPilotValue = ev.data.changes.base_pilot_id;
               console.log("Extracted 'newPilotValue' from ev.data.changes:", newPilotValue);
          } else {
               // Fallback or log a warning if the expected structure isn't found
               console.warn("Could not find 'base_pilot_id' in ev.data.changes. Check event data structure.");
               // As a fallback, you might still check ev.data.newValue, but changes is more common
               // newPilotValue = ev.data.newValue;
          }
          // --- End Revised Value Extraction ---


          // Get just the ID, or false if no pilot is selected or value is falsy
          const pilotId = newPilotValue ? newPilotValue.id : false;

          // --- DEBUGGING: Log the final ID being sent ---
          console.log("Extracted Pilot ID for RPC:", pilotId);
          console.log("Writing to base_import.import record ID:", this.id); // Ensure this.id is correct


          // Update our local simulated state (optional but good for consistency)
          if (this.pilotRecordState) {
              this.pilotRecordState.data.base_pilot_id = newPilotValue;
          }

          // Persist the selected pilot ID to the backend base_import.import record
          this._rpc({
              model: "base_import.import",
              method: "write",
              // Ensure 'this.id' is the correct import record ID and 'pilotId' has the value
              args: [[this.id], { base_pilot_id: pilotId }],
          })
          .then(() => {
              // If a data transformation is active, the chosen pilot might affect
              // the transformation result, so regenerate the preview.
              if (this.transformer_id) {
                  this._regenerateTransformationPreview();
              }
          })
          .guardedCatch((error) => {
              // Handle errors during the update RPC call
              this.do_warn(_t("Update Error"), _t("Failed to update base pilot"));
          });
      },

      /**
       * Hook called after the data preview successfully loads or updates.
       * Used here to synchronize our custom widgets with data from the server.
       * @override
       */
      onpreview_success: function (event, from, to, result) {
          // Always call the parent implementation first
          this._super(event, from, to, result);

          // Apply updates only if it's one of our target models
          if (FLIGHT_MODELS.includes(this.res_model)) {

              // --- Synchronize Transformer Select Dropdown ---
              // Get transformer ID from the preview result (if present)
              const serverTransformerId = result.transformer_id ? result.transformer_id.id : false;
              this.transformer_id = serverTransformerId; // Update local tracker
              // Set the value of the HTML select element
              this.$("select.flight_import_transformer").val(serverTransformerId || "");

              // --- Synchronize Base Pilot Many2one Widget ---
              // Check if this model should have the pilot widget and if the widget exists
              if (this.res_model === "flight.flight" && this.pilotWidget && this.pilotRecordState) {
                  // Format the pilot data from the server result into the
                  // {id, display_name} object format the widget expects, or false if null.
                  const serverPilot = result.base_pilot_id
                      ? { id: result.base_pilot_id.id, display_name: result.base_pilot_id.display_name }
                      : false;

                  // 1. IMPORTANT: Update the 'data' part of our simulated state object first.
                  this.pilotRecordState.data.base_pilot_id = serverPilot;

                  // 2. Call the widget's 'reset' method, passing the updated state object.
                  // This tells the widget to re-render itself based on the new data
                  // in pilotRecordState, without triggering the 'field_changed' event.
                  this.pilotWidget.reset(this.pilotRecordState);
              }

              // --- Update Transformation Notice ---
              // Remove any previous notice first
              this.$(".flight_import_transform_notice").remove();
              // If the preview data indicates it was transformed, add an informational notice
              if (result.is_transformed) {
                  const transformerName = this.$("select.flight_import_transformer option:selected").text();
                  const $notice = $("<div>", {
                      class: "alert alert-info mt-3 flight_import_transform_notice", // Class for styling/selection
                      text: _t("Data preview includes transformation using: ") + transformerName,
                  });
                  // Append the notice, typically below the main preview table/box
                  this.$(".oe_import_box").append($notice);
              }
          }
      },

      /**
       * Gathers options to be sent to the final server-side import method.
       * Extends the base method to add our custom options.
       * @override
       */
      import_options: function () {
          // Get the standard options from the parent implementation
          const options = this._super();

          // --- Add Base Pilot ID ---
          // Check if the pilot widget exists and has a value
          if (this.res_model === "flight.flight" && this.pilotWidget && this.pilotWidget.value) {
               // this.pilotWidget.value holds the {id, display_name} object or false
              const basePilotId = this.pilotWidget.value ? this.pilotWidget.value.id : false;
              if (basePilotId) {
                  options.base_pilot_id = basePilotId; // Add to options if set
              } else {
                  // Explicitly remove if not set, ensuring no stale value is sent
                  delete options.base_pilot_id;
              }
          }

          // --- Add Transformer ID ---
          // Get value from the HTML select dropdown
          const transformerId = parseInt(this.$("select.flight_import_transformer").val(), 10) || false;
          if (transformerId) {
              options.transformer_id = transformerId; // Add to options if set
          } else {
              // Explicitly remove if not set
              delete options.transformer_id;
          }

          // Return the combined options object
          return options;
      },

      /**
       * Clean up resources when the widget is destroyed.
       * Crucial for manually created widgets and event listeners.
       * @override
       */
      destroy: function () {
          // If the pilot widget instance exists
          if (this.pilotWidget) {
              // 1. IMPORTANT: Remove the event listener we attached manually.
              // Failure to do this can lead to errors or memory leaks if the
              // handler tries to operate on a destroyed widget context.
              this.pilotWidget.off("field_changed", this, this._onPilotChanged);

              // 2. Call the widget's own destroy method for its internal cleanup.
              this.pilotWidget.destroy();

              // 3. Clear our reference to the widget instance.
              this.pilotWidget = null;
          }
          // Clear the reference to our simulated state object
          this.pilotRecordState = null;

          // Finally, call the parent widget's destroy method.
          this._super.apply(this, arguments);
      },

  }); // End of DataImport.include

}); // End of odoo.define