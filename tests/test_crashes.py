"""Offline checks of consequential validation and export behavior."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from src.analysis.crashes import prepare_crashes


def feature(incident='a', x=-104.99, y=39.74, fatal=0, serious=1, pedestrian=1, bicycle=0,
            offense=None, year=2025):
    from datetime import datetime, timezone
    timestamp = int(datetime(year, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
    return {'attributes': {'incident_id': incident, 'first_occurrence_date': timestamp,
                           'FATALITIES': fatal, 'SERIOUSLY_INJURED': serious,
                           'pedestrian_ind': pedestrian, 'bicycle_ind': bicycle,
                           'top_traffic_accident_offense': offense},
            'geometry': {'x': x, 'y': y}}


def payload(*features):
    return {'spatialReference': {'wkid': 4326}, 'features': list(features)}


class CrashValidation(unittest.TestCase):
    def test_details_preserve_reported_context_and_distinguish_missing_snapshot_fields(self):
        first = feature('context')
        first['attributes'].update({'incident_address': 'MAIN ST / FIRST AVE',
                                    'LIGHT_CONDITION': 'DARK - LIGHTED',
                                    'ROAD_CONDITION': None,
                                    'TU1_VEHICLE_TYPE': 'PASSENGER CAR',
                                    'TU2_VEHICLE_TYPE': 'BICYCLE',
                                    'FATALITY_MODE_1': 'PEDESTRIAN'})
        second = feature('minimal')
        geo, qa = prepare_crashes(payload(first, second), 2025)
        rows = geo.set_index('incident_id')
        self.assertEqual(rows.loc['context', 'location'], 'MAIN ST / FIRST AVE')
        self.assertEqual(rows.loc['context', 'vehicle_types'], 'BICYCLE / PASSENGER CAR')
        self.assertEqual(rows.loc['context', 'road_condition'], 'Not reported')
        self.assertEqual(rows.loc['minimal', 'road_condition'], 'Not in snapshot')
        self.assertEqual(rows.loc['context', 'occurrence_utc'], '01 Mar 2025, 00:00 UTC')
        self.assertEqual(qa['detail_coverage']['location'], 1)

    def test_denver_tooltip_time_handles_dst_and_date_rollover(self):
        import pandas as pd
        cases = [
            ('2025-01-15T18:00:00Z', '15 Jan 2025, 11:00 MST'),
            ('2025-07-01T18:00:00Z', '01 Jul 2025, 12:00 MDT'),
            ('2025-03-09T08:59:00Z', '09 Mar 2025, 01:59 MST'),
            ('2025-03-09T09:00:00Z', '09 Mar 2025, 03:00 MDT'),
            ('2025-01-01T02:00:00Z', '31 Dec 2024, 19:00 MST'),
        ]
        for utc, expected in cases:
            with self.subTest(utc=utc):
                event = feature()
                event['attributes']['first_occurrence_date'] = int(pd.Timestamp(utc).timestamp() * 1000)
                geo, _ = prepare_crashes(payload(event), 2025)
                self.assertEqual(geo.iloc[0].occurrence_denver, expected)

    def test_offense_labels_recover_severity_without_inventing_person_counts(self):
        data = payload(feature('fatal', fatal=0, serious=0, offense='TRAF - ACCIDENT - FATAL '),
                       feature('sbi', fatal=None, serious=None, offense='TRAF - ACCIDENT - SBI '),
                       feature('minor', fatal=0, serious=0, offense='TRAF - ACCIDENT '))
        geo, qa = prepare_crashes(data, 2025)
        self.assertEqual(qa['mapped_incidents'], 2)
        self.assertEqual(qa['fatal_crashes'], 1)
        self.assertEqual(qa['offense_only_severity_rows'], 2)
        self.assertEqual(qa['nonsevere_rows'], 1)
        self.assertEqual(set(geo.severity), {'Fatal', 'Serious injury'})

    def test_five_complete_years_have_separate_annual_counts(self):
        data = payload(*(feature(str(y), year=y, fatal=int(y == 2021)) for y in range(2021, 2026)))
        geo, qa = prepare_crashes(data, (2021, 2025))
        self.assertEqual(len(geo), 5)
        self.assertEqual([r['year'] for r in qa['annual_counts']], list(range(2021, 2026)))
        self.assertEqual(sum(r['mapped_incidents'] for r in qa['annual_counts']), 5)
        self.assertEqual(qa['annual_counts'][0]['fatal_crashes'], 1)

    def test_pedestrian_or_bicycle_filter_and_overlapping_totals(self):
        data = payload(feature('walk'), feature('bike', pedestrian=0, bicycle=1),
                       feature('both', pedestrian=1, bicycle=1),
                       feature('car', pedestrian=0), feature('unknown', pedestrian=None),
                       feature('badflag', pedestrian=2))
        geo, qa = prepare_crashes(data, 2025)
        self.assertEqual(set(geo.incident_id), {'walk', 'bike', 'both'})
        self.assertEqual(qa['mapped_incidents'], 3)
        self.assertEqual(qa['pedestrian_involved_crashes'], 2)
        self.assertEqual(qa['bicycle_involved_crashes'], 2)
        self.assertEqual(qa['both_modes_crashes'], 1)
        self.assertEqual(qa['other_mode_rows'], 1)
        self.assertEqual(qa['unknown_mode_rows'], 2)

    def test_duplicate_offenses_are_one_event_with_fatal_precedence(self):
        geo, qa = prepare_crashes(payload(feature(), feature(fatal=1)), 2025)
        self.assertEqual(len(geo), 1)
        self.assertEqual(qa['fatal_crashes'], 1)
        self.assertEqual(qa['duplicate_rows_collapsed'], 1)
        self.assertEqual(geo.crs.to_epsg(), 26913)
        self.assertEqual(geo.iloc[0].severity, 'Fatal')

    def test_bad_coordinates_unknown_severity_and_conflicts_are_reported(self):
        data = payload(feature('ok'), feature('nan', x=float('nan')),
                       feature('outside', x=0), feature('unknown', fatal=None, serious=None),
                       feature('conflict'), feature('conflict', x=-104.90))
        geo, qa = prepare_crashes(data, 2025)
        self.assertEqual(list(geo.incident_id), ['ok'])
        self.assertEqual(qa['invalid_coordinate'], 2)
        self.assertEqual(qa['unknown_severity'], 1)
        self.assertEqual(qa['conflicting_incidents'], 1)

    def test_wrong_crs_empty_data_and_schema_change_stop(self):
        for data in [{'spatialReference': {'wkid': 2877}, 'features': [feature()]},
                     payload(), payload({'attributes': {}, 'geometry': {}})]:
            with self.assertRaises(ValueError):
                prepare_crashes(data, 2025)

    def test_interactive_export_and_reproduction_artifacts(self):
        import json
        script = Path(__file__).resolve().parents[1] / 'maps/day01-points/main.py'
        spec = importlib.util.spec_from_file_location('day01_main', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'synthetic.json'
            source.write_text(json.dumps(payload(feature(), feature('b', x=-104.85, y=39.8, fatal=1))))
            output = Path(directory) / 'synthetic.html'
            stats = module.render(source, 2025, output)
            self.assertEqual(stats['mapped_incidents'], 2)
            html = output.with_suffix('.html').read_text()
            self.assertIn('ScatterplotLayer', html)
            self.assertIn('CC BY 3.0', html)
            self.assertIn('tile.openstreetmap.org', html)
            self.assertIn('OpenStreetMap contributors', html)
            self.assertIn('map-heading', html)
            self.assertNotIn('AI-assisted analysis and cartography', html)
            self.assertNotIn('validated crash events. Pan', html)
            self.assertIn('occurrence_denver', html)
            self.assertIn('Not in snapshot', html)
            self.assertTrue(output.with_suffix('.qa.json').exists())
            self.assertTrue(output.with_suffix('.results.md').exists())

    def test_multi_year_exports_require_all_snapshots_and_preserve_years(self):
        import json
        script = Path(__file__).resolve().parents[1] / 'maps/day01-points/main.py'
        spec = importlib.util.spec_from_file_location('day01_multi', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            sources = []
            for year in range(2021, 2026):
                source = Path(directory) / f'{year}.json'
                source.write_text(json.dumps(payload(feature(str(year), year=year))))
                sources.append(source)
            output = Path(directory) / 'five-year.html'
            stats = module.render(sources, (2021, 2025), output)
            self.assertEqual(stats['mapped_incidents'], 5)
            self.assertEqual(len(stats['inputs']), 5)
            self.assertIn('2021–2025', output.with_suffix('.html').read_text())
            with self.assertRaises(ValueError):
                module.render(sources[:-1], (2021, 2025), output)

    def test_html_export_escapes_source_script_delimiters_and_rejects_png(self):
        import json
        script = Path(__file__).resolve().parents[1] / 'maps/day01-points/main.py'
        spec = importlib.util.spec_from_file_location('day01_html_only', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'synthetic.json'
            event = feature()
            event['attributes']['incident_address'] = '</script><script>alert(1)</script>'
            source.write_text(json.dumps(payload(event)))
            output = Path(directory) / 'map.html'
            module.render(source, 2025, output)
            self.assertFalse(output.with_suffix('.png').exists())
            with self.assertRaises(ValueError):
                module.render(source, 2025, output.with_suffix('.png'))
            html = output.with_suffix('.html').read_text()
            self.assertNotIn('</script><script>alert(1)</script>', html)
            self.assertTrue(output.with_suffix('.qa.json').exists())


if __name__ == '__main__':
    unittest.main()
