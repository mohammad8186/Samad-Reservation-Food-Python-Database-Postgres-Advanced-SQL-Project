# Database Management Project

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-v13+-blue) ![Python](https://img.shields.io/badge/Python-v3.12+-brightgreen) ![Status](https://img.shields.io/badge/Status-Complete-green)

## 📖 Project Overview
This project involves designing and managing a **university food reservation system** using PostgreSQL as the database management system and Python for interaction with the database. The system features procedures, triggers, and views to support key functionalities such as tracking reservations, calculating revenue, and maintaining database integrity.

### ✨ Key Features:
- **Procedures** for handling business logic (e.g., daily revenue calculation, recent transactions).
- **Triggers** for maintaining data integrity (e.g., avoiding duplicate entries, ensuring minimum inventory).
- **Views** for simplified data querying and presentation.
- Optimized queries using **indices** to enhance performance.
- Error handling and user-friendly messages.

---

## 🗂️ Database Structure
The system consists of the following tables:

1. **Foods**: Tracks food items and their availability.
2. **Students**: Stores student information.
3. **Reservations**: Links students to their food reservations.
4. **Transactions**: Logs reservation changes between students.

### Relationships:
- `Foods` and `Reservations` are linked via `foodid`.
- `Students` and `Reservations` are linked via `studentid`.
- `Transactions` involve two reservations (`srcreservationid` and `dstreservationid`).

---

## 🛠️ Setup Instructions

### Prerequisites:
- PostgreSQL v13 or higher
- Python 3.12+
- Required Python packages: `psycopg2`

### Installation:
1. Clone this repository:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Install dependencies:
   ```bash
   pip install psycopg2
   ```

3. Set up the database:
   - Create the database in PostgreSQL:
     ```sql
     CREATE DATABASE university_food_system;
     ```
   - Update the database credentials in the `Python` script:
     ```python
     DB_NAME = "university_food_system"
     USER = "<your_username>"
     PASSWORD = "<your_password>"
     HOST = "localhost"
     PORT = "5432"
     ```

4. Run the main script to execute the operations:
   ```bash
   python main.py
   ```

---

## 🚀 Features

### 1️⃣ Procedures
| Name                                  | Description                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| `get_food_reservation_counts_today`   | Displays the count of food reservations for the current day.               |
| `get_students_with_reservation_today` | Lists students with reservations for the current day.                      |
| `get_recent_transactions`             | Shows the last 10 reservation transactions.                                |
| `get_daily_revenue`                   | Calculates the daily revenue based on food prices.                         |
| `calculate_remaining_inventory`       | Shows remaining inventory after deducting today’s reservations.            |

### 2️⃣ Views
| Name                 | Description                                                        |
|----------------------|--------------------------------------------------------------------|
| `food_student`       | Displays students and the food they reserved.                     |
| `transaction_student`| Displays transactions, including original and new reserved food.  |

### 3️⃣ Triggers
| Name                                  | Description                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| `trg_prevent_duplicate_studentid`     | Ensures no duplicate student IDs are added.                                |
| `trg_check_initial_inventory`         | Verifies that new foods have at least 500 in inventory.                    |
| `trg_check_multiple_students_order`   | Prevents students from reserving more than one food item at the same time. |
| `trg_check_multiple_foods_same_date`  | Prevents assigning more than two foods with the same date.                 |
| `trg_check_multiple_food_orders_per_day` | Prevents students from ordering multiple foods in one day.                |

---

## 📊 Performance Optimization

### Query Optimization:
- Added an index on the `studentid` column in the `students` table to improve query performance.
- Measured query execution time before and after indexing:
  - **Before Indexing**: X.XXXX seconds
  - **After Indexing**: Y.YYYY seconds

### Constraint:
Added a unique constraint to the `transactions` table:
```sql
ALTER TABLE public.transactions
ADD CONSTRAINT unique_transaction_ids UNIQUE (srcreservationid, dstreservationid);
```

---

## ⚠️ Error Handling
- Procedures and triggers handle exceptions to prevent data inconsistencies.
- User-friendly error messages are displayed for issues like duplicate entries or insufficient inventory.

---

## 📸 Screenshots

### Example Procedure Execution
```bash
Choose a procedure to run:
1. CALL get_food_reservation_counts_today('result_set');
...
Output:
food_name   | reservation_count
------------|-------------------
Pizza       | 15
Burger      | 10
```

### Example Trigger
When attempting to insert a student with an existing `studentid`:
```bash
ERROR: student with id 123 already exists
```

---

## 💡 Future Enhancements
- **Caching**: Use Redis for storing frequently accessed data like inventory counts.
- **Enhanced UI**: Develop a web-based interface for managing the reservation system.


