"""Satellite image catalog for the dashboard."""

from collections import Counter

from backend.satellite_simulation import load_manifest


def satellite_catalog(class_name=None, limit=50, offset=0):
    records = load_manifest()

    classes = Counter(
        record["class_name"]
        for record in records
    )

    if class_name is not None:
        if class_name not in classes:
            raise ValueError("Unknown satellite land-use class.")

        selected = [
            (index, record)
            for index, record in enumerate(records)
            if record["class_name"] == class_name
        ]
    else:
        selected = list(enumerate(records))

    total = len(selected)
    page = selected[offset:offset + limit]

    images = [
        {
            "image_index": index,
            "class_name": record["class_name"],
            "filename": record["saved_path"].split("/")[-1],
        }
        for index, record in page
    ]

    return {
        "total_images": len(records),
        "filtered_total": total,
        "classes": [
            {"name": name, "count": count}
            for name, count in sorted(classes.items())
        ],
        "limit": limit,
        "offset": offset,
        "images": images,
    }
