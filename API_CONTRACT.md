| Operation       | Method | Purpose                         |
| --------------- | ------ | ------------------------------- |
| Create Home     | `POST` | Bootstrap the first Home        |
| Add Resident    | `POST` | Add someone to an existing Home |
| Save Preference | `POST` | Configure a resident            |
| Create Poll     | `POST` | Create/open tomorrow's poll     |
| Vote            | `POST` | Record a resident's vote        |
| Close Poll      | `POST` | End voting                      |
| Get Summary     | `GET`  | Retrieve final decision         |
| Get Meal Plan   | `GET`  | Retrieve what should be cooked  |



                 EXTERNAL API
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      D1 API       D2 API       D3 API
        │            │            │
        ▼            ▼            ▼
       D1           D2           D3
        │            │            │
        └────────────┼────────────┘
                     ▼
                 PostgreSQL




                                     n8n
                     │
             "What time is it?"
                     │
                     ▼
              CREATE POLL API
                     │
                     ▼
                 MealBot C
                     │
                     ▼
              [3 candidates]
                     │
                     ▼
                Telegram T
                     │
                  VOTING
                     │
                     ▼
                VOTE API
                     │
                     ▼
                MealBot C
                     │
                 2 hours
                     │
                     ▼
                CLOSE API
                     │
                     ▼
              MealSummary
                     │
              ┌──────┴──────┐
              ▼             ▼
           Residents       Cook