# AI Pipeline

## Example Input

"My AC is leaking water and guests are arriving tonight."

---

## Step 1: Problem Detection

Output:

{
    "problem_type": "AC"
}

---

## Step 2: Category Mapping

Mapping:

AC -> Electrical

Output:

{
    "problem_type": "AC",
    "category": "Electrical"
}

---

## Step 3: Urgency Detection

Output:

{
    "urgency": "High"
}

---

## Step 4: Assignment Engine

Input:

{
    "problem_type": "AC",
    "category": "Electrical",
    "urgency": "High"
}

Assignment Factors:

- Category Match
- Expert Availability
- Expert Load
- Round Robin Position
- Urgency