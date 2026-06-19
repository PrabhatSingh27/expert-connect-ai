# Database Design

## users

id
name
email
phone
password_hash
role
created_at

Roles:

- admin
- operator
- customer
- expert

---

## expert_profiles

id
user_id
category
experience_years
rating
verified

---

## issues

id
customer_id
description
problem_type
category
urgency
preferred_date
preferred_time
status
created_at

---

## issue_media

id
issue_id
file_url
file_type

Types:

- image
- audio
- video

---

## expert_availability

id
expert_id
available_date
start_time
end_time

---

## assignments

id
issue_id
expert_id
assigned_at
status

---

## messages

id
assignment_id
sender_id
message
created_at

---

## feedback

id
assignment_id
rating
review
created_at