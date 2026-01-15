"""Example usage of mobile app components.

Demonstrates how to use the round list and detail views with the API client.
"""

from ar_golf_tracker.mobile_app.api_client import APIClient
from ar_golf_tracker.mobile_app.round_list_view import RoundListView
from ar_golf_tracker.mobile_app.round_detail_view import RoundDetailView


def example_round_list_workflow():
    """Example workflow for displaying and selecting rounds."""
    
    # Initialize API client
    api_client = APIClient(base_url="https://api.argolftracker.com")
    
    # Login (in real app, get credentials from user)
    tokens = api_client.login("user@example.com", "password123")
    print(f"Logged in successfully")
    
    # Fetch rounds from API
    rounds_data = api_client.get_rounds(limit=20)
    print(f"Fetched {len(rounds_data)} rounds")
    
    # Create round list view
    round_list = RoundListView()
    round_list.load_rounds(rounds_data)
    
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
    
    # Initialize API client
    api_client = APIClient(base_url="https://api.argolftracker.com")
    
    # Login (in real app, reuse existing token)
    tokens = api_client.login("user@example.com", "password123")
    
    # Fetch round details
    round_data = api_client.get_round(round_id)
    shots_data = api_client.get_round_shots(round_id)
    
    # Optionally fetch course data
    course_data = None
    if round_data.get('course_id'):
        try:
            course_data = api_client.get_course(round_data['course_id'])
        except Exception as e:
            print(f"Could not fetch course data: {e}")
    
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
        print(f"  Hole {hole['hole_number']}: {hole['shot_count']} shots, {hole['total_distance']}")


def example_filtering_workflow():
    """Example workflow demonstrating filtering and sorting."""
    
    # Initialize API client
    api_client = APIClient(base_url="https://api.argolftracker.com")
    
    # Login
    tokens = api_client.login("user@example.com", "password123")
    
    # Fetch rounds
    rounds_data = api_client.get_rounds(limit=50)
    
    # Create round list view
    round_list = RoundListView()
    round_list.load_rounds(rounds_data)
    
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
    print("AR Golf Tracker Mobile App - Example Usage")
    print("=" * 60)
    
    # Note: These examples require a running backend API
    # In a real application, you would handle authentication and errors properly
    
    print("\nExample 1: Round List Workflow")
    print("-" * 60)
    try:
        round_id = example_round_list_workflow()
        
        if round_id:
            print("\n\nExample 2: Round Detail Workflow")
            print("-" * 60)
            example_round_detail_workflow(round_id)
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This example requires a running backend API")
    
    print("\n\nExample 3: Filtering and Sorting")
    print("-" * 60)
    try:
        example_filtering_workflow()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This example requires a running backend API")
