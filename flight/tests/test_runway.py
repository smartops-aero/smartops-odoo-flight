from odoo.exceptions import ValidationError
from odoo.tests import tagged
from psycopg2 import IntegrityError

from .common import FlightCommon


@tagged("post_install", "-at_install", "flight_runway")
class TestAerodromeRunway(FlightCommon):
    """Test cases for flight.aerodrome.runway model"""

    def test_01_runway_creation(self):
        """Test basic runway creation"""
        runway = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "04L",
                "length": 3460,
                "width": 60,
            }
        )

        self.assertTrue(runway.id)
        self.assertEqual(runway.code, "04L")
        self.assertEqual(runway.aerodrome_id, self.aerodrome_jfk)
        self.assertEqual(runway.length, 3460)
        self.assertEqual(runway.width, 60)

    def test_02_runway_display_name_computation(self):
        """Test runway name is computed from aerodrome ICAO and code"""
        runway = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "13R",
            }
        )

        # Name should be "ICAO CODE"
        expected_name = f"{self.aerodrome_jfk.icao} 13R"
        self.assertEqual(runway.name, expected_name)

    def test_03_runway_display_name_without_aerodrome(self):
        """Test runway name fallback when aerodrome not set"""
        # This shouldn't happen in practice due to required=True, but tests the compute logic
        runway = self.env["flight.aerodrome.runway"].new({"code": "22L"})
        runway._compute_name()

        self.assertEqual(runway.name, "22L")

    def test_04_runway_display_name_without_code(self):
        """Test runway name fallback when code not set"""
        runway = self.env["flight.aerodrome.runway"].new(
            {"aerodrome_id": self.aerodrome_jfk.id}
        )
        runway._compute_name()

        self.assertEqual(runway.name, "New Runway")

    def test_05_runway_code_validation_valid_codes(self):
        """Test valid runway codes are accepted"""
        valid_codes = [
            "01",
            "09",
            "18",
            "27",
            "36",  # Standard runways
            "04L",
            "04R",
            "04C",  # With designators
            "22L",
            "22R",
            "22C",
            "88",  # Special case for all runways
        ]

        for code in valid_codes:
            runway = self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": code,
                }
            )
            self.assertEqual(runway.code, code)

    def test_06_runway_code_validation_invalid_number_too_low(self):
        """Test runway code validation - number too low"""
        with self.assertRaises(ValidationError) as cm:
            self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": "00",  # Invalid: must be 01-36
                }
            )
        self.assertIn("must be between 01 and 36", str(cm.exception))

    def test_07_runway_code_validation_invalid_number_too_high(self):
        """Test runway code validation - number too high"""
        with self.assertRaises(ValidationError) as cm:
            self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": "37",  # Invalid: must be 01-36
                }
            )
        self.assertIn("must be between 01 and 36", str(cm.exception))

    def test_08_runway_code_validation_invalid_length(self):
        """Test runway code validation - too short"""
        # Too short - only 1 character
        with self.assertRaises(ValidationError) as cm:
            self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": "1",  # Invalid: too short
                }
            )
        self.assertIn("must be 2-3 characters", str(cm.exception))

        # Note: Too long is handled by field size=3 at database level (auto-truncation)

    def test_09_runway_code_validation_invalid_designator(self):
        """Test runway code validation - invalid third character"""
        with self.assertRaises(ValidationError) as cm:
            self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": "22X",  # Invalid: third character must be L/R/C
                }
            )
        self.assertIn("must be L, R, or C", str(cm.exception))

    def test_10_runway_code_validation_non_numeric(self):
        """Test runway code validation - non-numeric first two characters"""
        with self.assertRaises(ValidationError) as cm:
            self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": "AB",  # Invalid: must be numeric
                }
            )
        self.assertIn("must be digits", str(cm.exception))

    def test_11_runway_special_code_88(self):
        """Test special runway code 88 (all runways) is allowed"""
        runway = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "88",
            }
        )

        self.assertTrue(runway.id)
        self.assertEqual(runway.code, "88")

    def test_12_runway_unique_per_aerodrome(self):
        """Test runway code must be unique per aerodrome"""
        # Create first runway
        self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "09L",
            }
        )

        # Try to create duplicate - should fail
        with self.assertRaises(IntegrityError):
            self.env["flight.aerodrome.runway"].create(
                {
                    "aerodrome_id": self.aerodrome_jfk.id,
                    "code": "09L",  # Duplicate code for same aerodrome
                }
            )

    def test_13_runway_same_code_different_aerodromes(self):
        """Test same runway code allowed at different aerodromes"""
        # Create runway at JFK
        runway_jfk = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "13R",
            }
        )

        # Create runway with same code at LAX - should succeed
        runway_lax = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_lax.id,
                "code": "13R",
            }
        )

        self.assertTrue(runway_jfk.id)
        self.assertTrue(runway_lax.id)
        self.assertEqual(runway_jfk.code, runway_lax.code)
        self.assertNotEqual(runway_jfk.aerodrome_id, runway_lax.aerodrome_id)

    def test_14_runway_relationship_with_aerodrome(self):
        """Test runway One2many relationship with aerodrome"""
        # Create multiple runways for same aerodrome
        runway1 = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "04L",
                "length": 3460,
            }
        )

        runway2 = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "04R",
                "length": 3000,
            }
        )

        runway3 = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "13L",
                "length": 3000,
            }
        )

        # Check aerodrome has all runways
        self.assertEqual(len(self.aerodrome_jfk.runway_ids), 3)
        self.assertIn(runway1, self.aerodrome_jfk.runway_ids)
        self.assertIn(runway2, self.aerodrome_jfk.runway_ids)
        self.assertIn(runway3, self.aerodrome_jfk.runway_ids)

    def test_15_runway_cascade_delete_with_aerodrome(self):
        """Test runways are deleted when aerodrome is deleted (ondelete='cascade')"""
        # Create aerodrome with runways
        aerodrome = self.env["flight.aerodrome"].create(
            {
                "name": "Test Airport for Delete",
                "icao": "KTDL",
                "city": "Test City",
            }
        )

        runway1 = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": aerodrome.id,
                "code": "09",
            }
        )

        runway2 = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": aerodrome.id,
                "code": "27",
            }
        )

        runway1_id = runway1.id
        runway2_id = runway2.id

        # Delete aerodrome
        aerodrome.unlink()

        # Runways should be deleted (cascade)
        self.assertFalse(self.env["flight.aerodrome.runway"].browse(runway1_id).exists())
        self.assertFalse(self.env["flight.aerodrome.runway"].browse(runway2_id).exists())

    def test_16_runway_length_width_with_uom(self):
        """Test runway length and width with different UoMs"""
        meter_uom = self.env.ref("uom.product_uom_meter")
        foot_uom = self.env.ref("uom.product_uom_foot")

        # Create runway with meters
        runway_m = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "31L",
                "length": 3460,
                "length_uom_id": meter_uom.id,
                "width": 60,
                "width_uom_id": meter_uom.id,
            }
        )

        self.assertEqual(runway_m.length_uom_id, meter_uom)
        self.assertEqual(runway_m.width_uom_id, meter_uom)

        # Create runway with feet
        runway_ft = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_lax.id,
                "code": "25R",
                "length": 11350,
                "length_uom_id": foot_uom.id,
                "width": 200,
                "width_uom_id": foot_uom.id,
            }
        )

        self.assertEqual(runway_ft.length_uom_id, foot_uom)
        self.assertEqual(runway_ft.width_uom_id, foot_uom)

    def test_17_runway_ordering(self):
        """Test runways are ordered by code"""
        # Create runways out of order
        self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "31R",
            }
        )

        self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "13L",
            }
        )

        self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "22L",
            }
        )

        # Get runways - should be ordered by code
        runways = self.env["flight.aerodrome.runway"].search(
            [("aerodrome_id", "=", self.aerodrome_jfk.id)]
        )

        # Check ordering (alphabetically by code)
        codes = runways.mapped("code")
        self.assertEqual(codes, sorted(codes))

    def test_18_runway_copy(self):
        """Test runway duplication"""
        runway = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "04L",
                "length": 3460,
                "width": 60,
            }
        )

        # Copy to different aerodrome with different code
        runway_copy = runway.copy(
            {
                "aerodrome_id": self.aerodrome_lax.id,
                "code": "06L",
            }
        )

        self.assertNotEqual(runway_copy.id, runway.id)
        self.assertEqual(runway_copy.code, "06L")
        self.assertEqual(runway_copy.aerodrome_id, self.aerodrome_lax)
        self.assertEqual(runway_copy.length, runway.length)
        self.assertEqual(runway_copy.width, runway.width)

    def test_19_runway_search_by_aerodrome(self):
        """Test searching runways by aerodrome"""
        # Create runways at different aerodromes
        self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "13R",
            }
        )

        self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_lax.id,
                "code": "25L",
            }
        )

        # Search for JFK runways
        jfk_runways = self.env["flight.aerodrome.runway"].search(
            [("aerodrome_id", "=", self.aerodrome_jfk.id)]
        )

        # Should only find JFK runway
        self.assertTrue(jfk_runways)
        self.assertTrue(all(r.aerodrome_id == self.aerodrome_jfk for r in jfk_runways))

    def test_20_runway_name_updates_when_aerodrome_changes(self):
        """Test runway name is recomputed when aerodrome ICAO changes"""
        runway = self.env["flight.aerodrome.runway"].create(
            {
                "aerodrome_id": self.aerodrome_jfk.id,
                "code": "22R",
            }
        )

        original_name = runway.name
        self.assertIn(self.aerodrome_jfk.icao, original_name)

        # Change aerodrome ICAO
        new_icao = "KNEW"
        self.aerodrome_jfk.write({"icao": new_icao})

        # Name should update
        self.assertIn(new_icao, runway.name)
        self.assertNotEqual(runway.name, original_name)
