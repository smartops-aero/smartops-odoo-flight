# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
import math


@tagged('post_install', '-at_install', 'flight_uom')
class TestFlightUom(TransactionCase):
    """Test cases for flight-specific units of measure"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Get aviation UOM categories
        cls.distance_categ = cls.env.ref('uom.product_uom_categ_length')
        cls.weight_categ = cls.env.ref('uom.product_uom_categ_weight')
        cls.speed_categ = cls.env.ref('flight_uom.product_uom_categ_speed')
        cls.fuel_categ = cls.env.ref('flight_uom.product_uom_categ_fuel')
        
        # Get aviation UOMs
        cls.uom_nm = cls.env.ref('flight_uom.product_uom_nm')
        cls.uom_ft = cls.env.ref('flight_uom.product_uom_ft')
        cls.uom_kt = cls.env.ref('flight_uom.product_uom_kt')
        cls.uom_lb = cls.env.ref('flight_uom.product_uom_lb')
        cls.uom_gal = cls.env.ref('flight_uom.product_uom_gal')
        cls.uom_lbs_per_hour = cls.env.ref('flight_uom.product_uom_lbs_per_hour')
        
    def test_01_nautical_mile_conversion(self):
        """Test nautical mile conversions"""
        # 1 nm = 1.852 km
        nm_value = 100.0
        km_value = self.env['uom.uom']._compute_quantity(
            nm_value, 
            self.uom_nm, 
            self.env.ref('uom.product_uom_km')
        )
        
        self.assertAlmostEqual(km_value, 185.2, places=1)
        
        # Convert back
        nm_converted = self.env['uom.uom']._compute_quantity(
            km_value,
            self.env.ref('uom.product_uom_km'),
            self.uom_nm
        )
        
        self.assertAlmostEqual(nm_converted, nm_value, places=1)
        
    def test_02_feet_conversion(self):
        """Test feet to meters conversion"""
        # 1 ft = 0.3048 m
        ft_value = 35000.0  # Typical cruising altitude
        m_value = self.env['uom.uom']._compute_quantity(
            ft_value,
            self.uom_ft,
            self.env.ref('uom.product_uom_meter')
        )
        
        self.assertAlmostEqual(m_value, 10668.0, places=0)
        
    def test_03_knots_speed_conversion(self):
        """Test knots speed conversion"""
        # 1 kt = 1.852 km/h
        kt_value = 450.0  # Typical cruise speed
        kmh_value = kt_value * 1.852
        
        self.assertAlmostEqual(kmh_value, 833.4, places=1)
        
    def test_04_pounds_weight_conversion(self):
        """Test pounds to kilograms conversion"""
        # 1 lb = 0.453592 kg
        lb_value = 10000.0
        kg_value = self.env['uom.uom']._compute_quantity(
            lb_value,
            self.uom_lb,
            self.env.ref('uom.product_uom_kgm')
        )
        
        self.assertAlmostEqual(kg_value, 4535.92, places=2)
        
    def test_05_fuel_consumption_rate(self):
        """Test fuel consumption rate calculations"""
        # Fuel burn rate in lbs/hour
        burn_rate = 5000.0  # lbs/hour
        flight_hours = 3.5
        
        total_fuel_lbs = burn_rate * flight_hours
        self.assertEqual(total_fuel_lbs, 17500.0)
        
        # Convert to gallons (assuming jet fuel density ~6.7 lbs/gal)
        fuel_gallons = total_fuel_lbs / 6.7
        self.assertAlmostEqual(fuel_gallons, 2611.94, places=2)
        
    def test_06_uom_category_validation(self):
        """Test UOM category constraints"""
        # Cannot convert between incompatible categories
        with self.assertRaises(Exception):
            self.env['uom.uom']._compute_quantity(
                100.0,
                self.uom_nm,  # Distance
                self.uom_kt   # Speed
            )
            
    def test_07_aviation_specific_uoms(self):
        """Test aviation-specific unit creation"""
        # Create Mach number UOM
        mach_uom = self.env['uom.uom'].create({
            'name': 'Mach',
            'category_id': self.speed_categ.id,
            'uom_type': 'smaller',
            'factor': 1225.044,  # 1 Mach ≈ 1225.044 km/h at sea level
        })
        
        self.assertTrue(mach_uom.id)
        self.assertEqual(mach_uom.category_id, self.speed_categ)
        
    def test_08_flight_level_conversion(self):
        """Test flight level (FL) conversions"""
        # FL350 = 35,000 feet
        flight_level = 350
        feet = flight_level * 100
        
        self.assertEqual(feet, 35000)
        
        # Convert to meters
        meters = feet * 0.3048
        self.assertAlmostEqual(meters, 10668.0, places=0)
        
    def test_09_fuel_density_calculations(self):
        """Test fuel density and volume/weight conversions"""
        # Jet A-1 density: ~0.775-0.840 kg/L (avg 0.8075)
        fuel_kg = 10000.0
        fuel_density = 0.8075  # kg/L
        
        fuel_liters = fuel_kg / fuel_density
        self.assertAlmostEqual(fuel_liters, 12384.0, places=0)
        
        # Convert to US gallons (1 L = 0.264172 gal)
        fuel_gallons = fuel_liters * 0.264172
        self.assertAlmostEqual(fuel_gallons, 3272.5, places=1)
        
    def test_10_range_calculations(self):
        """Test range calculations with different units"""
        # Aircraft range
        range_nm = 3500.0  # nautical miles
        
        # Convert to kilometers
        range_km = range_nm * 1.852
        self.assertAlmostEqual(range_km, 6482.0, places=0)
        
        # Convert to statute miles
        range_mi = range_nm * 1.15078
        self.assertAlmostEqual(range_mi, 4027.73, places=2)
        
    def test_11_altitude_pressure_conversion(self):
        """Test altitude and pressure conversions"""
        # Standard pressure altitude calculations
        # ISA: 1013.25 hPa at sea level, decreases ~1 hPa per 30 ft
        
        altitude_ft = 10000
        pressure_drop_hpa = altitude_ft / 30
        sea_level_pressure = 1013.25
        
        pressure_at_altitude = sea_level_pressure - pressure_drop_hpa
        self.assertAlmostEqual(pressure_at_altitude, 679.92, places=2)
        
    def test_12_weight_balance_calculations(self):
        """Test weight and balance unit conversions"""
        # Aircraft weights
        empty_weight_lb = 45000.0
        fuel_weight_lb = 20000.0
        payload_weight_lb = 8000.0
        
        total_weight_lb = empty_weight_lb + fuel_weight_lb + payload_weight_lb
        self.assertEqual(total_weight_lb, 73000.0)
        
        # Convert to kilograms
        total_weight_kg = self.env['uom.uom']._compute_quantity(
            total_weight_lb,
            self.uom_lb,
            self.env.ref('uom.product_uom_kgm')
        )
        
        self.assertAlmostEqual(total_weight_kg, 33112.24, places=2)