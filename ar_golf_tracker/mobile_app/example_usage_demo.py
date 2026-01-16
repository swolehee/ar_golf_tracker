"""Demo usage of mobile app components with mock data.

Demonstrates how to use the round list and detail views without requiring a backend.
"""

from datetime import datetime, timedelta
from ar_golf_tracker.mobile_app.round_list_view import RoundListView
from ar_golf_tracker.mobile_app.round_detail_view import RoundDetailView


def create_mock_rounds():
    """Create mock round data for demonstration."""
    rounds = []
    courses = ["Pebble Beach", "Augusta National", "St Andrews", "Pinehurst No. 2"]
    
    for i in range(10):
        date = datetime.now() - timedelta(days=i*7)
        start_time = date.replace(hour=9, minute=0, second=0)
        end_time = date.replace(hour=13, minute=30, second=0)
        
        rounds.append({
            'id': f'round_{i}',
            'user_id': 'demo_user',
            'course_id': f'course_{i % len(courses)}',
            'course_name': courses[i % len(courses)],
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'weather_conditions': 'Sunny' if i % 2 == 0 else 'Cloudy',
            'notes': f'Round {i+1} notes'
        })
    
    return rounds


def create_mock_shots(round_id: str):
    """Create mock shot data for a round."""
    shots = []
    clubs = ['Driver', '3-Wood', '5-Iron', '7-Iron', '9-Iron', 'Pitching Wedge', 'Sand Wedge', 'Putter']
    
    shot_num = 1
    swing_num = 1
    for hole in range(1, 19):
        # Tee shot
        shots.append({
            'id': f'shot_{shot_num}',
            'round_id': round_id,
            'hole_number': hole,
            'swing_number': swing_num,
            'club_type': 'Driver' if hole % 3 != 0 else '3-Wood',
            'shot_time': datetime.now().isoformat(),
            'gps_lat': 36.5674 + (hole * 0.001),
            'gps_lon': -121.9500 + (hole * 0.001),
            'gps_accuracy': 5.0,
            'gps_altitude': 10.0,
            'distance_yards': 250 + (hole % 30),
            'distance_accuracy': 2.0,
            'notes': None
        })
        shot_num += 1
        swing_num += 1
        
        # Approach shot
        shots.append({
            'id': f'shot_{shot_num}',
            'round_id': round_id,
            'hole_number': hole,
            'swing_number': swing_num,
            'club_type': clubs[4 + (hole % 3)],
            'shot_time': datetime.now().isoformat(),
            'gps_lat': 36.5674 + (hole * 0.001) + 0.002,
            'gps_lon': -121.9500 + (hole * 0.001) + 0.002,
            'gps_accuracy': 5.0,
            'gps_altitude': 10.0,
            'distance_yards': 120 + (hole % 40),
            'distance_accuracy': 2.0,
            'notes': None
        })
        shot_num += 1
        swing_num += 1
        
        # Putt(s)
        putts = 2 if hole % 3 == 0 else 1
        for _ in range(putts):
            shots.append({
                'id': f'shot_{shot_num}',
                'round_id': round_id,
                'hole_number': hole,
                'swing_number': swing_num,
                'club_type': 'Putter',
                'shot_time': datetime.now().isoformat(),
                'gps_lat': 36.5674 + (hole * 0.001) + 0.003,
                'gps_lon': -121.9500 + (hole * 0.001) + 0.003,
                'gps_accuracy': 5.0,
                'gps_altitude': 10.0,
                'distance_yards': 15 + (hole % 10),
                'distance_accuracy': 1.0,
                'notes': None
            })
            shot_num += 1
            swing_num += 1
    
    return shots


def create_mock_course():
    """Create mock course data."""
    return {
        'id': 'course_0',
        'name': 'Pebble Beach',
        'location': 'Pebble Beach, CA',
        'par': 72,
        'yardage': 6828,
        'rating': 74.5,
        'slope': 145,
        'holes': [
            {'number': i, 'par': 4 if i % 3 != 0 else (3 if i % 5 == 0 else 5), 'yardage': 380 + (i * 10)}
            for i in range(1, 19)
        ]
    }


def example_round_list_workflow():
    """Example workflow for displaying and selecting rounds."""
    
    print("Creating mock data...")
    rounds_data = create_mock_rounds()
    
    # Create shots for each round
    shots_by_round = {}
    for round_data in rounds_data:
        shots_by_round[round_data['id']] = create_mock_shots(round_data['id'])
    
    # Create round list view
    round_list = RoundListView()
    round_list.load_rounds_with_shots(rounds_data, shots_by_round)
    
    # Display rounds summary
    summary = round_list.get_rounds_summary()
    print(f"\nRounds Summary:")
    print(f"  Total rounds: {summary['total_rounds']}")
    print(f"  Total shots: {summary['total_shots']}")
    print(f"  Unique courses: {summary['unique_courses']}")
    if summary['date_range']:
        print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
    
    # Display round list
    print(f"\nRecent Rounds:")
    for round_item in round_list.get_filtered_rounds()[:5]:
        data = round_item.to_dict()
        print(f"  {data['date']} - {data['course_name']}")
        print(f"    Shots: {data['total_shots']}, Holes: {data['holes_played']}")
    
    # Select a round
    if round_list.get_round_count() > 0:
        first_round = round_list.get_filtered_rounds()[0]
        round_list.select_round(first_round.id)
        print(f"\nSelected round: {first_round.course_name}")
        
        return first_round.id
    
    return None


def example_round_detail_workflow(round_id: str):
    """Example workflow for displaying round details.
    
    Args:
        round_id: ID of the round to display
    """
    
    print("\nFetching round details...")
    
    # Create mock data
    rounds_data = create_mock_rounds()
    round_data = next((r for r in rounds_data if r['id'] == round_id), None)
    shots_data = create_mock_shots(round_id)
    course_data = create_mock_course()
    
    # Create round detail view
    detail_view = RoundDetailView()
    detail_view.load_round(round_data, shots_data, course_data)
    
    # Display round summary
    summary = detail_view.get_round_summary()
    print(f"\nRound Details:")
    print(f"  Course: {summary['course_name']}")
    print(f"  Date: {summary['date']} at {summary['start_time']}")
    if summary['duration']:
        print(f"  Duration: {summary['duration']}")
    print(f"  Total shots: {summary['total_shots']}")
    print(f"  Holes played: {summary['holes_played']}")
    
    # Display course info if available
    course_info = detail_view.get_course_info()
    if course_info:
        print(f"\nCourse Information:")
        print(f"  Par: {course_info['par']}")
        print(f"  Yardage: {course_info['yardage']}")
        if course_info['rating']:
            print(f"  Rating: {course_info['rating']}")
        if course_info['slope']:
            print(f"  Slope: {course_info['slope']}")
    
    # Display club usage
    club_usage = detail_view.get_club_usage_summary()
    print(f"\nClub Usage:")
    for club, count in sorted(club_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {club}: {count} shots")
    
    # Display average distances
    avg_distances = detail_view.get_average_distance_by_club()
    if avg_distances:
        print(f"\nAverage Distances:")
        for club, distance in sorted(avg_distances.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {club}: {distance:.1f} yards")
    
    # Display hole-by-hole breakdown
    print(f"\nHole-by-Hole Breakdown:")
    for hole in detail_view.get_holes_data()[:9]:  # First 9 holes
        total_dist = hole['total_distance']
        if isinstance(total_dist, str):
            print(f"  Hole {hole['hole_number']}: {hole['shot_count']} shots, {total_dist}")
        else:
            print(f"  Hole {hole['hole_number']}: {hole['shot_count']} shots, {total_dist:.0f} yards")


def example_filtering_workflow():
    """Example workflow demonstrating filtering and sorting."""
    
    print("\nDemonstrating filtering and sorting...")
    
    # Create mock data
    rounds_data = create_mock_rounds()
    
    # Create shots for each round
    shots_by_round = {}
    for round_data in rounds_data:
        shots_by_round[round_data['id']] = create_mock_shots(round_data['id'])
    
    # Create round list view
    round_list = RoundListView()
    round_list.load_rounds_with_shots(rounds_data, shots_by_round)
    
    # Get unique courses
    courses = round_list.get_unique_courses()
    print(f"\nCourses played:")
    for course in courses:
        print(f"  - {course}")
    
    # Filter by course
    if courses:
        selected_course = courses[0]
        round_list.set_course_filter(selected_course)
        print(f"\nRounds at {selected_course}:")
        for round_item in round_list.get_filtered_rounds():
            data = round_item.to_dict()
            print(f"  {data['date']}: {data['total_shots']} shots")
    
    # Clear filter and sort by oldest first
    round_list.set_course_filter(None)
    round_list.set_sort_order('asc')
    print(f"\nAll rounds (oldest first):")
    for round_item in round_list.get_filtered_rounds()[:5]:
        data = round_item.to_dict()
        print(f"  {data['date']} - {data['course_name']}")


if __name__ == "__main__":
    print("=" * 60)
    print("AR Golf Tracker Mobile App - Demo Usage")
    print("=" * 60)
    print("\nThis demo uses mock data and doesn't require a backend server.")
    
    print("\nExample 1: Round List Workflow")
    print("-" * 60)
    round_id = example_round_list_workflow()
    
    if round_id:
        print("\n\nExample 2: Round Detail Workflow")
        print("-" * 60)
        example_round_detail_workflow(round_id)
    
    print("\n\nExample 3: Filtering and Sorting")
    print("-" * 60)
    example_filtering_workflow()
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
