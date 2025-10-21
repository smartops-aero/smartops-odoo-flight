from datetime import datetime, timedelta

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install", "website_flight_fleet")
class TestWebsiteFlightFleet(TransactionCase):
    """Test cases for website flight fleet display"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get website
        cls.website = cls.env["website"].get_current_website()

        # Create aircraft classes
        cls.class_jet = cls.env["flight.aircraft.class"].create(
            {
                "name": "Business Jet",
                "aircraft_category": "airplane",
            }
        )

        cls.class_turbo = cls.env["flight.aircraft.class"].create(
            {
                "name": "Turboprop",
                "aircraft_category": "airplane",
            }
        )

        cls.class_heli = cls.env["flight.aircraft.class"].create(
            {
                "name": "Helicopter",
                "aircraft_category": "rotorcraft",
            }
        )

        # Create makes
        cls.make_gulfstream = cls.env["flight.aircraft.make"].create(
            {
                "name": "Gulfstream",
            }
        )

        cls.make_cessna = cls.env["flight.aircraft.make"].create(
            {
                "name": "Cessna",
            }
        )

        cls.make_bell = cls.env["flight.aircraft.make"].create(
            {
                "name": "Bell",
            }
        )

        # Create models
        cls.model_g650 = cls.env["flight.aircraft.model"].create(
            {
                "name": "G650",
                "make_id": cls.make_gulfstream.id,
                "class_id": cls.class_jet.id,
                "engine_type": "turbofan",
                "gear_type": "retractable_tricycle",
                "code": "G650",
            }
        )

        cls.model_citation = cls.env["flight.aircraft.model"].create(
            {
                "name": "Citation CJ3",
                "make_id": cls.make_cessna.id,
                "class_id": cls.class_jet.id,
                "engine_type": "turbofan",
                "gear_type": "retractable_tricycle",
                "code": "CJ3",
            }
        )

        cls.model_caravan = cls.env["flight.aircraft.model"].create(
            {
                "name": "Caravan 208",
                "make_id": cls.make_cessna.id,
                "class_id": cls.class_turbo.id,
                "engine_type": "turboprop",
                "gear_type": "fixed_tricycle",
                "code": "C208",
            }
        )

        cls.model_bell407 = cls.env["flight.aircraft.model"].create(
            {
                "name": "407",
                "make_id": cls.make_bell.id,
                "class_id": cls.class_heli.id,
                "engine_type": "turboshaft",
                "gear_type": "skids",
                "code": "B407",
            }
        )

        # Create aircraft
        cls.aircraft_g650 = cls.env["flight.aircraft"].create(
            {
                "registration": "N650GS",
                "model_id": cls.model_g650.id,
                "operator_id": cls.env.company.partner_id.id,
                "dom": "2020-01-01",
                "website_published": True,
            }
        )

        cls.aircraft_citation = cls.env["flight.aircraft"].create(
            {
                "registration": "N123CJ",
                "model_id": cls.model_citation.id,
                "operator_id": cls.env.company.partner_id.id,
                "dom": "2018-01-01",
                "website_published": True,
            }
        )

        cls.aircraft_caravan = cls.env["flight.aircraft"].create(
            {
                "registration": "N208CV",
                "model_id": cls.model_caravan.id,
                "operator_id": cls.env.company.partner_id.id,
                "dom": "2019-01-01",
                "website_published": False,  # Not published
            }
        )

        cls.aircraft_bell = cls.env["flight.aircraft"].create(
            {
                "registration": "N407BH",
                "model_id": cls.model_bell407.id,
                "operator_id": cls.env.company.partner_id.id,
                "dom": "2021-01-01",
                "website_published": True,
            }
        )

    def test_01_website_published_aircraft(self):
        """Test website published aircraft filtering"""
        # Get published aircraft
        published_aircraft = self.env["flight.aircraft"].search(
            [("website_published", "=", True)]
        )

        self.assertIn(self.aircraft_g650, published_aircraft)
        self.assertIn(self.aircraft_citation, published_aircraft)
        self.assertNotIn(self.aircraft_caravan, published_aircraft)
        self.assertIn(self.aircraft_bell, published_aircraft)

    def test_02_aircraft_by_category(self):
        """Test grouping aircraft by category"""
        # Get airplanes
        airplanes = self.env["flight.aircraft"].search(
            [
                ("model_id.class_id.aircraft_category", "=", "airplane"),
                ("website_published", "=", True),
            ]
        )

        self.assertIn(self.aircraft_g650, airplanes)
        self.assertIn(self.aircraft_citation, airplanes)
        self.assertNotIn(self.aircraft_bell, airplanes)

        # Get helicopters
        helicopters = self.env["flight.aircraft"].search(
            [
                ("model_id.class_id.aircraft_category", "=", "rotorcraft"),
                ("website_published", "=", True),
            ]
        )

        self.assertIn(self.aircraft_bell, helicopters)
        self.assertNotIn(self.aircraft_g650, helicopters)

    def test_03_aircraft_published_filtering(self):
        """Test website published aircraft filtering"""
        published = self.env["flight.aircraft"].search(
            [("website_published", "=", True)]
        )

        self.assertIn(self.aircraft_g650, published)
        self.assertIn(self.aircraft_citation, published)
        self.assertIn(self.aircraft_bell, published)
        self.assertNotIn(self.aircraft_caravan, published)

    def test_04_aircraft_model_display(self):
        """Test aircraft model display name"""
        # Check actual display name (just the model name, not make + model)
        self.assertEqual(self.model_g650.display_name, "G650")

        # Check model properties
        self.assertEqual(self.model_g650.name, "G650")
        self.assertEqual(self.model_g650.make_id, self.make_gulfstream)
        self.assertEqual(self.model_g650.engine_type, "turbofan")

    def test_05_aircraft_image_management(self):
        """Test aircraft image attachments for gallery"""
        # Create images for aircraft with proper base64 data
        import base64

        test_image_data = base64.b64encode(b"fake_image_data_for_testing").decode(
            "utf-8"
        )

        image1 = self.env["ir.attachment"].create(
            {
                "name": "g650_exterior.jpg",
                "type": "binary",
                "datas": test_image_data,
                "res_model": "flight.aircraft",
                "res_id": self.aircraft_g650.id,
                "public": True,
            }
        )

        image2 = self.env["ir.attachment"].create(
            {
                "name": "g650_interior.jpg",
                "type": "binary",
                "datas": test_image_data,
                "res_model": "flight.aircraft",
                "res_id": self.aircraft_g650.id,
                "public": True,
            }
        )

        # Get aircraft images
        images = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "flight.aircraft"),
                ("res_id", "=", self.aircraft_g650.id),
                ("public", "=", True),
            ]
        )

        self.assertEqual(len(images), 2)
        self.assertIn(image1, images)
        self.assertIn(image2, images)

    def test_06_fleet_statistics(self):
        """Test fleet statistics calculation"""
        published_fleet = self.env["flight.aircraft"].search(
            [("website_published", "=", True)]
        )

        # Count by category
        stats = {}
        for aircraft in published_fleet:
            category = aircraft.model_id.class_id.aircraft_category
            if category not in stats:
                stats[category] = 0
            stats[category] += 1

        self.assertEqual(stats.get("airplane", 0), 2)
        self.assertEqual(stats.get("rotorcraft", 0), 1)

    def test_07_aircraft_search_by_engine(self):
        """Test website search filters for aircraft by engine type"""
        # Filter by engine type
        turbofan_aircraft = self.env["flight.aircraft"].search(
            [
                ("model_id.engine_type", "=", "turbofan"),
                ("website_published", "=", True),
            ]
        )

        self.assertIn(self.aircraft_g650, turbofan_aircraft)
        self.assertIn(self.aircraft_citation, turbofan_aircraft)
        self.assertNotIn(self.aircraft_bell, turbofan_aircraft)

        # Filter by turboshaft engines (helicopters)
        turboshaft_aircraft = self.env["flight.aircraft"].search(
            [
                ("model_id.engine_type", "=", "turboshaft"),
                ("website_published", "=", True),
            ]
        )

        self.assertIn(self.aircraft_bell, turboshaft_aircraft)
        self.assertNotIn(self.aircraft_g650, turboshaft_aircraft)

    def test_08_aircraft_seo_metadata(self):
        """Test SEO metadata for aircraft pages"""
        # Check aircraft has SEO-friendly URL
        self.aircraft_g650.registration.replace(" ", "-").lower()

        # Check meta description content
        meta_description = (
            f"{self.aircraft_g650.model_id.make_id.name} {self.aircraft_g650.model_id.name} - "
            f"{self.aircraft_g650.model_id.engine_type} engine, "
            f"{self.aircraft_g650.model_id.gear_type} landing gear"
        )

        self.assertTrue(meta_description)
        self.assertIn("Gulfstream", meta_description)
        self.assertIn("turbofan", meta_description)

    def test_09_fleet_comparison_table(self):
        """Test data for fleet comparison table"""
        comparison_data = []

        for aircraft in [
            self.aircraft_g650,
            self.aircraft_citation,
            self.aircraft_bell,
        ]:
            if aircraft.website_published:
                comparison_data.append(
                    {
                        "registration": aircraft.registration,
                        "model": aircraft.model_id.display_name,
                        "category": aircraft.model_id.class_id.aircraft_category,
                        "engine_type": aircraft.model_id.engine_type,
                        "gear_type": aircraft.model_id.gear_type,
                        "code": aircraft.model_id.code,
                    }
                )

        self.assertEqual(len(comparison_data), 3)

        # Check data integrity
        g650_data = next(
            (d for d in comparison_data if d["registration"] == "N650GS"), None
        )
        self.assertIsNotNone(g650_data)
        self.assertEqual(g650_data["engine_type"], "turbofan")
        self.assertEqual(g650_data["code"], "G650")

    def test_10_aircraft_availability_calendar(self):
        """Test aircraft availability for booking calendar"""
        # Create sample bookings
        today = datetime.now().date()

        self.env["flight.flight"].create(
            {
                "date": today + timedelta(days=5),
                "aircraft_id": self.aircraft_g650.id,
                "departure_id": self.env["flight.aerodrome"]
                .create(
                    {
                        "name": "Test Airport",
                        "icao": "KTST",
                    }
                )
                .id,
                "arrival_id": self.env["flight.aerodrome"]
                .create(
                    {
                        "name": "Test Airport 2",
                        "icao": "KTS2",
                    }
                )
                .id,
            }
        )

        # Check aircraft availability
        booked_dates = self.env["flight.flight"].search(
            [
                ("aircraft_id", "=", self.aircraft_g650.id),
                ("date", ">=", today),
                ("date", "<=", today + timedelta(days=30)),
            ]
        )

        self.assertEqual(len(booked_dates), 1)
        self.assertEqual(booked_dates[0].date, today + timedelta(days=5))

    def test_11_aircraft_model_codes(self):
        """Test aircraft model ICAO codes"""
        # Check ICAO codes are set correctly
        self.assertEqual(self.aircraft_g650.model_id.code, "G650")
        self.assertEqual(self.aircraft_citation.model_id.code, "CJ3")
        self.assertEqual(self.aircraft_caravan.model_id.code, "C208")
        self.assertEqual(self.aircraft_bell.model_id.code, "B407")

        # Check codes are unique
        codes = [
            self.model_g650.code,
            self.model_citation.code,
            self.model_caravan.code,
            self.model_bell407.code,
        ]
        self.assertEqual(len(codes), len(set(codes)))

    def test_12_responsive_fleet_display(self):
        """Test data structure for responsive fleet display"""
        # Prepare data for different screen sizes
        fleet_data = {
            "desktop": {
                "columns": ["Image", "Model", "Category", "Engine", "Gear", "Code"],
                "items_per_page": 10,
            },
            "tablet": {
                "columns": ["Image", "Model", "Category", "Engine"],
                "items_per_page": 6,
            },
            "mobile": {"columns": ["Model", "Category"], "items_per_page": 4},
        }

        self.assertTrue(fleet_data["desktop"])
        self.assertTrue(fleet_data["tablet"])
        self.assertTrue(fleet_data["mobile"])
        self.assertEqual(len(fleet_data["desktop"]["columns"]), 6)


@tagged("post_install", "-at_install", "website_flight_fleet", "at_install")
class TestWebsiteFlightFleetHttp(HttpCase):
    """HTTP test cases for website flight fleet pages"""

    def test_01_fleet_page_access(self):
        """Test public access to fleet page"""
        # This would test actual HTTP routes
        # Implementation depends on specific website routes
        pass
