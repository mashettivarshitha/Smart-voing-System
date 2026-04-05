import streamlit as st
import sqlite3
import random

# ---------------- DATABASE ----------------
def get_connection():
    return sqlite3.connect("voting.db", timeout=10, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        age INTEGER,
        aadhaar TEXT,
        voter_id TEXT,
        has_voted INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        candidate TEXT PRIMARY KEY,
        count INTEGER
    )
    """)

    candidates = ["Candidate A", "Candidate B", "Candidate C"]
    for candidate in candidates:
        c.execute(
            "INSERT OR IGNORE INTO votes(candidate, count) VALUES (?, ?)",
            (candidate, 0)
        )

    conn.commit()
    conn.close()

init_db()

# ---------------- FUNCTIONS ----------------
def register(username, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users(username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return "exists"
    finally:
        conn.close()

def login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def update_details(username, age, aadhaar, voter_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE users SET age=?, aadhaar=?, voter_id=? WHERE username=?
    """, (age, aadhaar, voter_id, username))
    conn.commit()
    conn.close()

def has_voted(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT has_voted FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def vote(username, candidate):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT has_voted FROM users WHERE username=?", (username,))
    if c.fetchone()[0]:
        conn.close()
        return False

    c.execute("UPDATE votes SET count = count + 1 WHERE candidate=?", (candidate,))
    c.execute("UPDATE users SET has_voted=1 WHERE username=?", (username,))

    conn.commit()
    conn.close()
    return True

def get_results():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM votes")
    data = c.fetchall()
    conn.close()
    return data

# ---------------- UI ----------------
st.title("🗳️ Smart Voting System")

menu = ["Register", "Login", "Results"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- REGISTER ----------------
if choice == "Register":
    st.subheader("Register Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        result = register(username, password)

        if result == True:
            st.success("Registered Successfully ✅")
        elif result == "exists":
            suggestion = username + str(random.randint(100,999))
            st.warning(f"⚠️ Username exists! Try: {suggestion}")

# ---------------- LOGIN ----------------
elif choice == "Login":
    st.subheader("Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # SESSION INIT
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "step" not in st.session_state:
        st.session_state.step = 1

    # LOGIN BUTTON
    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.step = 1
        else:
            st.error("Invalid login ❌")

    # AFTER LOGIN
    if st.session_state.logged_in:

        st.success(f"Welcome {st.session_state.username} 🎉")

        if has_voted(st.session_state.username):
            st.warning("⚠️ You already voted!")
        else:

            # STEP 1
            if st.session_state.step == 1:
                st.subheader("Step 1: Eligibility Check")

                age = st.number_input("Enter Age", 0, 120, key="age_input")
                aadhaar = st.file_uploader("Upload Aadhaar", type=["jpg", "png", "pdf"])

                if st.button("Verify Eligibility"):
                    if age >= 18 and aadhaar is not None:
                        st.session_state.age = age
                        st.session_state.step = 2
                        st.success("✅ Eligible")
                        st.rerun()
                    else:
                        st.error("❌ Not eligible")

            # STEP 2
            elif st.session_state.step == 2:
                st.subheader("Step 2: Enter Voter ID")

                voter_id = st.text_input("Enter Voter ID")

                if st.button("Continue"):
                    if voter_id:
                        update_details(st.session_state.username, st.session_state.age, "uploaded", voter_id)
                        st.session_state.step = 3
                        st.rerun()
                    else:
                        st.error("Enter Voter ID")

            # STEP 3
            elif st.session_state.step == 3:
                st.subheader("Step 3: Vote")

                candidate = st.radio(
                    "Choose Candidate",
                    ["Candidate A", "Candidate B", "Candidate C"]
                )

                if st.button("Submit Vote"):
                    success = vote(st.session_state.username, candidate)

                    if success:
                        st.session_state.step = 4
                        st.success("🎉 Voted Successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Already voted")

            # STEP 4
            elif st.session_state.step == 4:
                st.success("✅ Your vote has been recorded")

# ---------------- RESULTS ----------------
elif choice == "Results":
    st.subheader("Voting Results 📊")

    results = get_results()

    for candidate, count in results:
        st.metric(candidate, count)