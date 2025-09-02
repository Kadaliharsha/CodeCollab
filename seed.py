from app import create_app, db
from app.models import Problem, TestCase, Room

# Create a Flask app instance to work with the database
app = create_app()

def seed_database():
    """
    This function populates the database with initial coding problems
    and their test cases.
    """
    with app.app_context():
        # --- Ensure all tables are created before we start ---
        print("Creating database tables if they don't exist...")
        db.create_all()
        print("Done.")

        # --- Clean up old data ---
        print("Deleting existing problems and test cases...")
        # FIXED: Delete in the correct order to respect foreign keys
        TestCase.query.delete()
        Room.query.delete() # Delete rooms before problems
        Problem.query.delete()
        db.session.commit()
        print("Done.")

        # --- Problem 1: Reverse a String ---
        print("Creating Problem 1: Reverse a String")
        problem1 = Problem()
        problem1.title = "Reverse a String"
        problem1.description = "Write a Python function `solve(s)` that takes a string `s` and returns the string reversed."
        problem1.template_code = "def solve(s):\n    # Your code here\n    return"
        db.session.add(problem1)
        db.session.commit()

        # Test cases now expect the raw string output, without extra quotes.
        tc1_1 = TestCase()
        tc1_1.problem_id = problem1.id
        tc1_1.input_data = '"hello"'
        tc1_1.expected_output = 'olleh'
        tc1_2 = TestCase()
        tc1_2.problem_id = problem1.id
        tc1_2.input_data = '"world"'
        tc1_2.expected_output = 'dlrow'
        tc1_3 = TestCase()  # An empty string prints nothing
        tc1_3.problem_id = problem1.id
        tc1_3.input_data = '""'
        tc1_3.expected_output = ''

        db.session.add_all([tc1_1, tc1_2, tc1_3])

        # --- Problem 2: Two Sum ---
        print("Creating Problem 2: Two Sum")
        problem2 = Problem()
        problem2.title = "Two Sum"
        problem2.description = "Write a Python function `solve(nums, target)` that takes a list of integers `nums` and an integer `target`, and returns the indices of the two numbers that add up to the target."
        problem2.template_code = "def solve(nums, target):\n    # Your code here\n    return"
        db.session.add(problem2)
        db.session.commit()

        # Test cases now expect the raw list output.
        tc2_1 = TestCase()
        tc2_1.problem_id = problem2.id
        tc2_1.input_data = '[2, 7, 11, 15], 9'
        tc2_1.expected_output = '[0, 1]'
        tc2_2 = TestCase()
        tc2_2.problem_id = problem2.id
        tc2_2.input_data = '[3, 2, 4], 6'
        tc2_2.expected_output = '[1, 2]'
        tc2_3 = TestCase()
        tc2_3.problem_id = problem2.id
        tc2_3.input_data = '[3, 3], 6'
        tc2_3.expected_output = '[0, 1]'
        db.session.add_all([tc2_1, tc2_2, tc2_3])

        # --- Final Commit ---
        db.session.commit()
        print("Database has been seeded successfully!")

if __name__ == '__main__':
    seed_database()