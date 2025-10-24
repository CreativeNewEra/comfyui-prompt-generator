"""
Tests for preset validation and structure
"""

import pytest


class TestPresetStructure:
    """Test that presets have valid structure"""

    def test_preset_categories_exist(self, presets):
        """Verify all expected preset categories exist"""
        expected_categories = ['styles', 'artists', 'composition', 'lighting']

        for category in expected_categories:
            assert category in presets, f"Category '{category}' not found in presets"

    def test_preset_categories_are_dicts(self, presets):
        """Verify all preset categories are dictionaries"""
        for category, items in presets.items():
            assert isinstance(items, dict), f"Category '{category}' is not a dictionary"

    def test_none_option_exists_in_all_categories(self, presets):
        """Verify 'None' option exists in each category"""
        for category, items in presets.items():
            assert 'None' in items, f"'None' option missing in '{category}' category"

    def test_none_option_is_empty_string(self, presets):
        """Verify 'None' option has empty string value"""
        for category, items in presets.items():
            assert items['None'] == '', f"'None' option in '{category}' should be empty string"

    def test_presets_have_string_values(self, presets):
        """Verify all preset values are strings"""
        for category, items in presets.items():
            for preset_name, preset_value in items.items():
                assert isinstance(preset_value, str), \
                    f"Preset '{preset_name}' in '{category}' has non-string value"

    def test_presets_have_non_empty_keys(self, presets):
        """Verify all preset keys are non-empty strings"""
        for category, items in presets.items():
            for preset_name in items.keys():
                assert isinstance(preset_name, str), \
                    f"Preset key in '{category}' is not a string"
                assert preset_name.strip() != '', \
                    f"Empty preset key found in '{category}'"


class TestPresetCategories:
    """Test individual preset categories"""

    def test_styles_category_has_multiple_options(self, presets):
        """Verify styles category has multiple preset options"""
        assert len(presets['styles']) > 1, "Styles should have more than just 'None'"

    def test_artists_category_has_multiple_options(self, presets):
        """Verify artists category has multiple preset options"""
        assert len(presets['artists']) > 1, "Artists should have more than just 'None'"

    def test_composition_category_has_multiple_options(self, presets):
        """Verify composition category has multiple preset options"""
        assert len(presets['composition']) > 1, "Composition should have more than just 'None'"

    def test_lighting_category_has_multiple_options(self, presets):
        """Verify lighting category has multiple preset options"""
        assert len(presets['lighting']) > 1, "Lighting should have more than just 'None'"

    def test_total_preset_count(self, presets):
        """Verify we have a reasonable number of total presets"""
        total_presets = sum(len(items) for items in presets.values())
        assert total_presets >= 50, f"Expected at least 50 total presets, got {total_presets}"


class TestSpecificPresets:
    """Test for specific preset values"""

    def test_cinematic_style_exists(self, presets):
        """Verify Cinematic style preset exists"""
        assert 'Cinematic' in presets['styles'], "Cinematic style should exist"

    def test_photorealistic_style_exists(self, presets):
        """Verify Photorealistic style preset exists"""
        assert 'Photorealistic' in presets['styles'], "Photorealistic style should exist"

    def test_portrait_composition_exists(self, presets):
        """Verify Portrait composition preset exists"""
        assert 'Portrait' in presets['composition'], "Portrait composition should exist"

    def test_golden_hour_lighting_exists(self, presets):
        """Verify Golden Hour lighting preset exists"""
        assert 'Golden Hour' in presets['lighting'], "Golden Hour lighting should exist"

    def test_presets_are_not_none_values(self, presets):
        """Verify non-None presets have actual content"""
        for category, items in presets.items():
            for preset_name, preset_value in items.items():
                if preset_name != 'None':
                    assert preset_value != '', \
                        f"Preset '{preset_name}' in '{category}' should not be empty"
