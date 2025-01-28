import psycopg2
import time

DB_NAME = "postgres"
USER = "postgres"
PASSWORD = "09902048023M.sh"
HOST = "localhost"
PORT = "5432"

procedures = {
    "1": {
        "name": "Create get_food_reservation_counts_today",
        "sql": """
        CREATE OR REPLACE PROCEDURE get_food_reservation_counts_today(
            INOUT result_set refcursor
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            OPEN result_set FOR
            SELECT 
                f.name AS food_name, 
                COUNT(r.id) AS reservation_count
            FROM 
                public.foods f
            JOIN 
                public.reservations r ON f.id = r.foodid
            WHERE 
                f.date::date = CURRENT_DATE
            GROUP BY 
                f.name;
        END;
        $$;
        """
    },
    "2": {
        "name": "Create get_students_with_reservation_today",
        "sql": """
        CREATE OR REPLACE PROCEDURE get_students_with_reservation_today(
            INOUT result_set refcursor
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            OPEN result_set FOR
            SELECT 
                *
            FROM 
                public.students s
            JOIN 
                public.reservations r ON s.studentid = r.studentid
            JOIN 
                public.foods f ON r.foodid = f.id
            WHERE 
                f.date::date = CURRENT_DATE;
        END;
        $$;
        """
    },
    "3": {
        "name": "Create get_recent_transactions",
        "sql": """
        CREATE OR REPLACE PROCEDURE get_recent_transactions(
            INOUT result_set refcursor
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            OPEN result_set FOR
            SELECT 
                srcreservationid,
                dstreservationid,
                date
            FROM 
                public.transactions
            ORDER BY 
                date DESC
            LIMIT 10;
        END;
        $$;
        """
    },
    "4": {
        "name": "Create get_daily_revenue",
        "sql": """
                   CREATE OR REPLACE FUNCTION get_daily_revenue()
        RETURNS DECIMAL AS $$
        DECLARE
            daily_revenue DECIMAL;
        BEGIN
            SELECT SUM(f.price)
            INTO daily_revenue
            FROM public.reservations r
            JOIN public.foods f ON r.foodid = f.id
            WHERE f.date::date = CURRENT_DATE;
        
            RETURN daily_revenue;
        END;
        $$ LANGUAGE plpgsql;"""
    },
    "5": {
        "name": "Create calculate_remaining_inventory",
        "sql": """
        CREATE OR REPLACE PROCEDURE calculate_remaining_inventory(
            INOUT result_set refcursor
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            OPEN result_set FOR
            SELECT 
                f.name AS food_name, 
                (f.inventory - COALESCE(s.reservation_count, 0)) AS remaining_count
            FROM 
                public.foods f
            LEFT JOIN (
                SELECT 
                    r.foodid,
                    COUNT(r.id) AS reservation_count
                FROM 
                    public.reservations r 
                GROUP BY 
                    r.foodid
            ) s ON f.id = s.foodid;
        END;
        $$;
        """
    }
}
views = {
    "1": {
        "name": "Create view food_student",
        "sql": """
        CREATE VIEW food_student AS
        SELECT s.first_name || ' ' || s.last_name AS student_name,
               f.name AS food_name
        FROM public.students s   
        JOIN public.reservations r ON s.studentid = r.studentid
        JOIN public.foods f ON r.foodid = f.id;
        """
    },
    "2": {
        "name": "Create view transaction_student",
        "sql": """
        CREATE VIEW transaction_student AS
        SELECT 
            s.studentid,
            s.first_name || ' ' || s.last_name AS student_name,
            f1.name AS original_food,
            f2.name AS new_food
        FROM 
            public.transactions t
        JOIN 
            public.reservations r1 ON t.srcreservationid = r1.id
        JOIN 
            public.reservations r2 ON t.dstreservationid = r2.id
        JOIN 
            public.foods f1 ON r1.foodid = f1.id
        JOIN 
            public.foods f2 ON r2.foodid = f2.id
        JOIN 
            public.students s ON r1.studentid = s.studentid;
        """
    }
}

triggers = {
    "1": {
        "name": "Create trigger trg_prevent_duplicate_studentid",
        "sql": """
        CREATE OR REPLACE FUNCTION prevent_duplicate_studentid()
        RETURNS TRIGGER AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM public.students WHERE studentid = NEW.studentid) THEN
                RAISE EXCEPTION 'student with id % already exists', NEW.studentid;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_prevent_duplicate_studentid
        BEFORE INSERT ON public.students
        FOR EACH ROW
        EXECUTE FUNCTION prevent_duplicate_studentid();
        """
    },
    "2": {
        "name": "Create trigger trg_check_initial_inventory",
        "sql": """
        CREATE OR REPLACE FUNCTION check_initial_inventory()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.inventory < 500 THEN
                RAISE EXCEPTION 'initial inventory for food % must be at least 500', NEW.name;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_check_initial_inventory
        BEFORE INSERT ON public.foods
        FOR EACH ROW
        EXECUTE FUNCTION check_initial_inventory();
        """
    },
    "3": {
        "name": "Create trigger trg_check_multiple_students_order",
        "sql": """
        CREATE OR REPLACE FUNCTION check_multiple_students_order()
        RETURNS TRIGGER AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM public.reservations
                WHERE studentid = NEW.studentid
                GROUP BY studentid
                HAVING COUNT(*) >= 2
            ) THEN
                RAISE EXCEPTION 'Student % cannot order more than one food item simultaneously.', NEW.studentid;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_check_multiple_students_order
        BEFORE INSERT ON public.reservations
        FOR EACH ROW
        EXECUTE FUNCTION check_multiple_students_order();
        """
    },
    "4": {
        "name": "Create trigger trg_check_multiple_foods_same_date",
        "sql": """
      CREATE OR REPLACE FUNCTION check_multiple_foods_same_date()
      RETURNS TRIGGER AS $$
      BEGIN
          IF (SELECT COUNT(*) FROM public.foods WHERE  date =  NEW.date) >= 2 THEN
              RAISE EXCEPTION 'More than two foods cannot have the same date';
          END IF;

          RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;

      CREATE TRIGGER trg_check_multiple_foods_same_date
      BEFORE INSERT ON public.foods
      FOR EACH ROW
      EXECUTE FUNCTION check_multiple_foods_same_date();
      """
    },

    "5": {
        "name": "Create trigger trg_check_multiple_food_orders_per_day",
        "sql": """
        CREATE OR REPLACE FUNCTION check_multiple_food_orders_per_day()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (SELECT COUNT(*) FROM public.reservations WHERE studentid = NEW.studentid AND date = NEW.date) >= 2 THEN
                RAISE EXCEPTION 'Student % cannot order more than one food item in a same day', NEW.studentid;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_check_multiple_food_orders_per_day
        BEFORE INSERT ON public.reservations
        FOR EACH ROW
        EXECUTE FUNCTION check_multiple_food_orders_per_day();
        """
    }
}

def connect():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT
        )
        return conn
    except Exception as e:
        print(f"error connecting to database: {e}")
        return None

def execute_query(conn, query):
    try:
        cur = conn.cursor()
        cur.execute(query)
        if query.strip().upper().startswith("SELECT"):
            results = cur.fetchall()
            for row in results:
                print(row)
        else:
            conn.commit()
            print("query executed successfully.")
        cur.close()
    except Exception as e:
        print(f"error executing query: {e}")

def time_query_execution(conn, query):
    try:
        cur = conn.cursor()
        start_time = time.time()
        cur.execute(query)
        end_time = time.time()
        execution_time = end_time - start_time
        cur.close()
        return execution_time
    except Exception as e:
        print(f"error executing query: {e}")
        return None

def create_procedure(conn):
    for key, value in procedures.items():
        print(f"{key}. {value['name']}")
    choice = input("choose a procedure to create: ")
    if choice in procedures:
        execute_query(conn, procedures[choice]["sql"])
    else:
        print("invalid choice")

def create_view(conn):
    for key, value in views.items():
        print(f"{key}. {value['name']}")
    choice = input("choose a view to create: ")
    if choice in views:
        execute_query(conn, views[choice]["sql"])
    else:
        print("invalid choice")

def create_trigger(conn):
    for key, value in triggers.items():
        print(f"{key}. {value['name']}")
    choice = input("Choose a trigger to create: ")
    if choice in triggers:
        execute_query(conn, triggers[choice]["sql"])
    else:
        print("invalid choice")

def get_daily_revenue(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT get_daily_revenue();")
        daily_revenue = cur.fetchone()[0]
        cur.close()
        return daily_revenue
    except Exception as e:
        print(f"Error getting daily revenue: {e}")
        return None

def call_procedure(conn):
    options = {
        "1": "CALL get_food_reservation_counts_today('result_set');",
        "2": "CALL get_students_with_reservation_today('result_set');",
        "3": "CALL get_recent_transactions('result_set');",
        "4": "CALL get_daily_revenue();",  # No 'result_set' for get_daily_revenue
        "5": "CALL calculate_remaining_inventory('result_set');"
    }
    for key, value in options.items():
        print(f"{key}. {value}")
    choice = input("Choose a procedure to run: ")
    if choice in options:
        try:
            cur = conn.cursor()
            if choice == "4":
                # Special handling for get_daily_revenue
                cur.execute("""
                           DO $$ 
                           DECLARE
                               daily_revenue DECIMAL;
                           BEGIN
                               CALL get_daily_revenue(daily_revenue);
                               RAISE NOTICE 'Daily revenue: %', daily_revenue;
                           END $$;
                           """)

                result = cur.fetchall()
                for row in result:
                    print(row)
                conn.commit()
            else:
                cur.execute(f"BEGIN; {options[choice]} FETCH ALL IN result_set;")
                results = cur.fetchall()
                for row in results:
                    print(row)
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"error executing procedure: {e}")
    else:
        print("Invalid choice")

def create_index_and_compare(conn):
    initial_query = "SELECT * FROM public.students WHERE studentid = 1001;"
    index_query = "CREATE INDEX idx_studentid ON public.students (studentid);"

    initial_time = time_query_execution(conn, initial_query)
    print(f"Initial execution time: {initial_time:.6f} seconds")

    execute_query(conn, index_query)

    final_time = time_query_execution(conn, initial_query)
    print(f"Execution time after indexing: {final_time:.6f} seconds")

    time_difference = initial_time - final_time
    print(f"Difference in execution time: {time_difference:.6f} seconds")

def add_constraint(conn):
    constraint_query = """
    ALTER TABLE public.transactions
    ADD CONSTRAINT unique_transaction_ids UNIQUE (srcreservationid,dstreservationid);
    """
    execute_query(conn, constraint_query)

def menu():
    conn = connect()
    if not conn:
        return

    while True:
        print("\nMenu:")
        print("1. Create procedure")
        print("2. Create view")
        print("3. Create trigger")
        print("4. Run procedure")
        print("5. Index on student and compare")
        print("6. Add constraint on transactions table")
        print("7. Get Daily Revenue")
        print("0. Exit")

        choice = int(input("Choose an option: "))

        if choice == 0:
            break
        elif choice == 1:
            create_procedure(conn)
        elif choice == 2:
            create_view(conn)
        elif choice == 3:
            create_trigger(conn)
        elif choice == 4:
            call_procedure(conn)
        elif choice == 5:
            create_index_and_compare(conn)
        elif choice == 6:
            add_constraint(conn)
        elif choice == 7:
            daily_revenue = get_daily_revenue(conn)
            if daily_revenue is not None:
                print(f"Daily Revenue: {daily_revenue}")
        else:
            print(" please choose again.")

    conn.close()

if __name__ == "__main__":
    menu()