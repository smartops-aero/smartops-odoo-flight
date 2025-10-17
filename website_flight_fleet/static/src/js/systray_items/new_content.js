/** @odoo-module **/

import {
  NewContentModal,
  MODULE_STATUS,
} from "@website/systray_items/new_content";
import { patch } from "@web/core/utils/patch";
import { xml } from "@odoo/owl";

patch(NewContentModal.prototype, {
  setup() {
    super.setup();

    // Add aircraft option to new content menu
    const newAircraftElement = {
      moduleXmlId: "base.module_website_flight_fleet",
      title: "Aircraft",
      icon: xml`<i class="fa fa-plane"/>`,
      createNewContent: () =>
        this.onAddContent("website_flight_fleet.aircraft_new_action", true),
      status: MODULE_STATUS.INSTALLED,
      model: "flight.aircraft",
    };

    // Insert aircraft option into content elements at the appropriate position
    this.state.newContentElements.push(newAircraftElement);
  },
});
