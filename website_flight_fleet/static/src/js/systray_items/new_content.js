/** @odoo-module **/

import {
  MODULE_STATUS,
  NewContentModal,
} from "@website/systray_items/new_content";
import { patch } from "web.utils";
import { xml } from "@odoo/owl";

patch(NewContentModal.prototype, "website_flight_fleet_new_content", {
  setup() {
    this._super();

    // Add aircraft option to new content menu
    const newAircraftElement = {
      moduleXmlId: "base.module_website_flight_fleet",
      name: "Aircraft",
      // Added title property
      title: "Aircraft",
      // Optional but recommended
      description: "Add a new aircraft to your fleet",
      model: "flight.aircraft",
      icon: xml`<i class="fa fa-plane"/>`,
      sequence: 35,
      createNewContent: () =>
        this.onAddContent("website_flight_fleet.aircraft_new_action", true),
      status: MODULE_STATUS.INSTALLED,
    };

    // Insert aircraft option into content elements
    const index = this.state.newContentElements.findIndex(
      (el) => el.sequence > newAircraftElement.sequence
    );
    if (index >= 0) {
      this.state.newContentElements.splice(index, 0, newAircraftElement);
    } else {
      this.state.newContentElements.push(newAircraftElement);
    }
  },
});
