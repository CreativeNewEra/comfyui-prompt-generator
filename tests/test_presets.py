"""
Tests for preset validation and structure
"""

import pytest


class TestPresetStructure:
    """Test that presets have valid structure"""

    def test_preset_categories_exist(self, presets, hierarchical_enabled):
        """Verify all expected preset categories exist"""
        if hierarchical_enabled:
            expected_keys = ['version', 'categories', 'preset_packs', 'universal_options', 'quality_tags']
            for key in expected_keys:
                assert key in presets, f"Key '{key}' not found in hierarchical presets"
        else:
            expected_categories = ['styles', 'artists', 'composition', 'lighting']
            for category in expected_categories:
                assert category in presets, f"Category '{category}' not found in presets"

    def test_preset_categories_are_dicts(self, presets, hierarchical_enabled):
        """Verify all preset categories are dictionaries"""
        if hierarchical_enabled:
            assert isinstance(presets['categories'], dict)
            assert isinstance(presets['preset_packs'], dict)
            assert isinstance(presets['universal_options'], dict)
            assert isinstance(presets['quality_tags'], dict)
            assert isinstance(presets['version'], str)
        else:
            for category, items in presets.items():
                assert isinstance(items, dict), f"Category '{category}' is not a dictionary"

    def test_none_option_exists_in_all_categories(self, presets, hierarchical_enabled):
        """Verify 'None' option exists in each category"""
        if hierarchical_enabled:
            pytest.skip("Legacy 'None' option structure not applicable to hierarchical presets")

        for category, items in presets.items():
            assert 'None' in items, f"'None' option missing in '{category}' category"

    def test_none_option_is_empty_string(self, presets, hierarchical_enabled):
        """Verify 'None' option has empty string value"""
        if hierarchical_enabled:
            pytest.skip("Legacy 'None' option structure not applicable to hierarchical presets")

        for category, items in presets.items():
            assert items['None'] == '', f"'None' option in '{category}' should be empty string"

    def test_presets_have_string_values(self, presets, hierarchical_enabled):
        """Verify all preset values are strings"""
        if hierarchical_enabled:
            pytest.skip("Hierarchical presets use nested structures instead of simple strings")

        for category, items in presets.items():
            for preset_name, preset_value in items.items():
                assert isinstance(preset_value, str), \
                    f"Preset '{preset_name}' in '{category}' has non-string value"

    def test_presets_have_non_empty_keys(self, presets, hierarchical_enabled):
        """Verify all preset keys are non-empty strings"""
        if hierarchical_enabled:
            pytest.skip("Hierarchical presets use nested structures instead of simple string keys")

        for category, items in presets.items():
            for preset_name in items.keys():
                assert isinstance(preset_name, str), \
                    f"Preset key in '{category}' is not a string"
                assert preset_name.strip() != '', \
                    f"Empty preset key found in '{category}'"


class TestPresetCategories:
    """Test individual preset categories"""

    def test_styles_category_has_multiple_options(self, presets, hierarchical_enabled):
        """Verify styles category has multiple preset options"""
        if hierarchical_enabled:
            pytest.skip("Styles category applies only to legacy presets")
        assert len(presets['styles']) > 1, "Styles should have more than just 'None'"

    def test_artists_category_has_multiple_options(self, presets, hierarchical_enabled):
        """Verify artists category has multiple preset options"""
        if hierarchical_enabled:
            pytest.skip("Artists category applies only to legacy presets")
        assert len(presets['artists']) > 1, "Artists should have more than just 'None'"

    def test_composition_category_has_multiple_options(self, presets, hierarchical_enabled):
        """Verify composition category has multiple preset options"""
        if hierarchical_enabled:
            pytest.skip("Composition category applies only to legacy presets")
        assert len(presets['composition']) > 1, "Composition should have more than just 'None'"

    def test_lighting_category_has_multiple_options(self, presets, hierarchical_enabled):
        """Verify lighting category has multiple preset options"""
        if hierarchical_enabled:
            pytest.skip("Lighting category applies only to legacy presets")
        assert len(presets['lighting']) > 1, "Lighting should have more than just 'None'"

    def test_total_preset_count(self, presets, hierarchical_enabled):
        """Verify we have a reasonable number of total presets"""
        if hierarchical_enabled:
            categories = presets.get('categories', {})
            assert len(categories) >= 3, "Expected multiple hierarchical categories"
        else:
            total_presets = sum(len(items) for items in presets.values())
            assert total_presets >= 50, f"Expected at least 50 total presets, got {total_presets}"


class TestSpecificPresets:
    """Test for specific preset values"""

    def test_cinematic_style_exists(self, presets, hierarchical_enabled):
        """Verify Cinematic style preset exists"""
        if hierarchical_enabled:
            pytest.skip("Cinematic style is specific to legacy presets")
        assert 'Cinematic' in presets['styles'], "Cinematic style should exist"

    def test_photorealistic_style_exists(self, presets, hierarchical_enabled):
        """Verify Photorealistic style preset exists"""
        if hierarchical_enabled:
            pytest.skip("Photorealistic style is specific to legacy presets")
        assert 'Photorealistic' in presets['styles'], "Photorealistic style should exist"

    def test_portrait_composition_exists(self, presets, hierarchical_enabled):
        """Verify Portrait composition preset exists"""
        if hierarchical_enabled:
            pytest.skip("Legacy composition options are not used in hierarchical presets")
        assert 'Portrait' in presets['composition'], "Portrait composition should exist"

    def test_golden_hour_lighting_exists(self, presets, hierarchical_enabled):
        """Verify Golden Hour lighting preset exists"""
        if hierarchical_enabled:
            pytest.skip("Legacy lighting options are not used in hierarchical presets")
        assert 'Golden Hour' in presets['lighting'], "Golden Hour lighting should exist"

    def test_presets_are_not_none_values(self, presets, hierarchical_enabled):
        """Verify non-None presets have actual content"""
        if hierarchical_enabled:
            pytest.skip("Hierarchical presets use nested structures instead of string values")

        for category, items in presets.items():
            for preset_name, preset_value in items.items():
                if preset_name != 'None':
                    assert preset_value != '', \
                        f"Preset '{preset_name}' in '{category}' should not be empty"


class TestHierarchicalPresetDetails:
    """Additional checks that apply only to hierarchical presets"""

    def test_categories_have_level2_types(self, presets, hierarchical_enabled):
        if not hierarchical_enabled:
            pytest.skip("Hierarchical categories not active")

        categories = presets.get('categories', {})
        assert categories, "Expected hierarchical categories to be defined"
        for category_id, category_data in categories.items():
            assert 'name' in category_data and category_data['name'], f"Category {category_id} missing name"
            level2 = category_data.get('level2_types', {})
            assert isinstance(level2, dict) and level2, f"Category {category_id} should have level2 types"

    def test_preset_packs_have_selections(self, presets, hierarchical_enabled):
        if not hierarchical_enabled:
            pytest.skip("Hierarchical preset packs not active")

        packs = presets.get('preset_packs', {}).get('packs', [])
        assert packs, "Expected preset packs to be defined"
        for pack in packs:
            assert 'name' in pack
            assert 'selections' in pack

    def test_universal_options_include_lighting(self, presets, hierarchical_enabled):
        if not hierarchical_enabled:
            pytest.skip("Hierarchical universal options not active")

        universal = presets.get('universal_options', {})
        assert 'lighting' in universal
