from pathlib import Path

import shapely.wkt
from warg import ensure_in_sys_path

ensure_in_sys_path(Path(__file__).parent.parent)

from ..utilities.string_parsing import extract_wkt_elements


def test_parsing_duplicate_point_str():
    source = "HTTP response body: b'{\"message\":\"Object with id cbca6c782cd14b88bd76173d is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.202275 47.616914)'\\nObject with id 9761e40232004526a4341d17 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.202268 47.616645)'\\nObject with id 04eaa401d7944d789c6cc3dc is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.202276 47.616925)'\\nObject with id 8bb4b33df68141c3a68b1cd5 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201303 47.617707)'\\nObject with id 2296f18cf6134d53a3bdc834 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201393 47.615763)'\\nObject with id 7361f6d2be284272a7c0916a is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201083 47.616701)'\\nObject with id 561c6b2e6d5c4c2483e61fca is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201393 47.615763)'\\nObject with id 108b4f58c6e3450e8eef9a05 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201466 47.616727)'\\nObject with id 68092a42b8a54a228058074d is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201422 47.614747)'\\nObject with id db9140c101304ab38be51a84 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.200977 47.614365)'\\nObject with id bfad493a1cd34a329c024055 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.201346 47.614674)'\\nObject with id 09a614dd8de3457bbc93dd05 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.200676 47.61526)'\\nObject with id 8d8ceab18d4a4fdc8f42cfc2 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.200384 47.617913)'\\nObject with id 9939539d541f4dd7bb44e967 is invalid: Geometry is invalid: 'duplicate points at index 1: POINT (-122.200493 47.617871)'\"}'"

    target = [
        shapely.wkt.loads(e)
        for e in [
            "POINT (-122.202275 47.616914)",
            "POINT (-122.202268 47.616645)",
            "POINT (-122.202276 47.616925)",
            "POINT (-122.201303 47.617707)",
            "POINT (-122.201393 47.615763)",
            "POINT (-122.201083 47.616701)",
            "POINT (-122.201393 47.615763)",
            "POINT (-122.201466 47.616727)",
            "POINT (-122.201422 47.614747)",
            "POINT (-122.200977 47.614365)",
            "POINT (-122.201346 47.614674)",
            "POINT (-122.200676 47.61526)",
            "POINT (-122.200384 47.617913)",
            "POINT (-122.200493 47.617871)",
        ]
    ]

    parsed = [e for c, e in extract_wkt_elements(source)]

    assert parsed == target, f"{parsed=} {target=}"


def test_self_intersection_str():
    source = 'HTTP response body: b\'{"message":"Object with id 67288225d29f4b998f47c4e8 is invalid: Geometry is invalid: \'Self-intersection occured at POINT (-122.20231413590133 47.61731151709477)\'"}'

    parsed = [e for c, e in extract_wkt_elements(source)]
    assert parsed == [
        shapely.wkt.loads("POINT (-122.20231413590133 47.61731151709477)")
    ]


def testsuh_iajsd():
    source = """'{"message":"Object with id 32d681921e224e8caab7e180 is invalid: Geometry is invalid: \\\'duplicate points at index 1: POINT (-122.204195 47.615519)\\\'\\\\nObject with id f7cfe3749d074dcf9fc21cbd is invalid: Geometry is invalid: \\\'duplicate points at index 3: POINT (-122.201867 47.615212)\\\'\\\\nObject with id cf2d1ea95c0e4c7b87c72eeb is invalid: Geometry is invalid: \\\'duplicate points at index 1: POINT (-122.20298 47.615697)\\\'\\\\nObject with id d28df0a34e4545fb812bc8ed is invalid: Geometry is invalid: \\\'duplicate points at index 11: POINT (-122.205033 47.615597)\\\'\\\\nObject with id 947c4efaf6414502b6259168 is invalid: Geometry is invalid: \\\'duplicate points at index 2: POINT (-122.201305 47.616761)\\\'\\\\nObject with id aa51054b7e0248f88a6ea3eb is invalid: Geometry is invalid: \\\'duplicate points at index 1: POINT (-122.200375 47.61519)\\\'\\\\nObject with id 4c9951fbabfe4f6eb160e0a5 is invalid: Geometry is invalid: \\\'duplicate points at index 5: POINT (-122.200399 47.617882)\\\'\\\\nObject with id 138f9c80dea14247a728d171 is invalid: Geometry is invalid: \\\'duplicate points at index 1: POINT (-122.200935 47.617599)\\\'\\\\nObject with id 7b7869a73d964a2e94632550 is invalid: Geometry is invalid: \\\'duplicate points at index 1: POINT (-122.200493 47.617871)\\\'"}'
"""
    contexts, parsed = zip(*extract_wkt_elements(source))
    print(contexts)
    print(parsed)


if __name__ == "__main__":
    test_parsing_duplicate_point_str()
    test_self_intersection_str()
    testsuh_iajsd()
