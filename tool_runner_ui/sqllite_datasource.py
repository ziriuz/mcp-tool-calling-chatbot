import random
import sqlite3
import pandas as pd


HR_DB_SCHEMA = """
table `departments` contains information about company departments:
fields (
    `department_id` int primary key,
    `department_name` varchar,
);
table `employee` contains information about employees:
fields (
    `emp_id` int primary key,
    `first_name` varchar,
    `last_name` varchar,
    `salary` int,
    `department_id` int foreign key references departments.department_id
);
"""


class SqlLiteDatasource:
    def __init__(self, db_url: str):
        self.__db_url = db_url
        self.connection = sqlite3.connect(db_url)
        self.cursor = self.connection.cursor()
        self.__schema = """
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY,
            department_name VARCHAR
        );

        CREATE TABLE IF NOT EXISTS employee (
            emp_id INTEGER PRIMARY KEY,
            first_name VARCHAR,
            last_name VARCHAR,
            salary INTEGER,
            department_id INTEGER,
            FOREIGN KEY(department_id) REFERENCES departments(department_id)
        );
        """

    def get_schema(self):
        return self.__schema

    def execute(self, statement):
        self.cursor.execute(statement)
        return self.cursor.fetchall()

    def retrieve_as_dataframe(self, statement):
        with sqlite3.connect(self.__db_url) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(statement)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            except Exception as e:
                return pd.DataFrame([[str(e)]], columns=["error"])
            finally:
                if cursor:
                    cursor.close()
        return pd.DataFrame(rows, columns=columns)

    def create_schema(self):
        self.cursor.executescript(self.__schema)
        self.connection.commit()

    def generate_hr_data(self):
        # Insert 5 departments
        departments = [
            (1, 'Sales'),
            (2, 'Engineering'),
            (3, 'HR'),
            (4, 'Marketing'),
            (5, 'Finance')
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO departments (department_id, department_name) VALUES (?, ?)",
            departments
        )

        # Create and insert 100 employees
        employees = []
        first_names = ["John", "Jane", "Alice", "Bob", "Carol"]
        last_names = ["Smith", "Doe", "Brown", "Johnson", "Davis"]

        for emp_id in range(1, 101):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            salary = random.randint(1000, 10000)
            dept_id = random.randint(1, 5)
            employees.append((emp_id, fname, lname, salary, dept_id))

        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO employee (emp_id, first_name, last_name, salary, department_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            employees
        )
        self.connection.commit()

    def update_hr_data(self):
        # Extended list of names and surnames for more unique combinations
        first_names = ["John", "Jane", "Alice", "Bob", "Carol", "David", "Emma", "Frank", 
                      "Grace", "Henry", "Ivy", "Jack", "Kelly", "Leo", "Mary", "Noah", 
                      "Olivia", "Peter", "Quinn", "Rachel"]
        last_names = ["Smith", "Doe", "Brown", "Johnson", "Davis", "Wilson", "Moore", 
                     "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", 
                     "Martin", "Thompson", "Young", "Clark", "Walker", "Hall", "Allen"]

        # Get current employees
        employees = self.retrieve_as_dataframe("SELECT emp_id FROM employee ORDER BY emp_id")
        emp_ids = employees['emp_id'].tolist()

        # Generate unique name combinations
        used_combinations = set()
        updated_employees = []

        for emp_id in emp_ids:
            while True:
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                if (fname, lname) not in used_combinations:
                    used_combinations.add((fname, lname))
                    updated_employees.append((fname, lname, emp_id))
                    break

        # Update the database with new unique combinations
        self.cursor.executemany(
            """
            UPDATE employee 
            SET first_name = ?, last_name = ?
            WHERE emp_id = ?
            """,
            updated_employees
        )
        self.connection.commit()

    def update_department_distribution(self):
        # Department distribution mapping
        dept_distribution = {
            1: 25,  # Sales
            2: 40,  # Engineering
            3: 8,   # HR
            4: 15,  # Marketing
            5: 12   # Finance
        }

        # Get all employees
        employees = self.retrieve_as_dataframe("SELECT emp_id FROM employee ORDER BY RANDOM()")
        emp_ids = employees['emp_id'].tolist()

        # Create list for updates based on distribution
        updates = []
        current_position = 0

        for dept_id, count in dept_distribution.items():
            # Get employee IDs for this department
            department_emp_ids = emp_ids[current_position:current_position + count]
            # Create update tuples
            updates.extend([(dept_id, emp_id) for emp_id in department_emp_ids])
            current_position += count

        # Update employee departments
        self.cursor.executemany(
            """
            UPDATE employee 
            SET department_id = ?
            WHERE emp_id = ?
            """,
            updates
        )
        self.connection.commit()


if __name__ == '__main__':
    db = SqlLiteDatasource("data/test-hr.db")
    db.update_department_distribution()
    
    # Verify the distribution
    verification = db.retrieve_as_dataframe("""
        SELECT d.department_name, COUNT(*) as count
        FROM employee e
        JOIN departments d ON e.department_id = d.department_id
        GROUP BY d.department_name
        ORDER BY d.department_id
    """)
    print(verification)    
    # db.create_schema()
    # db.generate_data()
    #db.update_hr_data()  # Uncomment to update names
    #emps = db.retrieve_as_dataframe("SELECT * FROM employee")
    #print(emps.head(10))

