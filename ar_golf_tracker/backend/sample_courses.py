"""Sample golf course data for testing and development."""

from typing import List, Dict, Any


def get_sample_courses() -> List[Dict[str, Any]]:
    """Get sample golf course data for testing.
    
    Returns:
        List of course dictionaries with geographic data
    """
    return [
        {
            "name": "Pebble Beach Golf Links",
            "latitude": 36.5674,
            "longitude": -121.9500,
            "address": "1700 17 Mile Dr, Pebble Beach, CA 93953",
            "total_holes": 18,
            "par": 72,
            "yardage": 6828,
            "rating": 75.5,
            "slope": 145,
            "holes": [
                {"hole_number": 1, "par": 4, "yardage": 380, "tee_lat": 36.5674, "tee_lon": -121.9500, "green_lat": 36.5680, "green_lon": -121.9505},
                {"hole_number": 2, "par": 5, "yardage": 502, "tee_lat": 36.5681, "tee_lon": -121.9506, "green_lat": 36.5690, "green_lon": -121.9515},
                {"hole_number": 3, "par": 4, "yardage": 390, "tee_lat": 36.5691, "tee_lon": -121.9516, "green_lat": 36.5698, "green_lon": -121.9522},
                {"hole_number": 4, "par": 4, "yardage": 331, "tee_lat": 36.5699, "tee_lon": -121.9523, "green_lat": 36.5705, "green_lon": -121.9528},
                {"hole_number": 5, "par": 3, "yardage": 188, "tee_lat": 36.5706, "tee_lon": -121.9529, "green_lat": 36.5710, "green_lon": -121.9532},
                {"hole_number": 6, "par": 5, "yardage": 523, "tee_lat": 36.5711, "tee_lon": -121.9533, "green_lat": 36.5720, "green_lon": -121.9542},
                {"hole_number": 7, "par": 3, "yardage": 106, "tee_lat": 36.5721, "tee_lon": -121.9543, "green_lat": 36.5724, "green_lon": -121.9545},
                {"hole_number": 8, "par": 4, "yardage": 428, "tee_lat": 36.5725, "tee_lon": -121.9546, "green_lat": 36.5733, "green_lon": -121.9553},
                {"hole_number": 9, "par": 4, "yardage": 464, "tee_lat": 36.5734, "tee_lon": -121.9554, "green_lat": 36.5743, "green_lon": -121.9562},
                {"hole_number": 10, "par": 4, "yardage": 446, "tee_lat": 36.5744, "tee_lon": -121.9563, "green_lat": 36.5752, "green_lon": -121.9570},
                {"hole_number": 11, "par": 4, "yardage": 390, "tee_lat": 36.5753, "tee_lon": -121.9571, "green_lat": 36.5760, "green_lon": -121.9577},
                {"hole_number": 12, "par": 3, "yardage": 202, "tee_lat": 36.5761, "tee_lon": -121.9578, "green_lat": 36.5765, "green_lon": -121.9581},
                {"hole_number": 13, "par": 4, "yardage": 445, "tee_lat": 36.5766, "tee_lon": -121.9582, "green_lat": 36.5774, "green_lon": -121.9589},
                {"hole_number": 14, "par": 5, "yardage": 580, "tee_lat": 36.5775, "tee_lon": -121.9590, "green_lat": 36.5785, "green_lon": -121.9600},
                {"hole_number": 15, "par": 4, "yardage": 397, "tee_lat": 36.5786, "tee_lon": -121.9601, "green_lat": 36.5793, "green_lon": -121.9607},
                {"hole_number": 16, "par": 4, "yardage": 402, "tee_lat": 36.5794, "tee_lon": -121.9608, "green_lat": 36.5801, "green_lon": -121.9614},
                {"hole_number": 17, "par": 3, "yardage": 178, "tee_lat": 36.5802, "tee_lon": -121.9615, "green_lat": 36.5806, "green_lon": -121.9618},
                {"hole_number": 18, "par": 5, "yardage": 543, "tee_lat": 36.5807, "tee_lon": -121.9619, "green_lat": 36.5817, "green_lon": -121.9629},
            ]
        },
        {
            "name": "Augusta National Golf Club",
            "latitude": 33.5030,
            "longitude": -82.0200,
            "address": "2604 Washington Rd, Augusta, GA 30904",
            "total_holes": 18,
            "par": 72,
            "yardage": 7475,
            "rating": 76.2,
            "slope": 148,
            "holes": [
                {"hole_number": i, "par": 4 if i % 3 != 0 else (3 if i % 5 == 0 else 5), 
                 "yardage": 400 + (i * 10), 
                 "tee_lat": 33.5030 + (i * 0.001), "tee_lon": -82.0200 + (i * 0.001),
                 "green_lat": 33.5030 + (i * 0.001) + 0.0005, "green_lon": -82.0200 + (i * 0.001) + 0.0005}
                for i in range(1, 19)
            ]
        },
        {
            "name": "St Andrews Old Course",
            "latitude": 56.3450,
            "longitude": -2.8050,
            "address": "Pilmour Links, St Andrews KY16 9SF, UK",
            "total_holes": 18,
            "par": 72,
            "yardage": 7297,
            "rating": 75.9,
            "slope": 142,
            "holes": [
                {"hole_number": i, "par": 4 if i % 4 != 0 else (3 if i % 6 == 0 else 5), 
                 "yardage": 380 + (i * 15), 
                 "tee_lat": 56.3450 + (i * 0.0008), "tee_lon": -2.8050 + (i * 0.0008),
                 "green_lat": 56.3450 + (i * 0.0008) + 0.0004, "green_lon": -2.8050 + (i * 0.0008) + 0.0004}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Pinehurst No. 2",
            "latitude": 35.1900,
            "longitude": -79.4700,
            "address": "1 Carolina Vista Dr, Pinehurst, NC 28374",
            "total_holes": 18,
            "par": 72,
            "yardage": 7588,
            "rating": 76.9,
            "slope": 145,
            "holes": [
                {"hole_number": i, "par": 4 if i % 3 != 0 else (3 if i % 7 == 0 else 5), 
                 "yardage": 390 + (i * 12), 
                 "tee_lat": 35.1900 + (i * 0.0009), "tee_lon": -79.4700 + (i * 0.0009),
                 "green_lat": 35.1900 + (i * 0.0009) + 0.00045, "green_lon": -79.4700 + (i * 0.0009) + 0.00045}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Torrey Pines Golf Course",
            "latitude": 32.9000,
            "longitude": -117.2500,
            "address": "11480 N Torrey Pines Rd, La Jolla, CA 92037",
            "total_holes": 18,
            "par": 72,
            "yardage": 7698,
            "rating": 77.7,
            "slope": 144,
            "holes": [
                {"hole_number": i, "par": 4 if i % 4 != 0 else (3 if i % 5 == 0 else 5), 
                 "yardage": 410 + (i * 11), 
                 "tee_lat": 32.9000 + (i * 0.0007), "tee_lon": -117.2500 + (i * 0.0007),
                 "green_lat": 32.9000 + (i * 0.0007) + 0.00035, "green_lon": -117.2500 + (i * 0.0007) + 0.00035}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Bethpage Black Course",
            "latitude": 40.7450,
            "longitude": -73.4600,
            "address": "99 Quaker Meeting House Rd, Farmingdale, NY 11735",
            "total_holes": 18,
            "par": 71,
            "yardage": 7468,
            "rating": 77.5,
            "slope": 148,
            "holes": [
                {"hole_number": i, "par": 4 if i % 3 != 0 else (3 if i % 8 == 0 else 5), 
                 "yardage": 395 + (i * 13), 
                 "tee_lat": 40.7450 + (i * 0.0006), "tee_lon": -73.4600 + (i * 0.0006),
                 "green_lat": 40.7450 + (i * 0.0006) + 0.0003, "green_lon": -73.4600 + (i * 0.0006) + 0.0003}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Whistling Straits",
            "latitude": 43.7500,
            "longitude": -87.7200,
            "address": "N8501 Lakeshore Rd, Sheboygan, WI 53083",
            "total_holes": 18,
            "par": 72,
            "yardage": 7790,
            "rating": 78.1,
            "slope": 151,
            "holes": [
                {"hole_number": i, "par": 4 if i % 4 != 0 else (3 if i % 6 == 0 else 5), 
                 "yardage": 420 + (i * 14), 
                 "tee_lat": 43.7500 + (i * 0.0008), "tee_lon": -87.7200 + (i * 0.0008),
                 "green_lat": 43.7500 + (i * 0.0008) + 0.0004, "green_lon": -87.7200 + (i * 0.0008) + 0.0004}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Oakmont Country Club",
            "latitude": 40.5200,
            "longitude": -79.8500,
            "address": "1233 Hulton Rd, Oakmont, PA 15139",
            "total_holes": 18,
            "par": 71,
            "yardage": 7255,
            "rating": 77.0,
            "slope": 145,
            "holes": [
                {"hole_number": i, "par": 4 if i % 3 != 0 else (3 if i % 7 == 0 else 5), 
                 "yardage": 385 + (i * 12), 
                 "tee_lat": 40.5200 + (i * 0.0007), "tee_lon": -79.8500 + (i * 0.0007),
                 "green_lat": 40.5200 + (i * 0.0007) + 0.00035, "green_lon": -79.8500 + (i * 0.0007) + 0.00035}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Shinnecock Hills Golf Club",
            "latitude": 40.8900,
            "longitude": -72.4500,
            "address": "200 Tuckahoe Rd, Southampton, NY 11968",
            "total_holes": 18,
            "par": 70,
            "yardage": 7445,
            "rating": 77.6,
            "slope": 146,
            "holes": [
                {"hole_number": i, "par": 4 if i % 4 != 0 else (3 if i % 5 == 0 else 5), 
                 "yardage": 400 + (i * 13), 
                 "tee_lat": 40.8900 + (i * 0.0006), "tee_lon": -72.4500 + (i * 0.0006),
                 "green_lat": 40.8900 + (i * 0.0006) + 0.0003, "green_lon": -72.4500 + (i * 0.0006) + 0.0003}
                for i in range(1, 19)
            ]
        },
        {
            "name": "Merion Golf Club",
            "latitude": 40.0100,
            "longitude": -75.2700,
            "address": "450 Ardmore Ave, Ardmore, PA 19003",
            "total_holes": 18,
            "par": 70,
            "yardage": 6996,
            "rating": 75.4,
            "slope": 144,
            "holes": [
                {"hole_number": i, "par": 4 if i % 3 != 0 else (3 if i % 6 == 0 else 5), 
                 "yardage": 370 + (i * 11), 
                 "tee_lat": 40.0100 + (i * 0.0008), "tee_lon": -75.2700 + (i * 0.0008),
                 "green_lat": 40.0100 + (i * 0.0008) + 0.0004, "green_lon": -75.2700 + (i * 0.0008) + 0.0004}
                for i in range(1, 19)
            ]
        },
    ]


def load_sample_courses(db) -> None:
    """Load sample courses into the database.
    
    Args:
        db: CloudDatabase instance
    """
    courses = get_sample_courses()
    conn = db.connect()
    
    with conn.cursor() as cursor:
        for course_data in courses:
            # Insert course
            cursor.execute("""
                INSERT INTO courses (name, location, address, total_holes, par, yardage, rating, slope)
                VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                course_data["name"],
                course_data["longitude"],
                course_data["latitude"],
                course_data["address"],
                course_data["total_holes"],
                course_data["par"],
                course_data["yardage"],
                course_data.get("rating"),
                course_data.get("slope")
            ))
            
            course_id = cursor.fetchone()[0]
            
            # Insert holes
            for hole_data in course_data["holes"]:
                cursor.execute("""
                    INSERT INTO holes (
                        course_id, hole_number, par, yardage,
                        tee_box_location, green_location
                    )
                    VALUES (%s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    )
                """, (
                    course_id,
                    hole_data["hole_number"],
                    hole_data["par"],
                    hole_data["yardage"],
                    hole_data["tee_lon"],
                    hole_data["tee_lat"],
                    hole_data["green_lon"],
                    hole_data["green_lat"]
                ))
    
    conn.commit()
    print(f"Loaded {len(courses)} sample courses with holes")
